"""Dues, penalties and payment recording (ledger entry + score + group SMS + fraud checks)."""
from datetime import date

from . import fraud, scoring
from .extensions import db
from .ledger import append_entry, pool_balance
from .models import LedgerEntry, Loan
from .services.sms import notify_all
from .timeutil import kes, local_date, now_utc, today_nairobi

METHODS = ("mpesa", "card", "cash")
MAX_FLEXIBLE = 500_000
LABELS = {"contribution": "Monthly contribution", "penalty": "Late penalty",
          "loan_installment": "Loan installment", "savings": "Extra savings", "welfare": "Welfare fund", "rotation": "Merry-go-round pot"}


class PaymentError(ValueError):
    """Raised for invalid payments (message is safe to show the user)."""


def period_of(d: date) -> str:
    return f"{d.year}-{d.month:02d}"


def due_date_for(chama, d: date) -> date:
    return date(d.year, d.month, chama.due_day)


def _originals(member_id, period, type):
    return LedgerEntry.query.filter_by(member_id=member_id, period=period, type=type).order_by(LedgerEntry.id).all()


def net_paid(member_id, period, type) -> int:
    """Total for this item in the period, including any corrections made to it."""
    rows = _originals(member_id, period, type)
    total = sum(r.amount for r in rows)
    if rows:
        ids = [r.id for r in rows]
        total += sum(c.amount for c in LedgerEntry.query.filter(LedgerEntry.corrects_id.in_(ids)))
    return total


def penalty_info(member, today: date) -> dict:
    chama, period = member.chama, period_of(today)
    due = due_date_for(chama, today)
    paid = net_paid(member.id, period, "contribution") >= chama.monthly_amount
    rows = _originals(member.id, period, "contribution")
    end = local_date(rows[0].created_at) if paid and rows else today
    days = max(0, (end - due).days)
    accrued = days * chama.penalty_per_day
    return {"days": days, "accrued": accrued, "owed": max(0, accrued - net_paid(member.id, period, "penalty"))}


def member_status(member, today: date) -> dict:
    chama = member.chama
    paid = net_paid(member.id, period_of(today), "contribution") >= chama.monthly_amount
    if paid:
        return {"status": "paid", "days": 0, "owed": 0, "penalty_per_day": chama.penalty_per_day}
    days = max(0, (today - due_date_for(chama, today)).days)
    info = penalty_info(member, today)
    return {"status": "overdue" if days else "pending", "days": days, "owed": info["owed"],
            "penalty_per_day": chama.penalty_per_day}


def active_loan(member):
    return Loan.query.filter_by(member_id=member.id, status="active").first()


def available_items(member, today: date) -> list:
    """Only the things this member can actually pay right now."""
    chama, items = member.chama, []
    if member_status(member, today)["status"] != "paid":
        items.append({"key": "contribution", "amount": chama.monthly_amount, "editable": False})
    owed = penalty_info(member, today)["owed"]
    if owed > 0:
        items.append({"key": "penalty", "amount": owed, "editable": True, "max": owed})
    loan = active_loan(member)
    if loan:
        items.append({"key": "loan_installment", "editable": False,
                      "amount": min(loan.installment_amount, loan.total_due - loan.repaid)})
    if chama.rotation_amount and net_paid(member.id, period_of(today), "rotation") < chama.rotation_amount:
        items.append({"key": "rotation", "amount": chama.rotation_amount, "editable": False})
    items.append({"key": "savings", "amount": 500, "editable": True, "max": MAX_FLEXIBLE})
    items.append({"key": "welfare", "amount": 200, "editable": True, "max": MAX_FLEXIBLE})
    for i in items:
        i["label"] = LABELS[i["key"]]
    return items


def group_sms_text(member, amount, balance, goal) -> str:
    return f"{member.first_name} paid {kes(amount)}. Group total: {kes(balance)} / goal {kes(goal)}."


def record_payment(member, key, amount, method, recorded_by, ref=None):
    """Validate and record one payment, then update score, SMS everyone, run fraud rules."""
    if method not in METHODS:
        raise PaymentError("Choose a valid payment method.")
    today = today_nairobi()
    item = next((i for i in available_items(member, today) if i["key"] == key), None)
    if item is None:
        raise PaymentError("That item cannot be paid right now.")
    if not isinstance(amount, int) or amount <= 0:
        raise PaymentError("Enter a whole-number amount above zero.")
    if not item["editable"] and amount != item["amount"]:
        raise PaymentError(f"{item['label']} is fixed at {kes(item['amount'])}.")
    if item["editable"] and amount > item["max"]:
        raise PaymentError(f"The most you can pay for {item['label'].lower()} is {kes(item['max'])}.")

    chama, now = member.chama, now_utc()
    entry = append_entry(chama.id, member.id, amount, key, method, recorded_by.id,
                         period=period_of(today), ref=ref, created_at=now)
    if key == "contribution":
        scoring.on_contribution(member, (due_date_for(chama, today) - today).days)
    elif key == "loan_installment":
        from .loans import apply_installment
        apply_installment(active_loan(member), amount, today, member)
    notify_all(chama, group_sms_text(member, amount, entry.running_balance, chama.goal_amount), "payment")
    fraud.check_cash_for_self(entry)
    db.session.commit()
    return entry

