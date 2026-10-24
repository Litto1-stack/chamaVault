"""Demo 'Viewing as' identity, role guards, and PIN checks (PINs are never logged or stored in plain text)."""
import re
from functools import wraps

from flask import abort, current_app, g, redirect, request, session, url_for
from werkzeug.security import check_password_hash

from .extensions import db
from .models import Account, Member

MAX_PIN_FAILS = 5


def load_viewer():
    """Resolve the signed-in member; keep seeded identity only in test mode."""
    member = db.session.get(Member, session.get("viewer_id") or 0)
    if member is None and not current_app.config.get("AUTH_REQUIRED", True):
        member = Member.query.filter_by(role="member").order_by(Member.id).first() or Member.query.first()
    g.viewer = member


def require_account_login():
    if not current_app.config.get("AUTH_REQUIRED", True):
        return
    public_endpoints = {
        "main.landing", "auth.login", "auth.signup", "auth.logout", "members.join",
        "info.page", "info.tools", "info.service_worker", "pay.mpesa_webhook",
    }
    if request.endpoint == "static" or request.endpoint in public_endpoints:
        return
    account = db.session.get(Account, session.get("account_id") or 0)
    if account is None or g.viewer is None or account.member_id != g.viewer.id:
        session.clear()
        return redirect(url_for("auth.login", next=request.full_path))


def role_required(*roles):
    def deco(fn):
        @wraps(fn)
        def wrapper(*a, **kw):
            if g.viewer is None or g.viewer.role not in roles:
                abort(403)
            return fn(*a, **kw)
        return wrapper
    return deco


def check_pin(member, pin) -> str | None:
    """Return None if the PIN is right, otherwise a safe error message. Locks after repeated failures."""
    if session.get("pin_fails", 0) >= MAX_PIN_FAILS:
        return "Too many wrong PIN attempts. Switch viewer or restart the demo to try again."
    if not re.fullmatch(r"\d{4}", pin or "") or not check_password_hash(member.pin_hash, pin):
        session["pin_fails"] = session.get("pin_fails", 0) + 1
        return "Incorrect PIN."
    session["pin_fails"] = 0
    return None
