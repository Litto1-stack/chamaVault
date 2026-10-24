"""Secret-ballot treasurer elections: signatories open and close, every member votes once."""
from collections import Counter

from .extensions import db
from .models import Ballot, Candidate, Election, ElectionVote, Member
from .services.sms import notify_all


class ElectionError(ValueError):
    """Raised for invalid election actions (message is safe to show the user)."""


def open_election(chama, opener, candidate_ids):
    if opener.role != "signatory":
        raise ElectionError("Only a signatory can open an election.")
    if Election.query.filter_by(chama_id=chama.id, status="open").first():
        raise ElectionError("An election is already open.")
    ids = sorted(set(candidate_ids))
    people = [db.session.get(Member, i) for i in ids]
    if not 2 <= len(people) <= 4 or any(p is None or p.chama_id != chama.id or p.role == "signatory" for p in people):
        raise ElectionError("Pick 2 to 4 candidates who are not signatories.")
    election = Election(chama_id=chama.id, role="treasurer")
    db.session.add(election)
    db.session.flush()
    db.session.add_all(Candidate(election_id=election.id, member_id=p.id) for p in people)
    notify_all(chama, "Treasurer election is open. Candidates: " + ", ".join(p.first_name for p in people) +
               ". Vote in ChamaVault > Elections.", "election")
    db.session.commit()
    return election


def cast_vote(election, voter, candidate_id):
    if election.status != "open":
        raise ElectionError("This election is closed.")
    if voter.chama_id != election.chama_id:
        raise ElectionError("You are not a member of this chama.")
    candidate = next((c for c in election.candidates if c.id == candidate_id), None)
    if candidate is None:
        raise ElectionError("Choose one of the candidates.")
    if Ballot.query.filter_by(election_id=election.id, voter_id=voter.id).first():
        raise ElectionError("You have already voted.")
    # Two separate rows: who voted, and what was voted. They are never linked.
    db.session.add(Ballot(election_id=election.id, voter_id=voter.id))
    db.session.add(ElectionVote(election_id=election.id, candidate_id=candidate.id))
    db.session.commit()


def turnout(election):
    return Ballot.query.filter_by(election_id=election.id).count()


def tally(election) -> list:
    counts = Counter(v.candidate_id for v in ElectionVote.query.filter_by(election_id=election.id))
    return sorted(((c, counts.get(c.id, 0)) for c in election.candidates), key=lambda x: -x[1])


def close_election(election, closer):
    if closer.role != "signatory":
        raise ElectionError("Only a signatory can close an election.")
    if election.status != "open":
        raise ElectionError("This election is already closed.")
    results = tally(election)
    if results[0][1] == 0:
        raise ElectionError("No votes have been cast yet.")
    if len(results) > 1 and results[0][1] == results[1][1]:
        raise ElectionError("The top candidates are tied. Wait for more votes before closing.")
    winner = results[0][0].member
    chama = winner.chama
    for m in chama.members:
        if m.role == "treasurer" and m.id != winner.id:
            m.role = "member"
    winner.role = "treasurer"
    election.status, election.winner_id = "closed", winner.id
    notify_all(chama, f"Election result: {winner.name} is the new treasurer with {results[0][1]} vote(s).", "election")
    db.session.commit()
    return winner
