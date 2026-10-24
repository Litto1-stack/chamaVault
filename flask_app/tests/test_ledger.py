"""Hash-chain tests: verification, tamper detection, append-only guard, corrections."""
import pytest
from sqlalchemy import text

from app.extensions import db
from app.ledger import LedgerError, correct_entry, corrections_by_original, verify_chain
from app.models import Chama, LedgerEntry, Member


def test_seeded_chain_is_valid(app):
    result = verify_chain(Chama.query.first().id)
    assert result["ok"] and result["count"] > 20


def test_tampered_amount_is_reported_at_first_broken_record(app):
    chama_id = Chama.query.first().id
    db.session.execute(text("UPDATE ledger_entry SET amount = amount + 100 WHERE id = 7"))
    db.session.commit()
    result = verify_chain(chama_id)
    assert not result["ok"] and result["broken_id"] == 7


def test_removed_record_breaks_the_link(app):
    chama_id = Chama.query.first().id
    db.session.execute(text("DELETE FROM ledger_entry WHERE id = 5"))
    db.session.commit()
    result = verify_chain(chama_id)
    assert not result["ok"] and result["broken_id"] == 6


def test_orm_cannot_update_or_delete_entries(app):
    entry = db.session.get(LedgerEntry, 1)
    entry.amount = 1
    with pytest.raises(RuntimeError):
        db.session.commit()
    db.session.rollback()
    db.session.delete(db.session.get(LedgerEntry, 1))
    with pytest.raises(RuntimeError):
        db.session.commit()
    db.session.rollback()


def test_correction_keeps_original_and_adjusts_balance(app):
    treasurer = Member.query.filter_by(role="treasurer").one()
    original = LedgerEntry.query.filter_by(type="contribution").first()
    before = LedgerEntry.query.order_by(LedgerEntry.id.desc()).first().running_balance
    fix = correct_entry(original.id, original.amount - 500, "Wrong amount typed at the meeting", treasurer.id)
    db.session.commit()
    assert original.amount == 1500                               # original untouched
    assert fix.amount == -500 and fix.running_balance == before - 500
    assert corrections_by_original(original.chama_id)[original.id].id == fix.id
    assert verify_chain(original.chama_id)["ok"]


def test_correction_needs_a_real_reason_and_only_once(app):
    treasurer = Member.query.filter_by(role="treasurer").one()
    original = LedgerEntry.query.filter_by(type="contribution").first()
    with pytest.raises(LedgerError):
        correct_entry(original.id, 1000, "oops", treasurer.id)
    correct_entry(original.id, 1000, "Member paid KES 1,000 not 1,500", treasurer.id)
    with pytest.raises(LedgerError):
        correct_entry(original.id, 900, "Trying to correct a second time", treasurer.id)
