"""Public-style info pages, calculators, CSV export, and the PWA service worker."""
import csv
import io

from flask import Blueprint, Response, current_app, g, render_template, send_from_directory

from ..models import LedgerEntry

bp = Blueprint("info", __name__)

PAGES = {"how-it-works": "How it works", "features": "Features", "faq": "FAQ", "privacy": "Privacy", "terms": "Terms"}


def _safe_cell(value):
    """Stop spreadsheet formula injection: text starting with = + - @ gets a leading quote."""
    text = "" if value is None else str(value)
    return "'" + text if text[:1] in ("=", "+", "-", "@") else text


@bp.route("/tools")
def tools():
    return render_template("tools.html")


@bp.route("/info/<page>")
def page(page):
    if page not in PAGES:
        return render_template("error.html", title="Not found", message="We couldn't find that page."), 404
    return render_template(f"info_{page.replace('-', '_')}.html", title=PAGES[page])


@bp.route("/ledger.csv")
def ledger_csv():
    rows = LedgerEntry.query.filter_by(chama_id=g.viewer.chama_id).order_by(LedgerEntry.id).all()
    out = io.StringIO()
    w = csv.writer(out)
    w.writerow(["id", "date_utc", "member", "type", "method", "amount_kes", "balance_kes", "recorded_by", "reason", "hash"])
    for e in rows:
        w.writerow([e.id, e.created_at.isoformat(), _safe_cell(e.member.name), e.type, e.method, e.amount,
                    e.running_balance, _safe_cell(e.recorded_by.name), _safe_cell(e.reason), e.hash])
    return Response(out.getvalue(), mimetype="text/csv",
                    headers={"Content-Disposition": "attachment; filename=chamavault-ledger.csv"})


@bp.route("/sw.js")
def service_worker():
    resp = send_from_directory(current_app.static_folder, "sw.js", mimetype="text/javascript")
    resp.headers["Service-Worker-Allowed"] = "/"
    resp.headers["Cache-Control"] = "no-cache"
    return resp
