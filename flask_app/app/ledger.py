"""Hash-chained ledger: append entries, verify the chain, and apply corrections."""
import hashlib
import json

from .extensions import db
from .models import LedgerEntry
from .timeutil import now_utc

GENESIS = "0" * 64
HASHED_FIELDS = ("chama_id", "member_id", "amount", "type", "method", "recorded_by_id",
                 "created_at", "period", "ref", "corrects_id", "reason", "running_balance")


class LedgerError(ValueError):
    """Raised for invalid ledger operations (message is safe to show the user)."""


def compute_hash(entry, prev_hash: str) -> str:
    values = [getattr(entry, f) for f in HASHED_FIELDS]
    values = [v.isoformat() if hasattr(v, "isoformat") else v for v in values]
    payload = json.dumps([prev_hash, *values], separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(payload.encode()).hexdigest()


def last_entry(chama_id):
    return (LedgerEntry.query.filter_by(chama_id=chama_id)
            .order_by(LedgerEntry.id.desc()).first())


def pool_balance(chama_id) -> int:
    last = last_entry(chama_id)
    return last.running_balance if last else 0


def append_entry(chama_id, member_id, amount, type, method, recorded_by_id,
                 period=None, ref=None, corrects_id=None, reason=None, created_at=None):
    last = last_entry(chama_id)
    entry = LedgerEntry(
        chama_id=chama_id, member_id=member_id, amount=amount, type=type, method=method,
        recorded_by_id=recorded_by_id, period=period, ref=ref, corrects_id=corrects_id,
        reason=reason, created_at=created_at or now_utc(),
        prev_hash=last.hash if last else GENESIS,
        running_balance=(last.running_balance if last else 0) + amount,
    )
    entry.hash = compute_hash(entry, entry.prev_hash)
    db.session.add(entry)
    db.session.flush()
    return entry


def verify_chain(chama_id) -> dict:
    """Recompute every hash in order; report the first broken record, if any."""
    prev_hash, balance, count = GENESIS, 0, 0
    for e in LedgerEntry.query.filter_by(chama_id=chama_id).order_by(LedgerEntry.id):
        count += 1
        balance += e.amount
        if e.prev_hash != prev_hash:
            return {"ok": False, "count": count, "broken_id": e.id,
                    "reason": "Link to the previous record is broken (a record was removed or reordered)."}
        if e.running_balance != balance:
            return {"ok": False, "count": count, "broken_id": e.id,
                    "reason": "Running balance does not match the sum of entries."}
        if e.hash != compute_hash(e, prev_hash):
            return {"ok": False, "count": count, "broken_id": e.id,
                    "reason": "Record contents were changed after it was written."}
        prev_hash = e.hash
    return {"ok": True, "count": count, "broken_id": None, "reason": None, "tip": prev_hash}


def corrections_by_original(chama_id) -> dict:
    """Map original entry id -> its correction entry (one correction per entry)."""
    rows = LedgerEntry.query.filter(LedgerEntry.chama_id == chama_id,
                                    LedgerEntry.corrects_id.isnot(None)).all()
    return {c.corrects_id: c for c in rows}


def correct_entry(original_id, new_amount, reason, recorded_by_id):
    """Append a correction for `original_id`; the original row is never touched."""
    original = db.session.get(LedgerEntry, original_id)
    reason = (reason or "").strip()
    if original is None:
        raise LedgerError("That ledger entry does not exist.")
    if original.type == "correction":
        raise LedgerError("A correction cannot itself be corrected.")
    if original.id in corrections_by_original(original.chama_id):
        raise LedgerError("This entry has already been corrected.")
    if not isinstance(new_amount, int) or new_amount == original.amount:
        raise LedgerError("Enter a new amount that differs from the original.")
    if original.amount * new_amount < 0:
        raise LedgerError("The corrected amount must keep the same direction (in or out).")
    if not 10 <= len(reason) <= 300:
        raise LedgerError("Give a written reason of 10 to 300 characters.")
    return append_entry(original.chama_id, original.member_id, new_amount - original.amount,
                        "correction", "system", recorded_by_id, period=original.period,
                        corrects_id=original.id, reason=reason)
