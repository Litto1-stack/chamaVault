"""Database models: Chama, Member, LedgerEntry, Loan, LoanVote, SmsLog, ScoreEvent, FraudFlag, PersonalGoal."""
from sqlalchemy import event

from .extensions import db
from .timeutil import now_utc

ROLES = ("treasurer", "signatory", "member")


class Account(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), nullable=False, unique=True, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    member_id = db.Column(db.ForeignKey("member.id"), nullable=False, unique=True)
    member = db.relationship("Member", backref=db.backref("account", uselist=False))


class Chama(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    monthly_amount = db.Column(db.Integer, nullable=False)       # KES
    goal_amount = db.Column(db.Integer, nullable=False)          # KES
    due_day = db.Column(db.Integer, nullable=False)              # day of month, 1-28
    penalty_per_day = db.Column(db.Integer, nullable=False)      # KES per day late
    loan_approval_pct = db.Column(db.Integer, nullable=False)    # % of voters who must approve
    loan_interest_pct = db.Column(db.Integer, nullable=False)    # flat: total % of principal; reducing: % per month
    loan_interest_type = db.Column(db.String(10), nullable=False, default="flat")      # flat|reducing
    loan_approval_mode = db.Column(db.String(10), nullable=False, default="vote")      # vote|officer
    require_guarantor = db.Column(db.Boolean, nullable=False, default=False)
    rotation_amount = db.Column(db.Integer, nullable=False, default=0)   # merry-go-round: KES per member per month (0 = off)
    rotation_start = db.Column(db.String(7))                             # "YYYY-MM" of the first cycle
    is_solo = db.Column(db.Boolean, nullable=False, default=False)       # single-person savings vault
    members = db.relationship("Member", backref="chama", order_by="Member.id")


class Member(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    chama_id = db.Column(db.ForeignKey("chama.id"), nullable=False)
    name = db.Column(db.String(80), nullable=False)
    phone = db.Column(db.String(15), unique=True, nullable=False)  # 2547XXXXXXXX
    email = db.Column(db.String(120))                              # optional; Resend notifications
    role = db.Column(db.String(12), nullable=False, default="member")
    pin_hash = db.Column(db.String(255), nullable=False)
    credit_score = db.Column(db.Integer, nullable=False, default=500)
    streak = db.Column(db.Integer, nullable=False, default=0)      # on-time contribution streak

    @property
    def first_name(self):
        return self.name.split()[0]


class LedgerEntry(db.Model):
    """Append-only. Amounts are signed KES: money in is positive, payouts negative."""
    id = db.Column(db.Integer, primary_key=True)
    chama_id = db.Column(db.ForeignKey("chama.id"), nullable=False, index=True)
    member_id = db.Column(db.ForeignKey("member.id"), nullable=False, index=True)
    amount = db.Column(db.Integer, nullable=False)
    type = db.Column(db.String(20), nullable=False)  # contribution|penalty|loan_installment|loan_payout|savings|welfare|correction
    method = db.Column(db.String(10), nullable=False)  # cash|mpesa|card|system
    recorded_by_id = db.Column(db.ForeignKey("member.id"), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=now_utc)
    period = db.Column(db.String(7))                 # "YYYY-MM" the entry counts towards
    ref = db.Column(db.String(40))                   # M-Pesa receipt / card auth reference
    corrects_id = db.Column(db.ForeignKey("ledger_entry.id"))
    reason = db.Column(db.String(300))
    running_balance = db.Column(db.Integer, nullable=False)
    prev_hash = db.Column(db.String(64), nullable=False, unique=True)  # unique => chain cannot fork
    hash = db.Column(db.String(64), nullable=False)

    member = db.relationship("Member", foreign_keys=[member_id])
    recorded_by = db.relationship("Member", foreign_keys=[recorded_by_id])


@event.listens_for(LedgerEntry, "before_update")
@event.listens_for(LedgerEntry, "before_delete")
def _ledger_is_append_only(mapper, connection, target):
    raise RuntimeError("The ledger is append-only: use a correction entry instead.")


class Loan(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    chama_id = db.Column(db.ForeignKey("chama.id"), nullable=False)
    member_id = db.Column(db.ForeignKey("member.id"), nullable=False)
    principal = db.Column(db.Integer, nullable=False)
    total_due = db.Column(db.Integer, nullable=False)          # principal + flat interest
    installments = db.Column(db.Integer, nullable=False)
    installment_amount = db.Column(db.Integer, nullable=False)
    guarantor_id = db.Column(db.ForeignKey("member.id"))
    guarantor_ok = db.Column(db.Boolean, nullable=False, default=True)   # guarantor has accepted (or none needed)
    installments_paid = db.Column(db.Integer, nullable=False, default=0)
    repaid = db.Column(db.Integer, nullable=False, default=0)
    status = db.Column(db.String(10), nullable=False, default="pending")  # pending|rejected|approved|active|repaid|defaulted
    requested_at = db.Column(db.DateTime, nullable=False, default=now_utc)
    paid_out_at = db.Column(db.DateTime)

    member = db.relationship("Member", foreign_keys=[member_id])
    guarantor = db.relationship("Member", foreign_keys=[guarantor_id])
    votes = db.relationship("LoanVote", backref="loan")


class LoanVote(db.Model):
    __table_args__ = (db.UniqueConstraint("loan_id", "member_id"),)
    id = db.Column(db.Integer, primary_key=True)
    loan_id = db.Column(db.ForeignKey("loan.id"), nullable=False)
    member_id = db.Column(db.ForeignKey("member.id"), nullable=False)
    approve = db.Column(db.Boolean, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=now_utc)

    member = db.relationship("Member")


class SmsLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    member_id = db.Column(db.ForeignKey("member.id"))
    to_phone = db.Column(db.String(15), nullable=False)
    body = db.Column(db.String(320), nullable=False)
    kind = db.Column(db.String(24), nullable=False)  # payment|correction|reminder|fraud_alert|loan
    status = db.Column(db.String(10), nullable=False, default="sent")
    created_at = db.Column(db.DateTime, nullable=False, default=now_utc)

    member = db.relationship("Member")


class ScoreEvent(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    member_id = db.Column(db.ForeignKey("member.id"), nullable=False, index=True)
    delta = db.Column(db.Integer, nullable=False)
    reason = db.Column(db.String(120), nullable=False)
    key = db.Column(db.String(60), unique=True)      # makes one-off events (missed, default) idempotent
    created_at = db.Column(db.DateTime, nullable=False, default=now_utc)


class FraudFlag(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    chama_id = db.Column(db.ForeignKey("chama.id"), nullable=False)
    rule = db.Column(db.String(30), nullable=False)
    detail = db.Column(db.String(300), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=now_utc)


class RotationSlot(db.Model):
    """Merry-go-round order: position 0 receives the pot in the first cycle."""
    id = db.Column(db.Integer, primary_key=True)
    chama_id = db.Column(db.ForeignKey("chama.id"), nullable=False)
    member_id = db.Column(db.ForeignKey("member.id"), nullable=False, unique=True)
    position = db.Column(db.Integer, nullable=False)

    member = db.relationship("Member")


class Invite(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    chama_id = db.Column(db.ForeignKey("chama.id"), nullable=False)
    code = db.Column(db.String(24), unique=True, nullable=False)
    name = db.Column(db.String(80), nullable=False)
    phone = db.Column(db.String(15), nullable=False)
    email = db.Column(db.String(120))
    used = db.Column(db.Boolean, nullable=False, default=False)
    created_at = db.Column(db.DateTime, nullable=False, default=now_utc)


class Election(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    chama_id = db.Column(db.ForeignKey("chama.id"), nullable=False)
    role = db.Column(db.String(12), nullable=False, default="treasurer")
    status = db.Column(db.String(8), nullable=False, default="open")   # open|closed
    winner_id = db.Column(db.ForeignKey("member.id"))
    created_at = db.Column(db.DateTime, nullable=False, default=now_utc)

    candidates = db.relationship("Candidate", backref="election")
    winner = db.relationship("Member")


class Candidate(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    election_id = db.Column(db.ForeignKey("election.id"), nullable=False)
    member_id = db.Column(db.ForeignKey("member.id"), nullable=False)

    member = db.relationship("Member")


class Ballot(db.Model):
    """Records THAT a member voted, never WHAT they voted (the ballot is secret)."""
    __table_args__ = (db.UniqueConstraint("election_id", "voter_id"),)
    id = db.Column(db.Integer, primary_key=True)
    election_id = db.Column(db.ForeignKey("election.id"), nullable=False)
    voter_id = db.Column(db.ForeignKey("member.id"), nullable=False)


class ElectionVote(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    election_id = db.Column(db.ForeignKey("election.id"), nullable=False)
    candidate_id = db.Column(db.ForeignKey("candidate.id"), nullable=False)


class PersonalGoal(db.Model):
    """Member-owned savings target (separate from the chama pool goal)."""
    id = db.Column(db.Integer, primary_key=True)
    member_id = db.Column(db.ForeignKey("member.id"), nullable=False, index=True)
    name = db.Column(db.String(80), nullable=False)
    target_kes = db.Column(db.Integer, nullable=False)
    saved_kes = db.Column(db.Integer, nullable=False, default=0)
    monthly_pledge = db.Column(db.Integer, nullable=False, default=0)
    target_date = db.Column(db.Date)
    created_at = db.Column(db.DateTime, nullable=False, default=now_utc)

    member = db.relationship("Member", backref="personal_goals")

