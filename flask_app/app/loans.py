"""Loans: request, group vote, mock payout, installment tracking and default."""
import math
import secrets
from datetime import timedelta

from . import fraud, scoring
from .extensions import db
from . import rotation
from .ledger import append_entry, pool_balance
from .models import Member
from .models import Loan, LoanVote
from .payments import period_of
from .services.sms import notify_all, notify_members
from .timeutil import kes, local_date, now_utc, today_nairobi

MIN_LOAN, MAX_INSTALLMENTS, DEFAULT_GRACE_DAYS = 500, 6, 30


class LoanError(ValueError):
    """Raised for invalid loan actions (message is safe to show the user)."""


def loan_terms(principal, pct, n, kind):
    """Return (total_due, installment). Flat: pct is the total % added. Reducing: pct is % per month."""
    if kind == "reducing" and pct > 0:
        r = pct / 100
        pay = math.ceil(principal * r / (1 - (1 + r) ** -n))
        return pay * n, pay
    total = round(principal * (100 + pct) / 100)
    return total, math.ceil(total / n)


def available_pool(chama_id):
    return pool_balance(chama_id) - rotation.held(chama_id)


def request_loan(member, amount, installments, guarantor_id=None):
    chama = member.chama
    if Loan.query.filter(Loan.member_id == member.id, Loan.status.in_(("pending", "approved", "active"))).first():
        raise LoanError("You already have an open loan or request.")
    if not isinstance(amount, int) or amount < MIN_LOAN:
        raise LoanError(f"The minimum loan is {kes(MIN_LOAN)}.")
    if amount > available_pool(chama.id):
        raise LoanError("The group pool cannot cover that amount right now.")
    if not isinstance(installments, int) or not 1 <= installments <= MAX_INSTALLMENTS:
        raise LoanError(f"Choose between 1 and {MAX_INSTALLMENTS} monthly installments.")
    guarantor = None
    if chama.require_guarantor:
        guarantor = db.session.get(Member, guarantor_id or 0)
        if guarantor is None or guarantor.chama_id != chama.id or guarantor.id == member.id:
            raise LoanError("Choose another member of the chama as your guarantor.")
    total, per = loan_terms(amount, chama.loan_interest_pct, installments, chama.loan_interest_type)
    loan = Loan(chama_id=chama.id, member_id=member.id, principal=amount, total_due=total, installments=installments,
                installment_amount=per, guarantor_id=guarantor.id if guarantor else None,
                guarantor_ok=guarantor is None)
    db.session.add(loan)
    how = "the treasurer will decide" if chama.loan_approval_mode == "officer" else "please vote in ChamaVault"
    notify_all(chama, f"{member.first_name} requested a loan of {kes(amount)}; {how}.", "loan")
    if guarantor:
        notify_members([guarantor], f"{member.first_name} asked you to guarantee a {kes(amount)} loan. "
                                    "Open ChamaVault > Loans to accept or decline.", "loan")
    db.session.commit()
    return loan


def vote_summary(loan) -> dict:
    chama = loan.member.chama
    eligible = len(chama.members) - 1                      # the borrower cannot vote
    needed = math.ceil(chama.loan_approval_pct * eligible / 100)
    yes = sum(1 for v in loan.votes if v.approve)
    no = len(loan.votes) - yes
    return {"eligible": eligible, "needed": needed, "yes": yes, "no": no}


def cast_vote(loan, voter, approve: bool):
    if loan.status != "pending":
        raise LoanError("Voting on this loan is closed.")
    if loan.member.chama.loan_approval_mode != "vote":
        raise LoanError("This chama approves loans through the treasurer, not a vote.")
    if not loan.guarantor_ok:
        raise LoanError("Voting opens once the guarantor accepts.")
    if voter.id == loan.member_id:
        raise LoanError("You cannot vote on your own loan.")
    if any(v.member_id == voter.id for v in loan.votes):
        raise LoanError("You have already voted.")
    db.session.add(LoanVote(loan_id=loan.id, member_id=voter.id, approve=approve))
    db.session.flush()
    db.session.refresh(loan)
    s = vote_summary(loan)
    chama = loan.member.chama
    if s["yes"] >= s["needed"]:
        loan.status = "approved"
        notify_all(chama, f"{loan.member.first_name}'s loan of {kes(loan.principal)} was approved.", "loan")
    elif s["no"] > s["eligible"] - s["needed"]:
        loan.status = "rejected"
        notify_all(chama, f"{loan.member.first_name}'s loan request was not approved.", "loan")
    db.session.commit()


def answer_guarantee(loan, member, accept: bool):
    if loan.status != "pending" or loan.guarantor_id != member.id or loan.guarantor_ok:
        raise LoanError("There is nothing for you to answer on this loan.")
    if accept:
        loan.guarantor_ok = True
        notify_all(loan.member.chama, f"{member.first_name} agreed to guarantee {loan.member.first_name}'s loan.", "loan")
    else:
        loan.status = "rejected"
        notify_members([loan.member], f"{member.first_name} declined to guarantee your loan request.", "loan")
    db.session.commit()


def officer_decide(loan, treasurer, approve: bool):
    chama = loan.member.chama
    if chama.loan_approval_mode != "officer":
        raise LoanError("This chama approves loans by member vote.")
    if loan.status != "pending" or not loan.guarantor_ok:
        raise LoanError("This loan is not ready for a decision.")
    if loan.member_id == treasurer.id:
        raise LoanError("The treasurer cannot approve their own loan.")
    loan.status = "approved" if approve else "rejected"
    notify_all(chama, f"{loan.member.first_name}'s loan of {kes(loan.principal)} was "
                      f"{'approved' if approve else 'not approved'} by the treasurer.", "loan")
    db.session.commit()


def payout(loan, treasurer):
    """Mock M-Pesa disbursement of an approved loan."""
    if loan.status != "approved":
        raise LoanError("Only approved loans can be paid out.")
    chama = loan.member.chama
    balance = pool_balance(chama.id)
    if loan.principal > available_pool(chama.id):
        raise LoanError("The pool balance is too low for this payout.")
    now = now_utc()
    entry = append_entry(chama.id, loan.member_id, -loan.principal, "loan_payout", "mpesa", treasurer.id,
                         period=period_of(local_date(now)), ref="MP" + secrets.token_hex(4).upper(), created_at=now)
    loan.status, loan.paid_out_at = "active", now
    notify_all(chama, f"{kes(loan.principal)} was paid out to {loan.member.first_name}. "
                      f"Group total: {kes(entry.running_balance)} / goal {kes(chama.goal_amount)}.", "loan")
    fraud.check_large_payout(entry, balance)
    db.session.commit()


def next_due(loan):
    return local_date(loan.paid_out_at) + timedelta(days=30 * (loan.installments_paid + 1))


def apply_installment(loan, amount, today, member):
    on_schedule = today <= next_due(loan)
    loan.repaid += amount
    loan.installments_paid += 1
    scoring.on_installment(member, on_schedule)
    if loan.repaid >= loan.total_due:
        loan.status = "repaid"


def mark_defaults(today=None):
    today = today or today_nairobi()
    for loan in Loan.query.filter_by(status="active"):
        if today > next_due(loan) + timedelta(days=DEFAULT_GRACE_DAYS):
            loan.status = "defaulted"
            scoring.on_default(loan.member, loan.id)
            if loan.guarantor:
                scoring.apply(loan.guarantor, -50, "Guaranteed loan defaulted", key=f"guarantor:{loan.id}")
    db.session.commit()

