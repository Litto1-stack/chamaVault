"""Vaulti coach: a local FAQ coach today, with a drop-in slot for a real LLM later."""
from flask import current_app

from .. import scoring
from .vaulti_faq import ADVICE_TRIGGERS, DISCLAIMER, FALLBACK, FAQ, NO_ADVICE

SYSTEM_PROMPT = (
    "You are Vaulti, a friendly money coach for Kenyan chama members. Answer in the user's language "
    "(English or Swahili) in under 120 words. Teach concepts; NEVER recommend specific investments, "
    "products, or providers, and never promise returns. Point to CMA/SASRA/CBK-licensed professionals "
    "for advice. Use the member context given to personalise encouragement."
)


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


class LocalFaqCoach(VaultiCoach):
    def reply(self, question, member, lang):
        lang = "sw" if lang == "sw" else "en"
        q = (question or "").lower()
        if any(t in q for t in ADVICE_TRIGGERS):
            body, topic = NO_ADVICE[lang], "no_advice"
        else:
            topic, best = None, 0
            for name, (keywords, *_) in FAQ.items():
                hits = sum(1 for k in keywords if k in q)
                if hits > best:
                    topic, best = name, hits
            body = FAQ[topic][1 if lang == "en" else 2] if topic else FALLBACK[lang]
        answer = f"{_personal_line(member, lang)}\n\n{body}\n\n{DISCLAIMER[lang]}"
        return {"answer": answer, "topic": topic}


class LlmCoach(VaultiCoach):
    """Placeholder for a real LLM. Fill in _call_api; until then it falls back to the local FAQ."""

    def __init__(self, fallback: VaultiCoach):
        self.fallback = fallback

    def build_messages(self, question, member, lang):
        context = f"Member: {member.first_name}. Score: {member.credit_score}. Streak: {member.streak}. Language: {lang}."
        return [{"role": "system", "content": SYSTEM_PROMPT + " " + context},
                {"role": "user", "content": question}]

    def _call_api(self, messages) -> str:
        raise NotImplementedError("Wire an LLM client here (e.g. the Anthropic SDK).")

    def reply(self, question, member, lang):
        try:
            text = self._call_api(self.build_messages(question, member, lang))
            return {"answer": f"{text}\n\n{DISCLAIMER['sw' if lang == 'sw' else 'en']}", "topic": "llm"}
        except NotImplementedError:
            return self.fallback.reply(question, member, lang)


def get_coach() -> VaultiCoach:
    return current_app.extensions["vaulti_coach"]
