"""SMS reminders and daily checks, scheduled with APScheduler (and triggerable on demand)."""
from datetime import timedelta

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from . import loans, scoring
from .extensions import db
from .models import Chama
from .payments import due_date_for, member_status, period_of
from .services.sms import notify_members
from .timeutil import NAIROBI, kes, today_nairobi

MISSED_AFTER_DAYS = 7

KINDS = {
    "day_before": ("Day-before reminder (6 PM, everyone)", "everyone"),
    "due_morning": ("Due-day reminder (8 AM, unpaid only)", "unpaid"),
    "due_evening": ("Due-day final reminder (5 PM, still unpaid)", "unpaid"),
}


def _message(kind, chama):
    amt = kes(chama.monthly_amount)
    return {
        "day_before": f"{chama.name}: your {amt} contribution is due tomorrow. Pay early to boost your score.",
        "due_morning": f"{chama.name}: your {amt} contribution is due today. Pay in ChamaVault before 5 PM to avoid a penalty.",
        "due_evening": f"{chama.name}: your {amt} is still unpaid. Penalty of {kes(chama.penalty_per_day)}/day starts tomorrow.",
    }[kind]


def send_reminders(chama, kind, force=False, today=None):
    """Send one reminder round. Scheduled runs only fire on the right date; demos use force=True."""
    today = today or today_nairobi()
    due = due_date_for(chama, today)
    right_day = today == due - timedelta(days=1) if kind == "day_before" else today == due
    if not (force or right_day):
        return 0
    targets = [m for m in chama.members
               if KINDS[kind][1] == "everyone" or member_status(m, today)["status"] != "paid"]
    notify_members(targets, _message(kind, chama), f"reminder")
    db.session.commit()
    return len(targets)


def daily_checks(chama, today=None):
    """Mark members who missed the month (7+ days overdue) and default stale loans."""
    today = today or today_nairobi()
    marked = 0
    for m in chama.members:
        s = member_status(m, today)
        if s["status"] == "overdue" and s["days"] >= MISSED_AFTER_DAYS:
            marked += 1 if scoring.on_missed(m, period_of(today)) else 0
    db.session.commit()
    loans.mark_defaults(today)
    return marked


def start_scheduler(app):
    """Three reminder slots plus a nightly check, all in Africa/Nairobi time."""
    scheduler = BackgroundScheduler(timezone=NAIROBI)

    def run(fn, *args):
        def job():
            with app.app_context():
                chama = Chama.query.first()
                if chama:
                    fn(chama, *args)
        return job

    scheduler.add_job(run(send_reminders, "day_before"), CronTrigger(hour=18, minute=0, timezone=NAIROBI))
    scheduler.add_job(run(send_reminders, "due_morning"), CronTrigger(hour=8, minute=0, timezone=NAIROBI))
    scheduler.add_job(run(send_reminders, "due_evening"), CronTrigger(hour=17, minute=0, timezone=NAIROBI))
    scheduler.add_job(run(daily_checks), CronTrigger(hour=0, minute=5, timezone=NAIROBI))
    scheduler.start()
    return scheduler
