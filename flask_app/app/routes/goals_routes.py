"""Personal savings goals page and Vaulti-friendly planner JSON."""
from flask import Blueprint, flash, g, jsonify, redirect, render_template, request, url_for

from ..goals import GoalError, add_progress, create_goal, delete_goal, member_goals, plan_goal
from ..models import PersonalGoal
from ..extensions import db
from ..forms import to_int

bp = Blueprint("goals", __name__)


@bp.route("/goals", methods=["GET", "POST"])
def goals():
    if request.method == "POST":
        action = request.form.get("action") or "create"
        try:
            if action == "create":
                create_goal(g.viewer, request.form)
                flash("Goal saved. Vaulti can use it when you ask about saving.", "ok")
            elif action == "progress":
                goal = db.session.get(PersonalGoal, to_int(request.form.get("goal_id"), lo=1))
                if goal is None or goal.member_id != g.viewer.id:
                    raise GoalError("Goal not found.")
                amount = to_int(request.form.get("amount"), lo=1, hi=100_000_000)
                if amount is None:
                    raise GoalError("Enter how much you saved.")
                add_progress(goal, amount)
                flash("Progress updated.", "ok")
            elif action == "delete":
                goal = db.session.get(PersonalGoal, to_int(request.form.get("goal_id"), lo=1))
                if goal is None or goal.member_id != g.viewer.id:
                    raise GoalError("Goal not found.")
                delete_goal(goal)
                flash("Goal removed.", "ok")
            elif action == "email_digest":
                from ..services.email import goal_digest_email
                email = (request.form.get("email") or g.viewer.email or "").strip()
                if not email:
                    raise GoalError("Add an email address to send a digest.")
                goals_list = member_goals(g.viewer.id)
                if not goals_list:
                    raise GoalError("Create a goal first.")
                lines = []
                for goal in goals_list:
                    plan = plan_goal(goal.target_kes, goal.saved_kes, goal.monthly_pledge, goal.target_date)
                    lines.append(
                        f"{goal.name}: KES {goal.saved_kes:,} / {goal.target_kes:,} "
                        f"({plan['pct']}%) · pledge KES {goal.monthly_pledge:,}/mo"
                    )
                result = goal_digest_email(email, g.viewer.first_name, lines)
                if not result["ok"]:
                    raise GoalError(result.get("error") or "Email failed.")
                flash("Goal digest emailed." if not result.get("mock") else "Goal digest queued (Resend mock — add RESEND_API_KEY).", "ok")
            return redirect(url_for("goals.goals"))
        except GoalError as exc:
            flash(str(exc), "error")
            db.session.rollback()

    rows = []
    for goal in member_goals(g.viewer.id):
        rows.append((goal, plan_goal(goal.target_kes, goal.saved_kes, goal.monthly_pledge, goal.target_date)))
    return render_template("goals.html", rows=rows)


@bp.get("/goals/plan")
def plan_api():
    """Simple JSON planner for calculators / Vaulti chips."""
    target = to_int(request.args.get("target"), lo=100, hi=100_000_000) or 0
    saved = to_int(request.args.get("saved"), lo=0, hi=100_000_000) or 0
    pledge = to_int(request.args.get("pledge"), lo=0, hi=10_000_000) or 0
    raw = (request.args.get("date") or "").strip()
    target_date = None
    if raw:
        from datetime import date
        try:
            target_date = date.fromisoformat(raw)
        except ValueError:
            return jsonify(error="bad date"), 400
    return jsonify(plan_goal(target, saved, pledge, target_date))
