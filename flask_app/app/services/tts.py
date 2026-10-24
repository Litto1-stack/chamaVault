"""Kenyan text-to-speech via Cognaria (en-KE / sw-KE)."""
from __future__ import annotations

import json
import os
import urllib.error
import urllib.request

from flask import current_app

# Default Cognaria-style Kenyan voice ids (override with COGNARIA_VOICE_EN / _SW).
DEFAULT_VOICE_EN = "kenya_female_1"
DEFAULT_VOICE_SW = "zuri_ke"


class TtsError(RuntimeError):
    pass


def _config(key, default=""):
    if current_app:
        return current_app.config.get(key) or os.environ.get(key, default)
    return os.environ.get(key, default)


def synthesize(text: str, lang: str = "en") -> dict:
    """Return {"audio_url": str, "duration": float|None} or raise TtsError.

    When COGNARIA_API_KEY is missing, returns a mock payload so the UI can still demo.
    """
    text = (text or "").strip()
    if not text:
        raise TtsError("Nothing to speak.")
    # Cap length for cost / latency
    text = text[:2500]
    lang = "sw" if lang == "sw" else "en"
    api_key = _config("COGNARIA_API_KEY")
    voice = _config("COGNARIA_VOICE_SW", DEFAULT_VOICE_SW) if lang == "sw" else _config(
        "COGNARIA_VOICE_EN", DEFAULT_VOICE_EN
    )
    language = "sw-KE" if lang == "sw" else "en-KE"

    if not api_key:
        # Demo stub: data-URI silent-ish placeholder signal for UI wiring
        return {
            "audio_url": None,
            "duration": None,
            "voice": voice,
            "language": language,
            "mock": True,
            "text_preview": text[:120],
            "message": "Add COGNARIA_API_KEY to enable Kenyan voice playback.",
        }

    base = _config("COGNARIA_API_BASE", "https://api.cognariai.com").rstrip("/")
    payload = {
        "text": text,
        "voice": voice,
        "language": language,
        "format": "mp3",
        "emotion": "warm",
    }
    req = urllib.request.Request(
        f"{base}/v1/text-to-speech",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "User-Agent": "ChamaVault/1.0",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")[:200]
        raise TtsError(f"Cognaria HTTP {exc.code}: {body}") from exc
    except urllib.error.URLError as exc:
        raise TtsError(f"Cognaria unreachable: {exc}") from exc

    url = data.get("audio_url") or data.get("url")
    if not url:
        raise TtsError("Cognaria response missing audio_url")
    return {
        "audio_url": url,
        "duration": data.get("duration"),
        "voice": voice,
        "language": language,
        "mock": False,
    }
