"""End-to-end tests of pages, payments, SMS, fraud rules, loans and Vaulti."""
from app.extensions import db
from app.ledger import verify_chain
from app.models import Chama, FraudFlag, LedgerEntry, Loan, Member, SmsLog


def switch(client, name):
    member = Member.query.filter_by(name=name).one()
    client.post("/viewer", data={"member_id": member.id})
    return member


def test_home_is_dashboard_without_login(client):
    html = client.get("/").get_data(as_text=True)
    assert "Umoja Sisters" in html and "Make a payment" in html and "Overdue" in html


def test_every_page_renders(client):
    for path in ["/ledger", "/verify", "/pay", "/sms", "/reminders", "/loans", "/score", "/statement",
                 "/statement/check", "/vaulti", "/demo"]:
        assert client.get(path).status_code == 200, path


def test_mpesa_payment_updates_ledger_and_texts_everyone(client):
    achieng = switch(client, "Achieng Otieno")
    n_sms = SmsLog.query.count()
    r = client.post("/pay", data={"item": "contribution", "amount": "1500", "method": "mpesa", "mpesa_pin": "1234"})
    assert r.status_code == 302 and "/receipt/" in r.headers["Location"]
    assert SmsLog.query.count() == n_sms + 6
    assert "Achieng paid KES 1,500." in SmsLog.query.order_by(SmsLog.id.desc()).first().body
    assert verify_chain(achieng.chama_id)["ok"]


def test_wrong_mpesa_pin_records_nothing(client):
    switch(client, "Achieng Otieno")
    count = LedgerEntry.query.count()
    client.post("/pay", data={"item": "contribution", "amount": "1500", "method": "mpesa", "mpesa_pin": "0000"})
    assert LedgerEntry.query.count() == count


def test_fixed_amount_cannot_be_changed_and_card_rules_apply(client):
    switch(client, "Achieng Otieno")
    count = LedgerEntry.query.count()
    client.post("/pay", data={"item": "contribution", "amount": "10", "method": "mpesa", "mpesa_pin": "1234"})
    bad_card = {"item": "savings", "amount": "500", "method": "card", "card_name": "A B",
                "card_number": "1234", "card_expiry": "01/20", "card_cvv": "1"}
    client.post("/pay", data=bad_card)
    assert LedgerEntry.query.count() == count
    good = {**bad_card, "card_number": "4111 1111 1111 1111", "card_expiry": "12/45", "card_cvv": "123"}
    assert client.post("/pay", data=good).status_code == 302


def test_paid_contribution_is_not_offered_again(client):
    switch(client, "Wanjiku Kamau")
    html = client.get("/pay").get_data(as_text=True)
    assert "Monthly contribution" not in html and "Extra savings" in html


def test_webhook_matches_member_by_phone_and_rejects_bad_secret(client):
    body = {"phone": "0712 000 006", "amount": 1500, "receipt": "QTEST001"}
    assert client.post("/mpesa/webhook", json=body).status_code == 401
    ok = client.post("/mpesa/webhook", json=body, headers={"X-Webhook-Secret": "demo-secret"})
    assert ok.get_json()["member"] == "Achieng Otieno"
    again = client.post("/mpesa/webhook", json=body, headers={"X-Webhook-Secret": "demo-secret"})
    assert again.get_json()["result"] == "duplicate"


def test_treasurer_cash_for_self_alerts_signatories_quietly(client):
    mary = switch(client, "Mary Njeri")
    client.post("/cash", data={"member_id": mary.id, "item": "savings", "amount": "300", "pin": "1234"})
    assert FraudFlag.query.filter_by(rule="treasurer_cash_self").count() == 1
    to = {s.member.name for s in SmsLog.query.filter_by(kind="fraud_alert")}
    assert to == {"Fatuma Hassan", "Grace Wambui"}


