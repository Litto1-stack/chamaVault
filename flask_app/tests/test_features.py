"""Tests for loan rules, merry-go-round, elections, invites, settings, charts and exports."""
import json
from unittest.mock import MagicMock, patch

import pytest

from app import charts, rotation
from app.elections import ElectionError, cast_vote, close_election, open_election
from app.extensions import db
from app.loans import LoanError, available_pool, cast_vote as loan_vote, loan_terms, officer_decide, request_loan
from app.models import Chama, Election, Invite, LedgerEntry, Loan, Member, RotationSlot, SmsLog
from app.payments import period_of, record_payment
from app.stats import chama_stats
from app.services.vaulti import LocalFaqCoach, OpenRouterCoach
from app.timeutil import today_nairobi


def member(name):
    return Member.query.filter_by(name=name).one()


def test_openrouter_uses_configured_chat_completions(app):
    response = MagicMock()
    response.__enter__.return_value.read.return_value = (
        b'{"choices":[{"message":{"content":"A simple budget starts with a plan."}}]}'
    )
    with app.app_context():
        app.config.update(
            OPENROUTER_API_KEY="test-key", OPENROUTER_BASE_URL="https://openrouter.ai/api/v1",
            OPENROUTER_MODEL="google/gemini-2.5-flash-lite",
        )
        with patch("app.services.vaulti.urllib.request.urlopen", return_value=response) as urlopen:
            answer = OpenRouterCoach(LocalFaqCoach())._call_api([{"role": "user", "content": "budget"}])
        request = urlopen.call_args.args[0]
        assert request.full_url == "https://openrouter.ai/api/v1/chat/completions"
        assert json.loads(request.data)["model"] == "google/gemini-2.5-flash-lite"
        assert request.get_header("Authorization") == "Bearer test-key"
        assert answer == "A simple budget starts with a plan."


def test_loan_terms_flat_and_reducing():
    assert loan_terms(10_000, 10, 4, "flat") == (11_000, 2750)
    total, pay = loan_terms(10_000, 2, 4, "reducing")
    assert pay == 2627 and total == pay * 4 < 11_000          # costs less than 10% flat
    assert loan_terms(1_000, 0, 2, "reducing") == (1_000, 500)


def test_guarantor_required_and_must_accept_before_votes(client, app):
    chama = Chama.query.first()
    chama.require_guarantor = True
    db.session.commit()
    wanjiku, fatuma = member("Wanjiku Kamau"), member("Fatuma Hassan")
    with pytest.raises(LoanError):
        request_loan(wanjiku, 2000, 2)                           # no guarantor
    with pytest.raises(LoanError):
        request_loan(wanjiku, 2000, 2, wanjiku.id)               # cannot guarantee yourself
    loan = request_loan(wanjiku, 2000, 2, fatuma.id)
    assert not loan.guarantor_ok
    with pytest.raises(LoanError):
        loan_vote(loan, member("Mary Njeri"), True)
    client.post("/viewer", data={"member_id": fatuma.id})
    client.post(f"/loans/{loan.id}/guarantee", data={"choice": "accept"})
    assert db.session.get(Loan, loan.id).guarantor_ok
    loan_vote(loan, member("Mary Njeri"), True)


def test_officer_mode_blocks_votes_and_treasurer_decides(app):
    chama = Chama.query.first()
    chama.loan_approval_mode = "officer"
    db.session.commit()
    loan = request_loan(member("Wanjiku Kamau"), 2000, 2)
    with pytest.raises(LoanError):
        loan_vote(loan, member("Fatuma Hassan"), True)
    officer_decide(loan, member("Mary Njeri"), True)
    assert loan.status == "approved"


def test_treasurer_cannot_approve_own_loan(app):
    Chama.query.first().loan_approval_mode = "officer"
    db.session.commit()
    mary = member("Mary Njeri")
    loan = request_loan(mary, 1000, 1)
    with pytest.raises(LoanError):
        officer_decide(loan, mary, True)


def test_rotation_pot_flow_and_loans_cannot_spend_it(client, app):
    chama = Chama.query.first()
    period = period_of(today_nairobi())
    status = rotation.pot_status(chama, period)
    assert status["recipient"].name == "Wanjiku Kamau" and len(status["paid"]) == 3 and not status["complete"]
    held_before = rotation.held(chama.id)
    assert held_before == 1500 and available_pool(chama.id) == LedgerEntry.query.order_by(LedgerEntry.id.desc()).first().running_balance - 1500
    with pytest.raises(rotation.RotationError):
        rotation.pay_out_pot(chama, member("Mary Njeri"), period)      # not everyone has paid
    for name in ("Grace Wambui", "Akinyi Odhiambo", "Achieng Otieno"):
        m = member(name)
        record_payment(m, "rotation", 500, "mpesa", m)
    entry = rotation.pay_out_pot(chama, member("Mary Njeri"), period)
    assert entry.amount == -3000 and entry.member.name == "Wanjiku Kamau"
    assert rotation.held(chama.id) == 0
    with pytest.raises(rotation.RotationError):
        rotation.pay_out_pot(chama, member("Mary Njeri"), period)      # only once per cycle


def test_rotation_page_and_payout_route(client):
    client.post("/viewer", data={"member_id": member("Mary Njeri").id})
    html = client.get("/rotation").get_data(as_text=True)
    assert "Wanjiku Kamau" in html and "receives now" in html


