"""Demo seed: 'Umoja Sisters' with 6 members, ~4 months of history, one overdue member and one active loan.

Run: python seed.py   (wipes and recreates the database; every demo member's PIN is 1234)
"""
from datetime import date, datetime, time, timedelta

from werkzeug.security import generate_password_hash

from app import create_app
from app import scoring
from app.extensions import db
from app.ledger import append_entry
from app.models import Account, Chama, Loan, LoanVote, Member, PersonalGoal, RotationSlot
from app.payments import group_sms_text, period_of
from app.services.sms import notify_all
from app.timeutil import nairobi_to_utc, today_nairobi

DEMO_PIN = "1234"
DEMO_PASSWORD = "Demo1234"
MONTHLY, GOAL, PENALTY, ROTATION = 1500, 50_000, 50, 500

# name, phone, role, days relative to the due date for months -4..0 (negative = early, None = unpaid)
MEMBERS = [
    ("Wanjiku Kamau", "254712000001", "member", [-2, -1, -3, -2, -1]),
    ("Mary Njeri", "254712000002", "treasurer", [-3, -2, -2, -4, -2]),
    ("Fatuma Hassan", "254712000003", "signatory", [0, -1, 0, -1, 0]),
    ("Grace Wambui", "254712000004", "signatory", [0, 2, 0, -1, -1]),
    ("Akinyi Odhiambo", "254712000005", "member", [-1, 0, -2, -1, -1]),
    ("Achieng Otieno", "254712000006", "member", [1, 3, 2, 4, None]),   # overdue this month
]


def add_months(d: date, n: int) -> date:
    total = d.year * 12 + (d.month - 1) + n
    return date(total // 12, total % 12 + 1, 1)


def at_ten(day: date, minutes=0) -> datetime:
    return nairobi_to_utc(datetime.combine(day, time(10, minutes)))


def seed_demo(today: date | None = None):
    today = today or today_nairobi()
    db.drop_all()
    db.create_all()
    # Due day sits 3 days before "today" so one member is visibly overdue whenever the demo is seeded.
    due_day = min(max(1, today.day - 3), 25)
    chama = Chama(name="Umoja Sisters", monthly_amount=MONTHLY, goal_amount=GOAL, due_day=due_day,
                  penalty_per_day=PENALTY, loan_approval_pct=60, loan_interest_pct=10, loan_interest_type="flat",
                  loan_approval_mode="vote", require_guarantor=False, rotation_amount=ROTATION,
                  rotation_start=period_of(today))
    db.session.add(chama)
    db.session.flush()
    pin_hash = generate_password_hash(DEMO_PIN)
    members = {}
    for name, phone, role, _ in MEMBERS:
        members[name] = Member(chama_id=chama.id, name=name, phone=phone, role=role, pin_hash=pin_hash)
    db.session.add_all(members.values())
    db.session.flush()
    for member in members.values():
        email = f"demo+{member.phone[-4:]}@chamavault.local"
        member.email = email
        db.session.add(Account(email=email, password_hash=generate_password_hash(DEMO_PASSWORD), member_id=member.id))
    for pos, (name, *_rest) in enumerate(MEMBERS):
        db.session.add(RotationSlot(chama_id=chama.id, member_id=members[name].id, position=pos))
    treasurer = members["Mary Njeri"]
    borrower = members["Akinyi Odhiambo"]

    events = []   # (when, member, amount, type, method, recorded_by, period, offset)
    for idx, (name, _, _, offsets) in enumerate(MEMBERS):
        m = members[name]
        for k, offset in enumerate(offsets):
            if offset is None:
                continue
            month = add_months(today, k - 4)
            due = date(month.year, month.month, due_day)
            paid_on = due + timedelta(days=offset)
            method = ("mpesa", "mpesa", "cash", "mpesa", "card")[(idx + k) % 5]
            if m.role == "treasurer" and method == "cash":
                method = "mpesa"          # the treasurer never records cash for herself
            by = treasurer if method == "cash" else m
            events.append((at_ten(paid_on), m, MONTHLY, "contribution", method, by, period_of(due), offset))
            if offset > 0:
                events.append((at_ten(paid_on, 1), m, offset * PENALTY, "penalty", method, by, period_of(due), None))

    for name in ("Wanjiku Kamau", "Mary Njeri", "Fatuma Hassan"):   # three already paid into this month's pot
        m = members[name]
        events.append((at_ten(today - timedelta(days=1)), m, ROTATION, "rotation", "mpesa", m, period_of(today), None))

    payout_day = date(*add_months(today, -2).timetuple()[:2], due_day) + timedelta(days=10)
    events.append((at_ten(payout_day), borrower, -10_000, "loan_payout", "mpesa", treasurer, period_of(payout_day), None))
    installment_day = payout_day + timedelta(days=25)
    events.append((at_ten(installment_day), borrower, 2750, "loan_installment", "mpesa", borrower,
                   period_of(installment_day), "installment"))

    for when, m, amount, type_, method, by, period, extra in sorted(events, key=lambda e: e[0]):
        entry = append_entry(chama.id, m.id, amount, type_, method, by.id, period=period, created_at=when,
                             ref=None if method == "cash" else f"SEED{when:%y%m%d%H%M}{m.id}{type_[:2].upper()}")
        if type_ == "contribution":
            scoring.on_contribution(m, -extra, created_at=when)
        elif type_ == "loan_installment":
            scoring.on_installment(m, True, created_at=when)
        if period == period_of(today) and type_ in ("contribution", "penalty", "rotation"):
            notify_all(chama, group_sms_text(m, amount, entry.running_balance, GOAL), "payment", created_at=when)

    loan = Loan(chama_id=chama.id, member_id=borrower.id, principal=10_000, total_due=11_000, installments=4,
                installment_amount=2750, installments_paid=1, repaid=2750, status="active",
                requested_at=at_ten(payout_day - timedelta(days=5)), paid_out_at=at_ten(payout_day))
    db.session.add(loan)
    db.session.flush()
    for name, approve in (("Wanjiku Kamau", True), ("Mary Njeri", True), ("Fatuma Hassan", True),
                          ("Grace Wambui", True), ("Achieng Otieno", False)):
        db.session.add(LoanVote(loan_id=loan.id, member_id=members[name].id, approve=approve,
                                created_at=at_ten(payout_day - timedelta(days=3))))

    # Demo emails + personal goals for Vaulti / Resend digests
    members["Wanjiku Kamau"].email = "wanjiku@example.com"
    members["Mary Njeri"].email = "mary@example.com"
    db.session.add(PersonalGoal(
        member_id=members["Wanjiku Kamau"].id,
        name="School fees",
        target_kes=30_000,
        saved_kes=6_000,
        monthly_pledge=4_000,
        target_date=add_months(today, 6),
    ))
    db.session.add(PersonalGoal(
        member_id=members["Achieng Otieno"].id,
        name="Emergency fund",
        target_kes=15_000,
        saved_kes=2_000,
        monthly_pledge=1_500,
        target_date=add_months(today, 10),
    ))
    db.session.commit()


if __name__ == "__main__":
    with create_app().app_context():
        seed_demo()
        print(f"Seeded Umoja Sisters. Demo account password: {DEMO_PASSWORD}; transaction PIN: {DEMO_PIN}")
