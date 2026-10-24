"""Treasurer rules page, member invites by phone, and the public join page."""
from flask import Blueprint, current_app, flash, g, redirect, render_template, request, session, url_for
import re
from werkzeug.security import generate_password_hash

from ..auth import check_pin, role_required
from ..extensions import db
from ..members import MemberError, accept_invite, create_invite, update_rules
from ..models import Account, Invite

bp = Blueprint("members", __name__)


@bp.route("/settings", methods=["GET", "POST"])
@role_required("treasurer")
def settings():
    if request.method == "POST":
        error = check_pin(g.viewer, request.form.get("pin"))
        if error is None:
            try:
                update_rules(g.viewer.chama, request.form, g.viewer)
                flash("Rules saved. Every member was told by SMS.", "ok")
                return redirect(url_for("members.settings"))
            except MemberError as exc:
                error = str(exc)
        flash(error, "error")
        db.session.rollback()
    return render_template("settings.html")


@bp.route("/invite", methods=["GET", "POST"])
@role_required("treasurer")
def invite():
    if request.method == "POST":
        try:
            inv = create_invite(
                g.viewer.chama, request.form.get("name"), request.form.get("phone"),
                request.host_url, email=request.form.get("email"),
            )
            flash(f"Invite sent to {inv.name}. Open the SMS outbox to see the link.", "ok")
            return redirect(url_for("members.invite"))
        except MemberError as exc:
            flash(str(exc), "error")
    pending = Invite.query.filter_by(chama_id=g.viewer.chama_id, used=False).order_by(Invite.id.desc()).all()
    return render_template("invite.html", pending=pending)


@bp.route("/join/<code>", methods=["GET", "POST"])
def join(code):
    inv = Invite.query.filter_by(code=code).first()
    if inv is None or inv.used:
        return render_template("error.html", title="Invite not valid",
                               message="This invite link is invalid or has already been used."), 404
    if request.method == "POST":
        try:
            auth_required = current_app.config.get("AUTH_REQUIRED", True)
            email = (request.form.get("email") or "").strip().lower()
            password = request.form.get("password") or ""
            password_confirm = request.form.get("password_confirm") or ""
            if auth_required:
                if not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", email) or len(email) > 120:
                    raise MemberError("Enter a valid email address.")
                if Account.query.filter_by(email=email).first():
                    raise MemberError("An account with that email already exists. Please sign in first.")
                if len(password) < 8 or password != password_confirm:
                    raise MemberError("Use a password of at least 8 characters and confirm it correctly.")
            member = accept_invite(inv, request.form.get("pin"), request.form.get("pin_confirm"))
            session.clear()
            if auth_required:
                account = Account(email=email, password_hash=generate_password_hash(password), member_id=member.id)
                member.account = account
                db.session.add(account)
                db.session.commit()
                session["account_id"] = account.id
            session["viewer_id"] = member.id
            flash(f"Welcome to {member.chama.name}, {member.first_name}!", "ok")
            return redirect(url_for("main.dashboard"))
        except MemberError as exc:
            flash(str(exc), "error")
            db.session.rollback()
    return render_template("join.html", inv=inv)