def test_election_secret_ballot_and_winner_becomes_treasurer(app):
    chama = Chama.query.first()
    fatuma, grace = member("Fatuma Hassan"), member("Grace Wambui")
    wanjiku, akinyi = member("Wanjiku Kamau"), member("Akinyi Odhiambo")
    with pytest.raises(ElectionError):
        open_election(chama, wanjiku, [akinyi.id, wanjiku.id])               # members can't open
    with pytest.raises(ElectionError):
        open_election(chama, fatuma, [akinyi.id, grace.id])                  # signatories can't stand
    e = open_election(chama, fatuma, [akinyi.id, wanjiku.id])
    cand = {c.member_id: c.id for c in e.candidates}
    with pytest.raises(ElectionError):
        close_election(e, fatuma)                                            # no votes yet
    cast_vote(e, member("Mary Njeri"), cand[akinyi.id])
    with pytest.raises(ElectionError):
        cast_vote(e, member("Mary Njeri"), cand[wanjiku.id])                 # one vote each
    cast_vote(e, wanjiku, cand[wanjiku.id])
    with pytest.raises(ElectionError):
        close_election(e, fatuma)                                            # tied 1-1
    cast_vote(e, fatuma, cand[akinyi.id])
    assert close_election(e, fatuma).name == "Akinyi Odhiambo"
    assert akinyi.role == "treasurer" and member("Mary Njeri").role == "member"
    assert [m.role for m in Member.query.filter_by(role="treasurer")] == ["treasurer"]


def test_invite_and_join_adds_member_to_group_and_rotation(client):
    mary = member("Mary Njeri")
    client.post("/viewer", data={"member_id": mary.id})
    client.post("/invite", data={"name": "Njoki Mwangi", "phone": "0722 111 222"})
    inv = Invite.query.one()
    assert inv.phone == "254722111222" and SmsLog.query.filter_by(kind="invite").count() == 1
    client.post("/invite", data={"name": "Dup", "phone": "0712000001"})           # existing member's number
    assert Invite.query.count() == 1
    assert client.post(f"/join/{inv.code}", data={"pin": "12", "pin_confirm": "12"}).status_code == 200
    assert client.post(f"/join/{inv.code}", data={"pin": "4821", "pin_confirm": "4821"}).status_code == 302
    njoki = member("Njoki Mwangi")
    assert njoki.role == "member" and RotationSlot.query.filter_by(member_id=njoki.id).count() == 1
    assert client.get(f"/join/{inv.code}").status_code == 404                    # single use


def test_settings_validate_and_apply(client):
    client.post("/viewer", data={"member_id": member("Mary Njeri").id})
    base = {"monthly_amount": "2000", "goal_amount": "60000", "due_day": "10", "penalty_per_day": "40",
            "loan_interest_type": "reducing", "loan_interest_pct": "2", "loan_approval_mode": "vote",
            "loan_approval_pct": "50", "rotation_amount": "500", "pin": "1234"}
    client.post("/settings", data={**base, "due_day": "40"})
    assert Chama.query.first().due_day != 40
    client.post("/settings", data={**base, "pin": "9999"})
    assert Chama.query.first().monthly_amount == 1500
    client.post("/settings", data=base)
    c = Chama.query.first()
    assert (c.monthly_amount, c.due_day, c.loan_interest_type, c.require_guarantor) == (2000, 10, "reducing", False)
    assert SmsLog.query.filter_by(kind="rules").count() == 6


def test_non_treasurer_cannot_open_settings_or_invite(client):
    client.post("/viewer", data={"member_id": member("Wanjiku Kamau").id})
    assert client.get("/settings").status_code == 403 and client.get("/invite").status_code == 403


def test_new_pages_render(client):
    for path in ["/elections", "/rotation", "/tools", "/goals", "/info/how-it-works", "/info/features", "/info/faq",
                 "/info/privacy", "/info/terms", "/sw.js", "/static/manifest.webmanifest", "/ledger.csv", "/loans"]:
        assert client.get(path).status_code == 200, path
    assert client.get("/info/nope").status_code == 404


def test_csv_export_neutralises_formulas(client, app):
    mary = member("Mary Njeri")
    entry = LedgerEntry.query.filter_by(type="contribution").first()
    from app.ledger import correct_entry
    correct_entry(entry.id, 1000, "=HYPERLINK(\"http://x\") bad reason", mary.id)
    db.session.commit()
    body = client.get("/ledger.csv").get_data(as_text=True)
    assert body.startswith("id,date_utc") and "'=HYPERLINK" in body and ",=HYPERLINK" not in body


def test_charts_and_stats(app):
    s = chama_stats(Chama.query.first(), today_nairobi())
    assert s["members"] == 6 and 0 <= s["on_time_pct"] <= 100 and len(s["months"]) == 6 and s["mix"][0][0] == "Contributions"
    assert "<svg" in charts.area_chart(s["balance_points"]) and "<svg" in charts.bar_chart(s["months"])
    assert "<svg" in charts.donut(s["mix"]) and "620" in charts.gauge(620, 300, 850) and "75%" in charts.ring(75)
    assert charts.area_chart([1]) == "" and charts.initials("Wanjiku Kamau") == "WK"


def test_dashboard_shows_visuals(client):
    html = client.get("/").get_data(as_text=True)
    for needle in ("Pool growth", "Collected vs expected", "Where the money came from", "Merry-go-round", "avatar", "On-time payments"):
        assert needle in html, needle
