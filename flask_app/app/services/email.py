"""Transactional email via Resend. No-ops cleanly when RESEND_API_KEY is unset."""
from __future__ import annotations

import json
import logging
import os
import urllib.error
import urllib.request

from flask import current_app

log = logging.getLogger(__name__)


def _cfg(key, default=""):
    if current_app:
        return current_app.config.get(key) or os.environ.get(key, default)
    return os.environ.get(key, default)


def send_email(to: str, subject: str, html: str, text: str | None = None) -> dict:
    """Send one email. Returns {"ok": bool, "id": str|None, "mock": bool, "error": str|None}."""
    to = (to or "").strip()
    if not to or "@" not in to:
        return {"ok": False, "id": None, "mock": False, "error": "Invalid email address"}

    api_key = _cfg("RESEND_API_KEY")
    from_addr = _cfg("EMAIL_FROM", "ChamaVault <onboarding@resend.dev>")
    if not api_key:
        log.info("Resend mock: to=%s subject=%s", to, subject)
        return {"ok": True, "id": "mock", "mock": True, "error": None}

    payload = {
        "from": from_addr,
        "to": [to],
        "subject": subject,
        "html": html,
    }
    if text:
        payload["text"] = text

    req = urllib.request.Request(
        "https://api.resend.com/emails",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "User-Agent": "ChamaVault/1.0",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        return {"ok": True, "id": data.get("id"), "mock": False, "error": None}
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")[:300]
        log.warning("Resend HTTP %s: %s", exc.code, body)
        return {"ok": False, "id": None, "mock": False, "error": f"HTTP {exc.code}"}
    except urllib.error.URLError as exc:
        log.warning("Resend unreachable: %s", exc)
        return {"ok": False, "id": None, "mock": False, "error": str(exc)}


def invite_email(to: str, name: str, chama_name: str, join_url: str) -> dict:
    first = name.split()[0] if name else "there"
    subject = f"You're invited to {chama_name} on ChamaVault"
    html = (
        f"<p>Hi {first},</p>"
        f"<p>You are invited to join <strong>{chama_name}</strong> on ChamaVault.</p>"
        f"<p><a href=\"{join_url}\">Accept invite</a></p>"
        f"<p>Education and group ledger tools only — not financial advice.</p>"
    )
    return send_email(to, subject, html, text=f"Hi {first}, join {chama_name}: {join_url}")


def reminder_email(to: str, chama_name: str, body: str) -> dict:
    subject = f"{chama_name}: contribution reminder"
    html = f"<p>{body}</p><p style=\"color:#666;font-size:12px\">ChamaVault reminder</p>"
    return send_email(to, subject, html, text=body)


def goal_digest_email(to: str, first_name: str, lines: list[str]) -> dict:
    subject = "Your ChamaVault savings goals"
    items = "".join(f"<li>{line}</li>" for line in lines)
    html = (
        f"<p>Hi {first_name},</p>"
        f"<p>Goal progress:</p><ul>{items}</ul>"
        f"<p style=\"color:#666;font-size:12px\">Education only, not financial advice.</p>"
    )
    return send_email(to, subject, html, text="\n".join(lines))
