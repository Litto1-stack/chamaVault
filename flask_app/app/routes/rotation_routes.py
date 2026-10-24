"""Merry-go-round page: who receives the pot, who has paid in, and the treasurer's payout."""
from flask import Blueprint, flash, g, redirect, render_template, request, url_for

from ..auth import check_pin, role_required
from ..rotation import RotationError, cycle_index, pay_out_pot, pot_status, recipient, slots
from ..payments import period_of
from ..timeutil import today_nairobi

bp = Blueprint("rotation", __name__)


@bp.route("/rotation")
def rotation():
    chama = g.viewer.chama
    if not chama.rotation_amount:
        return render_template("rotation.html", enabled=False)
    period = period_of(today_nairobi())
    order = slots(chama)
    status = pot_status(chama, period)
    idx = cycle_index(chama, period)
    paid_ids = {m.id for m in status["paid"]}
    seats = [{"member": s.member, "paid": s.member_id in paid_ids,
              "now": status["recipient"] and s.member_id == status["recipient"].id,
              "turn": idx + ((s.position - idx) % len(order))} for s in order]
    return render_template("rotation.html", enabled=True, status=status, seats=seats, amount=chama.rotation_amount,
                           period=period, mine_paid=g.viewer.id in paid_ids)


@bp.post("/rotation/payout")
@role_required("treasurer")
def payout():
    error = check_pin(g.viewer, request.form.get("pin"))
    if error is None:
        try:
            pay_out_pot(g.viewer.chama, g.viewer, period_of(today_nairobi()))
            flash("Pot paid out and recorded in the ledger.", "ok")
            return redirect(url_for("rotation.rotation"))
        except RotationError as exc:
            error = str(exc)
    flash(error, "error")
    return redirect(url_for("rotation.rotation"))
