# ChamaVault (Flask)

*M-Pesa moves the money. ChamaVault proves it.* A demo web app for Kenyan chamas. No real payments or SMS.

## Run

```powershell
cd flask_app
python -m venv .venv
.\.venv\Scripts\pip install -r requirements.txt
.\.venv\Scripts\python seed.py     # creates "Umoja Sisters" demo data (PIN for everyone: 1234)
.\.venv\Scripts\python run.py      # http://127.0.0.1:5000
.\.venv\Scripts\python -m pytest   # 42 tests
```

The public landing page is `/`; create an account to create a chama, or sign in with a seeded demo account such as `demo+0001@chamavault.local` / `Demo1234` (transaction PIN `1234`). Set `API_KEY` in the workspace-root `.env` to enable Vaulti through OpenRouter. `BASE_URL` defaults to OpenRouter's API and `MODEL` defaults to `google/gemini-2.5-flash-lite`; Vaulti falls back to the local FAQ if the provider is unavailable.

## Try it (use the "Viewing as" dropdown)

| Try | As | Where |
|---|---|---|
| See pool, goal, Paid/Pending/Overdue and penalty per day | anyone | Home |
| Pay contribution via M-Pesa (PIN 1234) or Card (any 13-19 digits, future expiry, 3-4 digit CVV) | Achieng (overdue) | Make a payment → receipt |
| Record cash with PIN; cash for the treasurer herself quietly alerts signatories | Mary (treasurer) | Record cash → then Alerts as Fatuma |
| Correct an entry (reason required), original shows CORRECTED, all members get SMS; 2 in a week flags | Mary | Ledger → Request correction |
| Tamper test: change an amount in SQLite, then open Verify | any | Verify |
| M-Pesa webhook matched by phone | any | M-Pesa demo (or `POST /mpesa/webhook` with header `X-Webhook-Secret: demo-secret`) |
| Reminders "Trigger now" | Mary | Reminders, then SMS |
| Request loan, vote, pay out, pay installments | Wanjiku / others / Mary | Loans |
| Score explanation, printable statement + code | any | My score → View my statement |
| Vaulti coach in English and Kiswahili | any | Vaulti |
| Dashboard charts: pool growth, collected vs expected, money mix, stat tiles, avatars | any | Home |
| Score gauge | any | My score |
| Merry-go-round: pay into the pot, then pay it out once all 6 have paid | Achieng/Akinyi/Grace to pay, Mary to pay out | Merry-go-round |
| Change loan rules (flat or reducing, guarantor, treasurer vs vote approval, pot size) | Mary | Rules |
| Guarantor flow: request a loan after turning guarantor on, then accept as the guarantor | Wanjiku, then the guarantor | Loans |
| Secret-ballot treasurer election | Fatuma opens, everyone votes, Fatuma closes | Elections |
| Invite a member by phone; open the link from the SMS outbox | Mary | Invite, SMS, then /join/CODE |
| Loan, savings and share-out calculators | any | Calculators |
| Install the app / use offline; export the ledger | any | Browser "Install", footer "Export ledger (CSV)" |

## Files

- `config.py` settings · `run.py` dev server · `seed.py` demo data · `conftest.py` test fixtures
- `app/__init__.py` app factory · `extensions.py` db + CSRF · `models.py` tables · `timeutil.py` Nairobi time and KES
- `ledger.py` hash chain, verify, corrections · `payments.py` dues, penalties, recording · `scoring.py` score rules
- `loans.py` loan lifecycle · `fraud.py` anomaly rules · `reminders.py` APScheduler jobs · `auth.py` viewer, roles, PIN check · `forms.py` input parsing
- `stats.py` dashboard numbers from the ledger · `charts.py` hand-built SVG charts (no libraries)
- `rotation.py` merry-go-round · `elections.py` secret-ballot elections · `members.py` rules and invites
- `services/sms.py`, `mpesa.py`, `card.py` mock services behind interfaces · `services/vaulti.py` + `vaulti_faq.py` coach and FAQ
- `routes/` one blueprint per area · `templates/` Jinja pages · `static/` CSS and JS

## Vaulti literacy (Adaption + Together) · voice · email

1. Copy `.env.example` keys into your environment (or export them).
2. Build training data: `python literacy/scripts/build_dataset.py`
3. Train on Adaption: `ADAPTION_API_KEY=… python literacy/scripts/train_adaption.py`  
   Default model `openai/gpt-oss-20b`; promote with `--model Qwen/Qwen3.6-35B-A3B`.
4. Host the LoRA on Together AI; set `TOGETHER_API_KEY`, `VAULTI_MODEL_ID`, `VAULTI_BACKEND=llm`.
5. Optional: `COGNARIA_API_KEY` for Kenyan TTS on Vaulti; `RESEND_API_KEY` + `EMAIL_FROM` for invites/reminders/goal digests.

Vaulti teaches literacy (EN/SW), grounds answers with `literacy/docs/`, and refuses guaranteed-return / pick-a-stock advice.

## Swapping in real services later

Set the service in `app/__init__.py`: implement `SmsService.send` (Africa's Talking), `MpesaService.stk_push/complete` (Daraja). LLM path is already wired via Together when `VAULTI_BACKEND=llm`.

## Notes

- The seed sets the contribution due day to 3 days before the day you seed, so one member is always visibly overdue.
- Security: CSRF on all forms, PINs hashed and never logged (5 wrong tries lock PIN actions for the session), card data never stored.
- Inspired by chama.ke's feature set (two savings models, loan rules, elections, invites, installable app), built in this app's own design and stack.
- Reseed after pulling these changes (`python seed.py`): the database schema grew.
- Scheduler runs inside the dev server; set `SCHEDULER_ENABLED=0` to disable.
