"""Credit-score rule tests."""
from app import scoring
from app.models import Member


def test_contribution_points():
    assert scoring.contribution_delta(3) == 15       # early
    assert scoring.contribution_delta(0) == 10       # on time
    assert scoring.contribution_delta(-1) == -15     # late


def test_streak_resets_when_late_and_bonus_every_three():
    assert scoring.next_streak(2, 10) == 3
    assert scoring.next_streak(5, -15) == 0
    assert [scoring.streak_bonus(n) for n in (0, 1, 2, 3, 4, 6)] == [0, 0, 0, 20, 0, 20]


def test_score_is_clamped():
    assert scoring.clamp(2000) == scoring.MAX_SCORE and scoring.clamp(-50) == scoring.MIN_SCORE


def test_third_early_payment_earns_streak_bonus(app):
    m = Member(chama_id=1, name="T Test", phone="254700000099", pin_hash="x", credit_score=500)
    from app.extensions import db
    db.session.add(m)
    db.session.flush()
    for _ in range(3):
        scoring.on_contribution(m, 2)
    assert m.credit_score == 500 + 15 * 3 + 20 and m.streak == 3


def test_late_missed_and_default_penalties(app):
    m = Member.query.filter_by(name="Wanjiku Kamau").one()
    start = m.credit_score
    scoring.on_contribution(m, -2)
    assert m.credit_score == start - 15 and m.streak == 0
    scoring.on_missed(m, "2026-01")
    assert scoring.on_missed(m, "2026-01") is None   # idempotent
    scoring.on_default(m, 99)
    assert m.credit_score == start - 15 - 40 - 100


def test_installment_on_schedule_adds_25(app):
    m = Member.query.filter_by(name="Wanjiku Kamau").one()
    start = m.credit_score
    scoring.on_installment(m, True)
    assert m.credit_score == start + 25
