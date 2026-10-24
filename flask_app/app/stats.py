"""Dashboard numbers derived from the real ledger (balance history, monthly totals, mix, on-time rate)."""
from collections import defaultdict
from datetime import date

from .models import LedgerEntry, Loan
from .payments import period_of
from .timeutil import local_date

INFLOW_TYPES = ("contribution", "penalty", "savings", "welfare", "loan_installment", "rotation")
MIX_LABELS = {"contribution": "Contributions", "savings": "Extra savings", "welfare": "Welfare",
              "loan_installment": "Loan repayments", "penalty": "Penalties", "rotation": "Merry-go-round"}


def last_periods(today: date, n: int = 6) -> list:
    out, y, m = [], today.year, today.month
    for _ in range(n):
        out.append(f"{y}-{m:02d}")
        y, m = (y, m - 1) if m > 1 else (y - 1, 12)
    return out[::-1]


def chama_stats(chama, today: date) -> dict:
    entries = LedgerEntry.query.filter_by(chama_id=chama.id).order_by(LedgerEntry.id).all()
    by_id = {e.id: e for e in entries}
    kind = lambda e: by_id[e.corrects_id].type if e.type == "correction" and e.corrects_id in by_id else e.type

    collected, mix, on_time, total_contrib = defaultdict(int), defaultdict(int), 0, 0
    for e in entries:
        k = kind(e)
        if k == "contribution":
            collected[e.period] += e.amount
        if k in INFLOW_TYPES:
            mix[k] += e.amount
        if e.type == "contribution":
            total_contrib += 1
            due = date(int(e.period[:4]), int(e.period[5:]), chama.due_day)
            on_time += local_date(e.created_at) <= due

    expected = len(chama.members) * chama.monthly_amount
    short = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    months = [(short[int(p[5:]) - 1], collected.get(p, 0), expected) for p in last_periods(today)]
    return {
        "balance_points": [e.running_balance for e in entries],
        "months": months,
        "mix": [(MIX_LABELS[k], v) for k, v in sorted(mix.items(), key=lambda kv: -kv[1]) if v > 0],
        "on_time_pct": round(on_time * 100 / total_contrib) if total_contrib else 100,
        "pooled": sum(v for v in mix.values()),
        "members": len(chama.members),
        "active_loans": Loan.query.filter_by(chama_id=chama.id, status="active").count(),
    }
