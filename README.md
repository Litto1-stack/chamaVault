# ChamaVault

A focused, mobile-first chama ledger demo. It opens on the seeded **Umoja Sisters** dashboard.

## Run locally

```powershell
python -m http.server 8000
```

Open <http://localhost:8000>. No build step or package install is required.

This command runs the static demo only. To use accounts and the Flask-backed services, follow [flask_app/README.md](flask_app/README.md); the Flask configuration loads the workspace-root `.env` file.

## Main flow

- Review contribution status and the group total on the dashboard.
- Record a cash payment with demo PIN `1234`, or simulate an incoming M-Pesa payment from the SMS outbox.
- Open the ledger to see records and publish a correction with a written reason. The original stays visible, and the group and signatories receive simulated SMS alerts.
- Use **Invite a member** to join with code `482916` or create a chama. Chama creation uses demo OTP `2468`.
- Trigger a reminder and chat with Vaulti using the local English/Kiswahili FAQ.

- **Make a payment** page: choose what you're paying for, the amount auto-fills (locked for fixed items), pay by simulated M-Pesa (any 4-digit PIN) or demo card (format checks only, never stored), then get a receipt.
- **Ledger check**: records are hash-chained with SHA-256. Click the green badge on the Full ledger page to re-verify; a changed record turns it red and names the first broken one.
- **Loans & votes**: request, member vote (approval % from the chama rules), mock payout with the treasurer PIN, installments paid from the payment page.
- **Statement** (Members page): plain-language score rules, printable, with a verification code.

These extras live in `extras.js`, `chain.js` and `extras.css`. Hard refresh (Ctrl+Shift+R) once after updating.

Use the **?** menu to reset browser data to the seeded demo.

## Demo limits

The app stores data in this browser’s `localStorage`. SMS and M-Pesa are simulations; there is no payment processing, real SMS provider, shared backend, external AI, or tamper-proof server ledger. Do not enter real financial or personal data.
