"""Payment screen, receipt, treasurer cash recording, M-Pesa mock webhook and demo simulator."""
import hmac

from flask import Blueprint, current_app, flash, g, jsonify, redirect, render_template, request, url_for

from ..auth import check_pin, role_required
from ..extensions import csrf, db
from ..forms import to_int
from ..models import LedgerEntry, Member
from ..payments import PaymentError, available_items, member_status, period_of, record_payment
from ..services.card import mock_charge, validate_card
from ..services.mpesa import get_mpesa_service, normalize_phone
from ..timeutil import today_nairobi

bp = Blueprint("pay", __name__)


def _page(selected=None, **extra):
    items = available_items(g.viewer, today_nairobi())
    chosen = selected if selected in {i["key"] for i in items} else items[0]["key"]
    return render_template("pay.html", items=items, selected=chosen, **extra)


@bp.route("/pay", methods=["GET", "POST"])
def pay():
    if request.method == "GET":
        return _page(request.args.get("item"))
    form = request.form
    key, method = form.get("item", ""), form.get("method", "")
    amount = to_int(form.get("amount"), lo=1, hi=500_000)
    errors = []
    if amount is None:
        errors.append("Enter a whole-number amount above zero.")
    ref = None
    if method == "card":
        # Card fields are validated for format and dropped immediately; they are never stored or logged.
        errors += validate_card(form.get("card_name"), form.get("card_number"), form.get("card_expiry"), form.get("card_cvv"))
        ref = None if errors else mock_charge()
    elif method == "mpesa":
        mpesa = get_mpesa_service()
        req = mpesa.stk_push(g.viewer.phone, amount or 0, key)
        ref = mpesa.complete(req, g.viewer, form.get("mpesa_pin", ""))
        if ref is None and not errors:
            errors.append("M-Pesa PIN was not accepted. Payment cancelled.")
    else:
        errors.append("Choose M-Pesa or Card.")
    if not errors:
        try:
            entry = record_payment(g.viewer, key, amount, method, g.viewer, ref=ref)
            return redirect(url_for("pay.receipt", entry_id=entry.id))
        except PaymentError as exc:
            errors.append(str(exc))
    for e in errors:
        flash(e, "error")
    return _page(key)


@bp.route("/receipt/<int:entry_id>")
def receipt(entry_id):
    entry = db.get_or_404(LedgerEntry, entry_id)
    return render_template("receipt.html", e=entry)


@bp.route("/cash", methods=["GET", "POST"])
@role_required("treasurer")
def cash():
    chama = g.viewer.chama
    if request.method == "POST":
        target = db.session.get(Member, to_int(request.form.get("member_id"), lo=1) or 0)
        amount = to_int(request.form.get("amount"), lo=1, hi=500_000)
        error = check_pin(g.viewer, request.form.get("pin"))
        if error is None:
            try:
                if target is None or target.chama_id != chama.id or amount is None:
                    raise PaymentError("Choose a member and enter a valid amount.")
                entry = record_payment(target, request.form.get("item", ""), amount, "cash", g.viewer)
                flash("Cash payment recorded.", "ok")
                return redirect(url_for("pay.receipt", entry_id=entry.id))
            except PaymentError as exc:
                error = str(exc)
        flash(error, "error")
    today = today_nairobi()
    options = {m.id: available_items(m, today) for m in chama.members}
    return render_template("cash.html", options=options, members=chama.members)


def _match_and_record(payload):
    """Match an M-Pesa confirmation to a member by phone and record it. Returns (json, status)."""
    phone = normalize_phone(str(payload.get("phone", "")))
    amount = payload.get("amount")
    receipt_code = str(payload.get("receipt", ""))[:40]
    if not phone or not isinstance(amount, int) or amount <= 0 or not receipt_code:
        return {"result": "rejected", "reason": "phone, amount and receipt are required"}, 400
    if LedgerEntry.query.filter_by(ref=receipt_code).first():
        return {"result": "duplicate"}, 200
    member = Member.query.filter_by(phone=phone).first()
    if member is None:
        return {"result": "rejected", "reason": "no member with that phone number"}, 404
    today = today_nairobi()
    wanted = payload.get("account")
    options = {i["key"]: i for i in available_items(member, today)}
    if wanted not in options:   # default: monthly contribution when the amount matches, else savings
        due = options.get("contribution")
        wanted = "contribution" if due and due["amount"] == amount else "savings"
    try:
        entry = record_payment(member, wanted, amount, "mpesa", member, ref=receipt_code)
    except PaymentError as exc:
        return {"result": "rejected", "reason": str(exc)}, 422
    return {"result": "recorded", "entry_id": entry.id, "member": member.name, "type": wanted}, 200


@bp.post("/mpesa/webhook")
@csrf.exempt
def mpesa_webhook():
    sent = request.headers.get("X-Webhook-Secret", "")
    if not hmac.compare_digest(sent, current_app.config["MPESA_WEBHOOK_SECRET"]):
        return jsonify(result="unauthorized"), 401
    body, status = _match_and_record(request.get_json(silent=True) or {})
    return jsonify(body), status


@bp.route("/demo", methods=["GET", "POST"])
def demo():
    """Form that plays the part of Safaricom calling our webhook (demo only)."""
    outcome = None
    if request.method == "POST":
        payload = {"phone": request.form.get("phone", ""), "amount": to_int(request.form.get("amount"), lo=1),
                   "receipt": request.form.get("receipt", ""), "account": request.form.get("account") or None}
        outcome, _ = _match_and_record(payload)
    return render_template("demo.html", outcome=outcome, members=g.viewer.chama.members)
