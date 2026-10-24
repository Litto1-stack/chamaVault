"""Rule-based anomaly flags. Each hit is stored and a quiet SMS goes to the 2 signatories."""
from datetime import timedelta

from flask import current_app

from .extensions import db
from .models import Chama, FraudFlag, LedgerEntry
from .services.sms import notify_signatories
from .timeutil import kes, local_date, now_utc


def _flag(chama, rule, detail):
    db.session.add(FraudFlag(chama_id=chama.id, rule=rule, detail=detail))
    notify_signatories(chama, f"ChamaVault notice: {detail} Please review the ledger.")


def check_cash_for_self(entry):
    """Rule 1: the treasurer recorded a cash payment for themselves."""
    if entry.method == "cash" and entry.recorded_by_id == entry.member_id and entry.recorded_by.role == "treasurer":
        chama = db.session.get(Chama, entry.chama_id)
        _flag(chama, "treasurer_cash_self",
              f"Treasurer {entry.member.first_name} recorded a cash entry of {kes(entry.amount)} for themselves (#{entry.id}).")


def check_correction_burst(chama):
    """Rule 2: 2 or more corrections within 7 days."""
    since = now_utc() - timedelta(days=7)
    n = LedgerEntry.query.filter(LedgerEntry.chama_id == chama.id, LedgerEntry.type == "correction",
                                 LedgerEntry.created_at >= since).count()
    if n >= 2:
        _flag(chama, "correction_burst", f"{n} ledger corrections were made in the last 7 days.")


def check_large_payout(entry, balance_before):
    """Rule 3: a large payout within a couple of days after contribution day."""
    chama = db.session.get(Chama, entry.chama_id)
    cfg = current_app.config
    paid_day = local_date(entry.created_at)
    days_since_due = (paid_day - paid_day.replace(day=chama.due_day)).days
    is_large = balance_before > 0 and -entry.amount >= cfg["LARGE_PAYOUT_SHARE"] * balance_before
    if is_large and 0 <= days_since_due <= cfg["LARGE_PAYOUT_WINDOW_DAYS"]:
        _flag(chama, "large_payout_after_due",
              f"A payout of {kes(-entry.amount)} was made {days_since_due} day(s) after contribution day (#{entry.id}).")
