"""Group rules (settings validation) and phone-number invites."""
import re
import secrets

from werkzeug.security import generate_password_hash

from . import rotation
from .extensions import db
from .forms import to_int
from .models import Chama, Invite, Member, SmsLog
from .payments import period_of
from .services.mpesa import normalize_phone
from .services.sms import notify_all
from .timeutil import kes, today_nairobi


class MemberError(ValueError):
    """Raised for invalid settings or invites (message is safe to show the user)."""


def update_rules(chama, form, actor):
    """Validate every field first, then apply. Raises MemberError listing the first problem."""
    spec = {"monthly_amount": (100, 100_000), "goal_amount": (1_000, 100_000_000), "due_day": (1, 28),
            "penalty_per_day": (0, 1_000), "loan_approval_pct": (1, 100), "rotation_amount": (0, 50_000)}
    values = {}
    for field, (lo, hi) in spec.items():
        v = to_int(form.get(field), lo=lo, hi=hi)
        if v is None:
            raise MemberError(f"{field.replace('_', ' ').capitalize()} must be a whole number from {lo:,} to {hi:,}.")
        values[field] = v
    kind, mode = form.get("loan_interest_type"), form.get("loan_approval_mode")
    if kind not in ("flat", "reducing") or mode not in ("vote", "officer"):
        raise MemberError("Choose a valid interest type and approval method.")
    pct = to_int(form.get("loan_interest_pct"), lo=0, hi=100 if kind == "flat" else 20)
    if pct is None:
        raise MemberError("Interest must be 0-100% (flat) or 0-20% per month (reducing balance).")
    for field, v in values.items():
        setattr(chama, field, v)
    chama.loan_interest_type, chama.loan_interest_pct, chama.loan_approval_mode = kind, pct, mode
    chama.require_guarantor = form.get("require_guarantor") == "on"
    if chama.rotation_amount and not rotation.slots(chama):
        for m in chama.members:
            rotation.add_member_to_rotation(chama, m)
    if chama.rotation_amount and not chama.rotation_start:
        chama.rotation_start = period_of(today_nairobi())
    notify_all(chama, f"Chama rules updated by {actor.first_name}: contribution {kes(chama.monthly_amount)} "
                      f"due day {chama.due_day}, loans {pct}% {kind}.", "rules")
    db.session.commit()


def create_invite(chama, name, raw_phone, base_url, email=None):
    name = (name or "").strip()
    phone = normalize_phone(raw_phone)
    email = (email or "").strip() or None
    if not 2 <= len(name) <= 80:
        raise MemberError("Enter the person's name.")
    if phone is None:
        raise MemberError("Enter a valid Kenyan phone number, like 0712 345 678.")
    if email and ("@" not in email or len(email) > 120):
        raise MemberError("Enter a valid email address, or leave it blank.")
    if Member.query.filter_by(phone=phone).first():
        raise MemberError("That phone number is already in the chama.")
    invite = Invite(chama_id=chama.id, code=secrets.token_urlsafe(8), name=name, phone=phone, email=email)
    db.session.add(invite)
    join_url = f"{base_url}join/{invite.code}"
    # No member row exists yet, so the invite SMS goes straight to the outbox with the number.
    db.session.add(SmsLog(to_phone=phone, kind="invite",
                          body=f"Hi {name.split()[0]}, you are invited to join {chama.name} on ChamaVault: {join_url}"))
    db.session.commit()
    if email:
        from .services.email import invite_email
        invite_email(email, name, chama.name, join_url)
    return invite


def accept_invite(invite, pin, pin_confirm):
    if invite.used:
        raise MemberError("This invite was already used.")
    if not re.fullmatch(r"\d{4}", pin or "") or pin != pin_confirm:
        raise MemberError("Choose a 4-digit PIN and type it twice the same.")
    if Member.query.filter_by(phone=invite.phone).first():
        raise MemberError("That phone number is already in the chama.")
    chama = db.session.get(Chama, invite.chama_id)
    member = Member(chama_id=chama.id, name=invite.name, phone=invite.phone, email=invite.email,
                    role="member", pin_hash=generate_password_hash(pin))
    db.session.add(member)
    db.session.flush()
    invite.used = True
    if chama.rotation_amount:
        rotation.add_member_to_rotation(chama, member)
    notify_all(chama, f"{member.first_name} joined {chama.name}. Welcome!", "member")
    db.session.commit()
    return member

