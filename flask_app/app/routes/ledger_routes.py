"""Ledger list, chain verification, and treasurer corrections (no edit or delete routes exist)."""
from flask import Blueprint, flash, g, redirect, render_template, request, url_for

from .. import fraud
from ..auth import check_pin, role_required
from ..extensions import db
from ..forms import to_int
from ..ledger import LedgerError, correct_entry, corrections_by_original, verify_chain
from ..models import Chama, LedgerEntry
from ..services.sms import notify_all
from ..timeutil import kes

bp = Blueprint("ledger", __name__)


@bp.route("/ledger")
def ledger():
    chama = Chama.query.first()
    entries = (LedgerEntry.query.filter_by(chama_id=chama.id)
               .order_by(LedgerEntry.id.desc()).limit(150).all())
    return render_template("ledger.html", entries=entries, corrections=corrections_by_original(chama.id))


@bp.route("/verify")
def verify():
    chama = Chama.query.first()
    return render_template("verify.html", result=verify_chain(chama.id))


@bp.route("/ledger/<int:entry_id>/correct", methods=["GET", "POST"])
@role_required("treasurer")
def correct(entry_id):
    entry = db.get_or_404(LedgerEntry, entry_id)
    if request.method == "POST":
        new_amount = to_int(request.form.get("new_amount"), lo=-1_000_000, hi=1_000_000)
        error = check_pin(g.viewer, request.form.get("pin"))
        if error is None:
            try:
                if new_amount is None:
                    raise LedgerError("Enter the corrected amount as a whole number.")
                old = entry.amount
                fix = correct_entry(entry.id, new_amount, request.form.get("reason"), g.viewer.id)
                notify_all(g.viewer.chama,
                           f"CORRECTION by {g.viewer.first_name} (treasurer): entry #{entry.id} for "
                           f"{entry.member.first_name} changed from {kes(old)} to {kes(new_amount)}. "
                           f"Reason: {fix.reason}", "correction")
                fraud.check_correction_burst(g.viewer.chama)
                db.session.commit()
                flash("Correction recorded. The original stays visible and everyone was notified.", "ok")
                return redirect(url_for("ledger.ledger"))
            except LedgerError as exc:
                error = str(exc)
        flash(error, "error")
    return render_template("correct.html", entry=entry)
