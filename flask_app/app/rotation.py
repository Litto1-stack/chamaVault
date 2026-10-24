"""Merry-go-round (ROSCA): equal monthly pot contributions, one member takes the whole pot each cycle."""
from .extensions import db
from .ledger import append_entry
from .models import LedgerEntry, Member, RotationSlot
from .payments import net_paid, period_of
from .services.sms import notify_all
from .timeutil import kes, local_date, now_utc


class RotationError(ValueError):
    """Raised for invalid rotation actions (message is safe to show the user)."""


def slots(chama):
    return RotationSlot.query.filter_by(chama_id=chama.id).order_by(RotationSlot.position).all()


def cycle_index(chama, period: str) -> int:
    sy, sm = map(int, chama.rotation_start.split("-"))
    y, m = map(int, period.split("-"))
    return (y - sy) * 12 + (m - sm)


def recipient(chama, period: str):
    order = slots(chama)
    if not chama.rotation_amount or not order or not chama.rotation_start:
        return None
    return order[cycle_index(chama, period) % len(order)].member


def pot_status(chama, period: str) -> dict:
    paid = [m for m in chama.members if net_paid(m.id, period, "rotation") >= chama.rotation_amount]
    done = LedgerEntry.query.filter_by(chama_id=chama.id, period=period, type="rotation_payout").first()
    return {"recipient": recipient(chama, period), "paid": paid, "pot": chama.rotation_amount * len(chama.members),
            "collected": chama.rotation_amount * len(paid), "complete": len(paid) == len(chama.members),
            "paid_out": done is not None}


def held(chama_id) -> int:
    """Money sitting in the pool that belongs to the pot (not available for loans)."""
    rows = db.session.query(db.func.coalesce(db.func.sum(LedgerEntry.amount), 0)).filter(
        LedgerEntry.chama_id == chama_id, LedgerEntry.type.in_(("rotation", "rotation_payout"))).scalar()
    return int(rows)


def pay_out_pot(chama, treasurer, period: str):
    status = pot_status(chama, period)
    if status["recipient"] is None:
        raise RotationError("Merry-go-round is not set up.")
    if status["paid_out"]:
        raise RotationError("This cycle's pot was already paid out.")
    if not status["complete"]:
        raise RotationError("Every member must pay into the pot before it can be paid out.")
    entry = append_entry(chama.id, status["recipient"].id, -status["pot"], "rotation_payout", "mpesa", treasurer.id,
                         period=period, ref="ROT" + period.replace("-", ""), created_at=now_utc())
    notify_all(chama, f"Merry-go-round: {kes(status['pot'])} was paid to {status['recipient'].first_name}. "
                      f"Next cycle starts soon.", "payment")
    db.session.commit()
    return entry


def add_member_to_rotation(chama, member):
    db.session.add(RotationSlot(chama_id=chama.id, member_id=member.id, position=len(slots(chama))))
