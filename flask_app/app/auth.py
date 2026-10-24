"""Demo 'Viewing as' identity, role guards, and PIN checks (PINs are never logged or stored in plain text)."""
import re
from functools import wraps

from flask import abort, g, session
from werkzeug.security import check_password_hash

from .extensions import db
from .models import Member

MAX_PIN_FAILS = 5


def load_viewer():
    """Resolve the demo viewer from the session; default to the first plain member."""
    member = db.session.get(Member, session.get("viewer_id") or 0)
    if member is None:
        member = Member.query.filter_by(role="member").order_by(Member.id).first() or Member.query.first()
    g.viewer = member


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
