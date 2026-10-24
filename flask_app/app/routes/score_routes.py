"""Credit score page, printable statement with a verification code, and the code checker."""
import hashlib
import hmac

from flask import Blueprint, current_app, g, render_template, request

from .. import scoring
from ..extensions import db
from ..forms import to_int
from ..ledger import verify_chain
from ..models import LedgerEntry, Member, ScoreEvent
from ..timeutil import today_nairobi

bp = Blueprint("score", __name__)


def statement_code(member, entries) -> str:
    """Code tied to this member's ledger rows: changes if any of them is altered or added."""
    digest = hashlib.sha256("|".join(e.hash for e in entries).encode()).hexdigest()
    raw = hmac.new(current_app.config["SECRET_KEY"].encode(), f"{member.id}|{len(entries)}|{digest}".encode(),
                   hashlib.sha256).hexdigest()[:12].upper()
    return f"CV-{raw[:4]}-{raw[4:8]}-{raw[8:]}"


def _entries_for(member):
    return LedgerEntry.query.filter_by(member_id=member.id).order_by(LedgerEntry.id).all()


@bp.route("/score")
def score():
    events = ScoreEvent.query.filter_by(member_id=g.viewer.id).order_by(ScoreEvent.id.desc()).limit(10).all()
    return render_template("score.html", rules=scoring.RULES, events=events, band=scoring.band(g.viewer.credit_score),
                           lo=scoring.MIN_SCORE, hi=scoring.MAX_SCORE)


@bp.route("/statement")
def statement():
    entries = _entries_for(g.viewer)
    total_in = sum(e.amount for e in entries if e.amount > 0)
    total_out = -sum(e.amount for e in entries if e.amount < 0)
    return render_template("statement.html", entries=entries, total_in=total_in, total_out=total_out,
                           code=statement_code(g.viewer, entries), today=today_nairobi(),
                           chain_ok=verify_chain(g.viewer.chama_id)["ok"], band=scoring.band(g.viewer.credit_score))


@bp.route("/statement/check", methods=["GET", "POST"])
def check():
    result = None
    if request.method == "POST":
        member = db.session.get(Member, to_int(request.form.get("member_id"), lo=1) or 0)
        code = (request.form.get("code") or "").strip().upper()
        if member:
            result = hmac.compare_digest(code, statement_code(member, _entries_for(member)))
    return render_template("statement_check.html", result=result, members=Member.query.all())

