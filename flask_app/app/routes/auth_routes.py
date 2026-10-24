"""Account signup, login, and logout."""
import re
from urllib.parse import urlsplit

from flask import Blueprint, flash, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

from ..extensions import db
from ..models import Account, Chama, Member
from ..services.mpesa import normalize_phone

bp = Blueprint("auth", __name__)


def _safe_next(value):
    if value and value.startswith("/") and not value.startswith("//") and not urlsplit(value).netloc:
        return value
    return url_for("main.dashboard")


@bp.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        name = " ".join((request.form.get("name") or "").split())
        email = (request.form.get("email") or "").strip().lower()
        phone = normalize_phone(request.form.get("phone"))
        chama_name = " ".join((request.form.get("chama_name") or "").split())
        password = request.form.get("password") or ""
        password_confirm = request.form.get("password_confirm") or ""
        pin = request.form.get("pin") or ""
        pin_confirm = request.form.get("pin_confirm") or ""

        if not 2 <= len(name) <= 80 or not 2 <= len(chama_name) <= 80:
            flash("Enter your full name and a chama name (2 to 80 characters).", "error")
        elif not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", email) or len(email) > 120:
            flash("Enter a valid email address.", "error")
        elif not phone:
            flash("Enter a valid Kenyan phone number.", "error")
        elif Account.query.filter_by(email=email).first():
            flash("An account with that email already exists. Please sign in.", "error")
        elif len(password) < 8 or password != password_confirm:
            flash("Use a password of at least 8 characters and confirm it correctly.", "error")
        elif not re.fullmatch(r"\d{4}", pin) or pin != pin_confirm:
            flash("Choose and confirm a 4-digit transaction PIN.", "error")
        else:
            member = Member.query.filter_by(phone=phone).first()
            if member:
                if member.account:
                    flash("That phone number is already registered. Please sign in.", "error")
                    return render_template("signup.html")
                if not check_password_hash(member.pin_hash, pin):
                    flash("That phone belongs to an existing member. Enter their current transaction PIN to link this account.", "error")
                    return render_template("signup.html")
                member.email = email
                welcome = f"Welcome back, {member.first_name}. Your existing chama is linked."
            else:
                chama = Chama(
                    name=chama_name, monthly_amount=1000, goal_amount=50_000, due_day=1,
                    penalty_per_day=50, loan_approval_pct=60, loan_interest_pct=10,
                    loan_interest_type="flat", loan_approval_mode="vote",
                )
                db.session.add(chama)
                db.session.flush()
                member = Member(
                    chama_id=chama.id, name=name, phone=phone, email=email, role="treasurer",
                    pin_hash=generate_password_hash(pin),
                )
                db.session.add(member)
                db.session.flush()
                welcome = f"Your account and {chama.name} are ready."
            account = Account(email=email, password_hash=generate_password_hash(password), member_id=member.id)
            db.session.add(account)
            db.session.commit()
            session.clear()
            session["account_id"] = account.id
            session["viewer_id"] = member.id
            flash(welcome, "ok")
            return redirect(url_for("main.dashboard"))

    return render_template("signup.html")


@bp.route("/login", methods=["GET", "POST"])
def login():
    next_url = request.values.get("next", "")
    if request.method == "POST":
        email = (request.form.get("email") or "").strip().lower()
        account = Account.query.filter_by(email=email).first()
        if account is None or not check_password_hash(account.password_hash, request.form.get("password") or ""):
            flash("Email or password is incorrect.", "error")
        else:
            session.clear()
            session["account_id"] = account.id
            session["viewer_id"] = account.member_id
            return redirect(_safe_next(next_url))
    return render_template("login.html", next_url=next_url)


@bp.post("/logout")
def logout():
    session.clear()
    flash("You have signed out.", "ok")
    return redirect(url_for("main.landing"))