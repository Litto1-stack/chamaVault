"""Loan pages: request, vote, and treasurer payout."""
from flask import Blueprint, flash, g, redirect, render_template, request, url_for

from ..auth import check_pin, role_required
from ..extensions import db
from ..forms import to_int
from ..loans import (LoanError, answer_guarantee, available_pool, cast_vote, loan_terms, next_due, officer_decide, payout,
                     request_loan, vote_summary)
from ..models import Loan

bp = Blueprint("loans", __name__)


@bp.route("/loans")
def loans():
    chama = g.viewer.chama
    rows = Loan.query.filter_by(chama_id=chama.id).order_by(Loan.id.desc()).all()
    cards = [{"loan": l, "votes": vote_summary(l),
              "voted": any(v.member_id == g.viewer.id for v in l.votes),
              "due": next_due(l) if l.status == "active" else None} for l in rows]
    return render_template("loans.html", cards=cards, pool=available_pool(chama.id),
                           others=[m for m in chama.members if m.id != g.viewer.id])


@bp.post("/loans/request")
def request_():
    try:
        request_loan(g.viewer, to_int(request.form.get("amount")), to_int(request.form.get("installments")),
                     to_int(request.form.get("guarantor_id"), lo=1))
        flash("Loan request sent. Members will now vote.", "ok")
    except LoanError as exc:
        flash(str(exc), "error")
    return redirect(url_for("loans.loans"))


@bp.post("/loans/<int:loan_id>/vote")
def vote(loan_id):
    loan = db.get_or_404(Loan, loan_id)
    choice = request.form.get("choice")
    try:
        if choice not in ("approve", "reject"):
            raise LoanError("Choose approve or reject.")
        cast_vote(loan, g.viewer, choice == "approve")
        flash("Your vote was recorded.", "ok")
    except LoanError as exc:
        flash(str(exc), "error")
    return redirect(url_for("loans.loans"))


@bp.post("/loans/<int:loan_id>/payout")
@role_required("treasurer")
def pay_out(loan_id):
    loan = db.get_or_404(Loan, loan_id)
    error = check_pin(g.viewer, request.form.get("pin"))
    if error is None:
        try:
            payout(loan, g.viewer)
            flash("Payout sent (mock M-Pesa) and recorded in the ledger.", "ok")
            return redirect(url_for("loans.loans"))
        except LoanError as exc:
            error = str(exc)
    flash(error, "error")
    return redirect(url_for("loans.loans"))


@bp.post("/loans/<int:loan_id>/guarantee")
def guarantee(loan_id):
    loan = db.get_or_404(Loan, loan_id)
    try:
        accept = request.form.get("choice") == "accept"
        answer_guarantee(loan, g.viewer, accept)
        flash("You agreed to guarantee this loan." if accept else "You declined to guarantee this loan.", "ok")
    except LoanError as exc:
        flash(str(exc), "error")
    return redirect(url_for("loans.loans"))


@bp.post("/loans/<int:loan_id>/decide")
@role_required("treasurer")
def decide(loan_id):
    loan = db.get_or_404(Loan, loan_id)
    try:
        officer_decide(loan, g.viewer, request.form.get("choice") == "approve")
        flash("Decision recorded and everyone notified.", "ok")
    except LoanError as exc:
        flash(str(exc), "error")
    return redirect(url_for("loans.loans"))

