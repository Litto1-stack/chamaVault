"""Vaulti coach: local FAQ, Together AI LLM (Adaption fine-tune), RAG grounding."""
from __future__ import annotations

import json
import os
import urllib.error
import urllib.request

from flask import current_app

from .. import scoring
from .literacy_rag import build_context
from .vaulti_faq import ADVICE_TRIGGERS, DISCLAIMER, FALLBACK, FAQ, NO_ADVICE

SYSTEM_PROMPT = (
    "You are Vaulti, a friendly money coach for Kenyan chama members. Answer in the user's language "
    "(English or Swahili) in under 160 words. Teach concepts using Kenyan context (KES, M-Pesa, CMA, "
    "SASRA, CBK, NSE, SACCOs). NEVER recommend specific investments, products, or providers, and never "
    "promise returns or say 'you should buy X'. When asked about a share offer or IPO, explain how they "
    "work, risks, time horizon, and how to verify licences — do not say whether to buy. "
    "Point to CMA/SASRA/CBK-licensed professionals for personal advice. "
    "If grounding notes are provided, use them; do not invent live prices. "
    "Use the member context to personalise encouragement. End without repeating the disclaimer "
    "(the app appends it)."
)

# Hard refusals: guaranteed returns / explicit pick-for-me with no educational framing allowed.
HARD_REFUSAL = [
    "guaranteed return", "guarantee me", "50% return", "buy bitcoin",
    "which stock should i buy", "hisa gani", "nifanye uwekezaji gani",
]


class VaultiCoach:
    def reply(self, question: str, member, lang: str) -> dict:
        """Return {"answer": str, "topic": str|None}."""
        raise NotImplementedError


def _personal_line(member, lang):
    s, streak = member.credit_score, member.streak
    if lang == "sw":
        tip = ("Lipa mapema mwezi huu ili kuanza msururu mpya." if streak == 0 else
               f"Una msururu wa malipo {streak}. Endelea hivyo!" if streak < 3 else
               f"Una msururu mzuri wa malipo {streak}. Hongera!")
        return f"Habari {member.first_name}. Alama yako ni {s} ({scoring.band(s)}). {tip}"
    tip = ("Pay early this month to start a new streak." if streak == 0 else
           f"You're on a {streak}-payment streak. Keep it going!" if streak < 3 else
           f"Great {streak}-payment streak, well done!")
    return f"Hi {member.first_name}. Your score is {s} ({scoring.band(s)}). {tip}"


def _goals_line(member, lang) -> str:
    try:
        from ..models import PersonalGoal
        goals = PersonalGoal.query.filter_by(member_id=member.id).limit(3).all()
    except Exception:
        return ""
    if not goals:
        return ""
    if lang == "sw":
        bits = [f"{g.name}: {g.saved_kes}/{g.target_kes} KES" for g in goals]
        return "Malengo yako: " + "; ".join(bits)
    bits = [f"{g.name}: KES {g.saved_kes:,} / {g.target_kes:,}" for g in goals]
    return "Your goals: " + "; ".join(bits)


def _is_hard_refusal(question: str) -> bool:
    q = (question or "").lower()
    return any(t in q for t in HARD_REFUSAL)


def _is_advice_shaped(question: str) -> bool:
    q = (question or "").lower()
    return any(t in q for t in ADVICE_TRIGGERS)


