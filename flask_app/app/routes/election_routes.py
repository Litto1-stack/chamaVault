"""Election pages: see candidates, vote in secret, and (signatories) open or close the poll."""
from flask import Blueprint, flash, g, redirect, render_template, request, url_for

from ..auth import role_required
from ..elections import ElectionError, cast_vote, close_election, open_election, tally, turnout
from ..extensions import db
from ..forms import to_int
from ..models import Ballot, Election

bp = Blueprint("elections", __name__)


@bp.route("/elections")
def elections():
    chama = g.viewer.chama
    rows = Election.query.filter_by(chama_id=chama.id).order_by(Election.id.desc()).all()
    cards = [{"e": e, "turnout": turnout(e), "results": tally(e) if e.status == "closed" else None,
              "voted": Ballot.query.filter_by(election_id=e.id, voter_id=g.viewer.id).first() is not None} for e in rows]
    eligible = [m for m in chama.members if m.role != "signatory"]
    return render_template("elections.html", cards=cards, eligible=eligible,
                           has_open=any(c["e"].status == "open" for c in cards))


@bp.post("/elections/open")
@role_required("signatory")
def open_():
    ids = [to_int(v, lo=1) for v in request.form.getlist("candidates")]
    try:
        open_election(g.viewer.chama, g.viewer, [i for i in ids if i])
        flash("Election opened. Everyone has been notified.", "ok")
    except ElectionError as exc:
        flash(str(exc), "error")
    return redirect(url_for("elections.elections"))


@bp.post("/elections/<int:election_id>/vote")
def vote(election_id):
    election = db.get_or_404(Election, election_id)
    if election.chama_id != g.viewer.chama_id:
        from flask import abort
        abort(404)
    try:
        cast_vote(election, g.viewer, to_int(request.form.get("candidate"), lo=1) or 0)
        flash("Your secret vote was counted.", "ok")
    except ElectionError as exc:
        flash(str(exc), "error")
    return redirect(url_for("elections.elections"))


@bp.post("/elections/<int:election_id>/close")
@role_required("signatory")
def close(election_id):
    election = db.get_or_404(Election, election_id)
    if election.chama_id != g.viewer.chama_id:
        from flask import abort
        abort(404)
    try:
        winner = close_election(election, g.viewer)
        flash(f"{winner.name} is the new treasurer.", "ok")
    except ElectionError as exc:
        flash(str(exc), "error")
    return redirect(url_for("elections.elections"))