def test_cash_needs_correct_pin(client):
    mary = switch(client, "Mary Njeri")
    count = LedgerEntry.query.count()
    client.post("/cash", data={"member_id": mary.id, "item": "savings", "amount": "300", "pin": "9999"})
    assert LedgerEntry.query.count() == count


def test_two_corrections_in_a_week_flag_and_everyone_is_texted(client):
    switch(client, "Mary Njeri")
    ids = [e.id for e in LedgerEntry.query.filter_by(type="contribution").limit(2)]
    for i in ids:
        client.post(f"/ledger/{i}/correct", data={"new_amount": "1000", "reason": "Typed the wrong amount", "pin": "1234"})
    assert FraudFlag.query.filter_by(rule="correction_burst").count() == 1
    assert SmsLog.query.filter_by(kind="correction").count() == 12
    assert "CORRECTED" in client.get("/ledger").get_data(as_text=True)


def test_non_treasurer_cannot_correct_or_record_cash(client):
    switch(client, "Wanjiku Kamau")
    assert client.get("/ledger/1/correct").status_code == 403
    assert client.get("/cash").status_code == 403


def test_loan_vote_flow_and_large_payout_flag(client, app):
    wanjiku = switch(client, "Wanjiku Kamau")
    client.post("/loans/request", data={"amount": "2000", "installments": "2"})
    loan = Loan.query.filter_by(member_id=wanjiku.id).one()
    for name in ("Mary Njeri", "Fatuma Hassan", "Grace Wambui"):
        switch(client, name)
        client.post(f"/loans/{loan.id}/vote", data={"choice": "approve"})
    assert db.session.get(Loan, loan.id).status == "approved"
    switch(client, "Mary Njeri")
    client.post(f"/loans/{loan.id}/payout", data={"pin": "1234"})
    assert db.session.get(Loan, loan.id).status == "active"


def test_borrower_cannot_vote_on_own_loan(client):
    akinyi = switch(client, "Wanjiku Kamau")
    client.post("/loans/request", data={"amount": "1000", "installments": "1"})
    loan = Loan.query.filter_by(member_id=akinyi.id).one()
    client.post(f"/loans/{loan.id}/vote", data={"choice": "approve"})
    assert len(loan.votes) == 0


def test_vaulti_speaks_both_languages_and_refuses_investment_picks(client):
    switch(client, "Wanjiku Kamau")
    en = client.post("/vaulti", data={"question": "What is a money market fund?", "lang": "en"},
                     headers={"Accept": "application/json"}).get_json()["answer"]
    sw = client.post("/vaulti", data={"question": "Niambie kuhusu ulaghai wa M-Pesa", "lang": "sw"},
                     headers={"Accept": "application/json"}).get_json()["answer"]
    adv = client.post("/vaulti", data={"question": "Which stock should I buy?", "lang": "en"},
                      headers={"Accept": "application/json"}).get_json()
    assert "Wanjiku" in en and "CMA" in en and "Habari Wanjiku" in sw and "PIN" in sw
    assert adv["topic"] == "no_advice"


def test_reminder_trigger_targets(client):
    switch(client, "Mary Njeri")
    client.post("/reminders/trigger", data={"kind": "day_before"})
    assert SmsLog.query.filter_by(kind="reminder").count() == 6
    client.post("/reminders/trigger", data={"kind": "due_morning"})
    assert SmsLog.query.filter_by(kind="reminder").count() == 7   # only Achieng is unpaid


def test_statement_code_detects_ledger_changes(client):
    switch(client, "Wanjiku Kamau")
    html = client.get("/statement").get_data(as_text=True)
    code = html.split("CV-")[1].split("<")[0].strip()
    member = Member.query.filter_by(name="Wanjiku Kamau").one()
    ok = client.post("/statement/check", data={"member_id": member.id, "code": "CV-" + code}).get_data(as_text=True)
    bad = client.post("/statement/check", data={"member_id": member.id, "code": "CV-0000-0000-0000"}).get_data(as_text=True)
    assert "Genuine" in ok and "No match" in bad

