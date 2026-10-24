"""Credit-score rules (pure functions) plus helpers that record score events."""
from .extensions import db
from .models import ScoreEvent

EARLY, ON_TIME, INSTALLMENT, STREAK, LATE, MISSED, DEFAULT = 15, 10, 25, 20, -15, -40, -100
MIN_SCORE, MAX_SCORE = 300, 850
STREAK_LENGTH = 3

RULES = [
    (EARLY, "Pay your contribution at least a day before the due date"),
    (ON_TIME, "Pay your contribution on the due date"),
    (INSTALLMENT, "Pay a loan installment on schedule"),
    (STREAK, "Every 3 contributions in a row that are on time or early"),
    (LATE, "Pay a contribution or installment after the due date"),
    (MISSED, "Miss a month's contribution entirely"),
    (DEFAULT, "Default on a loan"),
]


def contribution_delta(days_before_due: int) -> int:
    if days_before_due > 0:
        return EARLY
    return ON_TIME if days_before_due == 0 else LATE


def next_streak(streak: int, delta: int) -> int:
    return streak + 1 if delta > 0 else 0


def streak_bonus(streak: int) -> int:
    return STREAK if streak > 0 and streak % STREAK_LENGTH == 0 else 0


def clamp(score: int) -> int:
    return max(MIN_SCORE, min(MAX_SCORE, score))


def band(score: int) -> str:
    if score >= 700:
        return "Excellent"
    if score >= 600:
        return "Good"
    if score >= 500:
        return "Fair"
    return "Needs work"


def apply(member, delta, reason, key=None, created_at=None):
    """Record a score change. Returns None if a one-off event with this key already exists."""
    if key and ScoreEvent.query.filter_by(key=key).first():
        return None
    member.credit_score = clamp(member.credit_score + delta)
    event = ScoreEvent(member_id=member.id, delta=delta, reason=reason, key=key)
    if created_at:
        event.created_at = created_at
    db.session.add(event)
    return event


def on_contribution(member, days_before_due, created_at=None):
    delta = contribution_delta(days_before_due)
    label = {EARLY: "Early contribution", ON_TIME: "On-time contribution"}.get(delta, "Late contribution")
    apply(member, delta, label, created_at=created_at)
    member.streak = next_streak(member.streak, delta)
    bonus = streak_bonus(member.streak)
    if bonus:
        apply(member, bonus, f"{member.streak}-payment streak", created_at=created_at)


def on_installment(member, on_schedule, created_at=None):
    if on_schedule:
        apply(member, INSTALLMENT, "Loan installment on schedule", created_at=created_at)
    else:
        apply(member, LATE, "Late loan installment", created_at=created_at)


def on_missed(member, period):
    member.streak = 0
    return apply(member, MISSED, f"Missed contribution {period}", key=f"missed:{member.id}:{period}")


def on_default(member, loan_id):
    return apply(member, DEFAULT, "Loan default", key=f"default:{loan_id}")
