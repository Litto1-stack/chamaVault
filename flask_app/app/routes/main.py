"""Home dashboard, demo 'Viewing as' switch, and the signatory alerts page."""
from flask import Blueprint, abort, current_app, g, redirect, render_template, request, session, url_for

from ..auth import role_required
from ..extensions import db
from ..forms import to_int
from ..ledger import pool_balance, verify_chain
from ..models import Chama, FraudFlag, LedgerEntry, Member
from .. import rotation
from ..payments import active_loan, member_status, period_of
from ..stats import chama_stats
from ..timeutil import today_nairobi

bp = Blueprint("main", __name__)


@bp.route("/")
def landing():
    if not current_app.config.get("AUTH_REQUIRED", True):
        return dashboard()
    return render_template("landing.html")


@bp.route("/dashboard")
def dashboard():
    chama = g.viewer.chama if g.viewer else Chama.query.first()
    if chama is None:
        return render_template("error.html", title="No data yet",
                               message="Run 'python seed.py' in the flask_app folder, then refresh."), 200
    today = today_nairobi()
    balance = pool_balance(chama.id)
    rows = [(m, member_status(m, today)) for m in chama.members]
    recent = (LedgerEntry.query.filter_by(chama_id=chama.id).order_by(LedgerEntry.id.desc()).limit(5).all())
    from ..goals import member_goals, plan_goal
    personal = []
    for goal in member_goals(g.viewer.id)[:2]:
        personal.append((goal, plan_goal(goal.target_kes, goal.saved_kes, goal.monthly_pledge, goal.target_date)))
    return render_template(
        "dashboard.html", balance=balance, goal=chama.goal_amount,
        pct=min(100, round(balance * 100 / chama.goal_amount)) if chama.goal_amount else 0,
        rows=rows, recent=recent, loan=active_loan(g.viewer), chain=verify_chain(chama.id),
        mine=member_status(g.viewer, today), today=today, stats=chama_stats(chama, today),
        pot=rotation.pot_status(chama, period_of(today)) if chama.rotation_amount else None,
        held=rotation.held(chama.id), personal_goals=personal,
    )


@bp.post("/viewer")
def switch_viewer():
    if current_app.config.get("AUTH_REQUIRED", True):
        abort(404)
    member_id = to_int(request.form.get("member_id"), lo=1)
    if member_id and db.session.get(Member, member_id):
        session["viewer_id"] = member_id
        session["pin_fails"] = 0
    ref = request.referrer or ""
    return redirect(ref if ref.startswith(request.host_url) else url_for("main.dashboard"))


@bp.route("/alerts")
@role_required("signatory")
def alerts():
    flags = FraudFlag.query.filter_by(chama_id=g.viewer.chama_id).order_by(FraudFlag.id.desc()).limit(50).all()
    return render_template("alerts.html", flags=flags)

