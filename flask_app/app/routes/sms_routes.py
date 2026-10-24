"""SMS outbox page and the reminder schedule with 'Trigger now' demo buttons."""
from flask import Blueprint, flash, g, redirect, render_template, request, url_for

from ..auth import role_required
from ..models import SmsLog
from ..reminders import KINDS, daily_checks, send_reminders

bp = Blueprint("sms", __name__)


@bp.route("/sms")
def outbox():
    messages = SmsLog.query.order_by(SmsLog.id.desc()).limit(200).all()
    return render_template("sms.html", messages=messages)


@bp.route("/reminders")
def reminders():
    return render_template("reminders.html", kinds=KINDS)


@bp.post("/reminders/trigger")
@role_required("treasurer")
def trigger():
    chama = g.viewer.chama
    kind = request.form.get("kind", "")
    if kind == "daily_checks":
        n = daily_checks(chama)
        flash(f"Daily checks done. {n} member(s) marked as missed.", "ok")
    elif kind in KINDS:
        n = send_reminders(chama, kind, force=True)
        flash(f"Sent {n} reminder SMS (demo trigger).", "ok")
    else:
        flash("Unknown reminder type.", "error")
    return redirect(url_for("sms.reminders"))