class LocalFaqCoach(VaultiCoach):
    def reply(self, question, member, lang):
        lang = "sw" if lang == "sw" else "en"
        q = (question or "").lower()
        if _is_hard_refusal(question):
            body, topic = NO_ADVICE[lang], "no_advice"
        elif _is_advice_shaped(question):
            # Educational explainer path: still refuse a personal pick, but teach frameworks.
            body, topic = self._explainer(q, lang), "literacy_explainer"
        else:
            topic, best = None, 0
            for name, (keywords, *_) in FAQ.items():
                hits = sum(1 for k in keywords if k in q)
                if hits > best:
                    topic, best = name, hits
            body = FAQ[topic][1 if lang == "en" else 2] if topic else FALLBACK[lang]
        answer = f"{_personal_line(member, lang)}\n\n{body}\n\n{DISCLAIMER[lang]}"
        return {"answer": answer, "topic": topic}

    def _explainer(self, q: str, lang: str) -> str:
        from .literacy_rag import retrieve
        snippets = retrieve(q, limit=1)
        if lang == "sw":
            base = (
                "Siwezi kukushauri ununue uwekezaji maalum. Hilo linahitaji mshauri mwenye leseni ya CMA. "
                "Ninaweza kufundisha: elewa hatari, muda, leseni, na usiweke pesa za dharura sokoni. "
                "Uliza kuhusu IPO, MMF, SACCO au malengo ya akiba nitaeleza misingi."
            )
        else:
            base = (
                "I can't recommend a specific investment for you — that needs a CMA-licensed adviser. "
                "I can teach: understand risk, time horizon, licences, and never invest emergency money. "
                "Ask about IPOs, MMFs, SACCOs, or savings goals and I'll explain the basics."
            )
        if snippets:
            # Keep short: first paragraph of grounding
            tip = snippets[0].strip().split("\n\n")[0][:400]
            return f"{base}\n\n{tip}"
        return base


class LlmCoach(VaultiCoach):
    """Together AI chat completions; falls back to local FAQ on any failure."""

    def __init__(self, fallback: VaultiCoach):
        self.fallback = fallback

    def build_messages(self, question, member, lang):
        goals = _goals_line(member, lang)
        context = (
            f"Member: {member.first_name}. Score: {member.credit_score}. "
            f"Streak: {member.streak}. Language: {lang}."
        )
        if goals:
            context += " " + goals
        grounding = build_context(question)
        system = SYSTEM_PROMPT + " " + context
        if grounding:
            system += "\n\n" + grounding
        return [
            {"role": "system", "content": system},
            {"role": "user", "content": question},
        ]

    def _call_api(self, messages) -> str:
        api_key = current_app.config.get("TOGETHER_API_KEY") or os.environ.get("TOGETHER_API_KEY")
        model = current_app.config.get("VAULTI_MODEL_ID") or os.environ.get("VAULTI_MODEL_ID")
        if not api_key or not model:
            raise RuntimeError("TOGETHER_API_KEY or VAULTI_MODEL_ID not configured")

        payload = {
            "model": model,
            "messages": messages,
            "max_tokens": 350,
            "temperature": 0.4,
        }
        req = urllib.request.Request(
            "https://api.together.xyz/v1/chat/completions",
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                "User-Agent": "ChamaVault/1.0",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=45) as resp:
                data = json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")[:200]
            raise RuntimeError(f"Together HTTP {exc.code}: {body}") from exc
        except urllib.error.URLError as exc:
            raise RuntimeError(f"Together unreachable: {exc}") from exc

        try:
            return data["choices"][0]["message"]["content"].strip()
        except (KeyError, IndexError, TypeError, AttributeError) as exc:
            raise RuntimeError("Unexpected Together response shape") from exc

    def reply(self, question, member, lang):
        lang = "sw" if lang == "sw" else "en"
        if _is_hard_refusal(question):
            return {
                "answer": f"{_personal_line(member, lang)}\n\n{NO_ADVICE[lang]}\n\n{DISCLAIMER[lang]}",
                "topic": "no_advice",
            }
        try:
            text = self._call_api(self.build_messages(question, member, lang))
            return {
                "answer": f"{_personal_line(member, lang)}\n\n{text}\n\n{DISCLAIMER[lang]}",
                "topic": "llm",
            }
        except Exception:
            return self.fallback.reply(question, member, lang)


def get_coach() -> VaultiCoach:
    return current_app.extensions["vaulti_coach"]
