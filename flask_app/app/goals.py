"""Personal savings goals: CRUD helpers and pure pledge math (not investment advice)."""
from __future__ import annotations

import math
from datetime import date

from .extensions import db
from .forms import to_int
from .models import PersonalGoal
from .timeutil import today_nairobi


class GoalError(ValueError):
    """Safe-to-show validation error."""


def months_between(start: date, end: date) -> int:
    """Whole calendar months from start to end (minimum 1 if end >= start)."""
    if end < start:
        return 0
    return max(1, (end.year - start.year) * 12 + (end.month - start.month) + (1 if end.day >= start.day else 0))


def plan_goal(target_kes: int, saved_kes: int, monthly_pledge: int, target_date: date | None,
              today: date | None = None) -> dict:
    """Arithmetic planner for Vaulti and the goals UI.

    Returns months_needed, shortfall, suggested_pledge, on_track.
    """
    today = today or today_nairobi()
    remaining = max(0, target_kes - saved_kes)
    months_needed = math.ceil(remaining / monthly_pledge) if monthly_pledge > 0 else None
    deadline_months = months_between(today, target_date) if target_date else None
    suggested = math.ceil(remaining / deadline_months) if deadline_months and remaining else monthly_pledge
    on_track = True
    if deadline_months is not None and months_needed is not None:
        on_track = months_needed <= deadline_months
    elif deadline_months is not None and monthly_pledge <= 0:
        on_track = remaining == 0
    return {
        "remaining": remaining,
        "months_needed": months_needed,
        "deadline_months": deadline_months,
        "suggested_pledge": suggested if remaining else 0,
        "on_track": on_track,
        "pct": min(100, round(saved_kes * 100 / target_kes)) if target_kes else 0,
    }


def create_goal(member, form) -> PersonalGoal:
    name = (form.get("name") or "").strip()
    target = to_int(form.get("target_kes"), lo=100, hi=100_000_000)
    pledge = to_int(form.get("monthly_pledge"), lo=0, hi=10_000_000)
    saved = to_int(form.get("saved_kes"), lo=0, hi=100_000_000) or 0
    raw_date = (form.get("target_date") or "").strip()
    if not 2 <= len(name) <= 80:
        raise GoalError("Give your goal a short name.")
    if target is None:
        raise GoalError("Enter a target amount in KES (at least 100).")
    if pledge is None:
        raise GoalError("Enter a monthly pledge (0 or more).")
    target_date = None
    if raw_date:
        try:
            target_date = date.fromisoformat(raw_date)
        except ValueError as exc:
            raise GoalError("Use a valid target date (YYYY-MM-DD).") from exc
        if target_date < today_nairobi():
            raise GoalError("Pick a target date in the future.")
    goal = PersonalGoal(
        member_id=member.id,
        name=name,
        target_kes=target,
        saved_kes=saved,
        monthly_pledge=pledge,
        target_date=target_date,
    )
    db.session.add(goal)
    db.session.commit()
    return goal


def add_progress(goal: PersonalGoal, amount: int) -> PersonalGoal:
    if amount < 1:
        raise GoalError("Enter a positive amount.")
    goal.saved_kes = min(goal.target_kes, goal.saved_kes + amount)
    db.session.commit()
    return goal


def delete_goal(goal: PersonalGoal) -> None:
    db.session.delete(goal)
    db.session.commit()


def member_goals(member_id: int) -> list[PersonalGoal]:
    return PersonalGoal.query.filter_by(member_id=member_id).order_by(PersonalGoal.id.desc()).all()
