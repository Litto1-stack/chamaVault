"""Vaulti literacy, goals planner, TTS stub, and advice refusal."""
from datetime import date

from app.goals import plan_goal
from app.models import Member, PersonalGoal
from app.services.literacy_rag import retrieve
from seed import DEMO_PIN


def switch(client, name):
    member = Member.query.filter_by(name=name).one()
    client.post("/viewer", data={"member_id": member.id})
    return member


def test_vaulti_refuses_guaranteed_returns_and_stock_picks(client):
    switch(client, "Wanjiku Kamau")
    adv = client.post(
        "/vaulti",
        data={"question": "Which stock should I buy?", "lang": "en"},
        headers={"Accept": "application/json"},
    ).get_json()
    assert adv["topic"] == "no_advice"
    assert "CMA" in adv["answer"] or "licensed" in adv["answer"].lower()

    g50 = client.post(
        "/vaulti",
        data={"question": "Can you guarantee me 50% return?", "lang": "en"},
        headers={"Accept": "application/json"},
    ).get_json()
    assert g50["topic"] == "no_advice"


def test_vaulti_explains_ipo_without_buy_recommendation(client):
    switch(client, "Wanjiku Kamau")
    data = client.post(
        "/vaulti",
        data={"question": "Dangote is selling shares — is that a good investment?", "lang": "en"},
        headers={"Accept": "application/json"},
    ).get_json()
    # Local FAQ explainer or no_advice; never urge a purchase
    assert data["topic"] in ("literacy_explainer", "no_advice", "llm")
    low = data["answer"].lower()
    assert "should buy" not in low and "buy dangote" not in low
    assert "cma" in low or "licence" in low or "license" in low or "education" in low


def test_goal_planner_math():
    plan = plan_goal(30_000, 0, 5_000, date(2027, 4, 24), today=date(2026, 10, 24))
    assert plan["remaining"] == 30_000
    assert plan["months_needed"] == 6
    assert plan["suggested_pledge"] >= 1
    assert plan["pct"] == 0

    behind = plan_goal(30_000, 0, 1_000, date(2026, 12, 24), today=date(2026, 10, 24))
    assert behind["on_track"] is False
    assert behind["suggested_pledge"] > 1_000


def test_personal_goals_crud(client, app):
    switch(client, "Wanjiku Kamau")
    assert client.get("/goals").status_code == 200
    # Seed already has School fees for Wanjiku
    assert PersonalGoal.query.filter_by(name="School fees").count() == 1

    client.post("/goals", data={
        "action": "create",
        "name": "Laptop",
        "target_kes": "40000",
        "saved_kes": "5000",
        "monthly_pledge": "5000",
        "target_date": "2027-06-01",
    })
    goal = PersonalGoal.query.filter_by(name="Laptop").one()
    assert goal.saved_kes == 5000

    client.post("/goals", data={"action": "progress", "goal_id": str(goal.id), "amount": "2000"})
    assert goal.saved_kes == 7000

    plan = client.get("/goals/plan?target=10000&saved=2000&pledge=2000").get_json()
    assert plan["remaining"] == 8000 and plan["months_needed"] == 4


def test_tts_mock_without_cognaria_key(client):
    switch(client, "Wanjiku Kamau")
    res = client.post(
        "/vaulti/speak",
        data={"text": "Habari, hii ni Vaulti.", "lang": "sw"},
        headers={"Accept": "application/json"},
    )
    assert res.status_code == 200
    data = res.get_json()
    assert data.get("mock") is True
    assert "COGNARIA" in (data.get("message") or "")


def test_rag_retrieves_ipo_doc():
    snippets = retrieve("Is the Dangote share offer on the NSE a good IPO?")
    assert snippets and "prospectus" in snippets[0].lower()


def test_goal_digest_email_mock(client):
    switch(client, "Wanjiku Kamau")
    client.post("/goals", data={
        "action": "email_digest",
        "email": "wanjiku@example.com",
    })
    # Mock Resend still flashes ok
    html = client.get("/goals").get_data(as_text=True)
    assert "School fees" in html
