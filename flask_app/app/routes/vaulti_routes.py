"""Vaulti coach page; answers as JSON for the chat box or as a normal page without JavaScript."""
from flask import Blueprint, g, jsonify, render_template, request, session

from ..services.tts import TtsError, synthesize
from ..services.vaulti import get_coach
from ..services.vaulti_faq import FAQ

bp = Blueprint("vaulti", __name__)
SUGGESTIONS = {
    "en": [
        "How do I improve my score?",
        "How do I avoid M-Pesa scams?",
        "What is a money market fund?",
        "Dangote is selling shares — how do IPOs work?",
        "Can I save KES 30,000 in 6 months?",
    ],
    "sw": [
        "Nitaboreshaje alama yangu?",
        "Nijikinge vipi na ulaghai wa M-Pesa?",
        "SACCO ni nini?",
        "IPO au ofa ya hisa ni nini?",
        "Naweza kuweka akiba KES 30,000 kwa miezi 6?",
    ],
}


@bp.route("/vaulti", methods=["GET", "POST"])
def vaulti():
    lang = request.values.get("lang") or session.get("lang", "en")
    lang = lang if lang in ("en", "sw") else "en"
    session["lang"] = lang
    question = (request.form.get("question") or "").strip()[:300]
    answer = None
    if request.method == "POST":
        if not question:
            answer = {"answer": "Please type a question." if lang == "en" else "Tafadhali andika swali.", "topic": None}
        else:
            answer = get_coach().reply(question, g.viewer, lang)
        if request.accept_mimetypes.best == "application/json":
            return jsonify(answer)
    return render_template(
        "vaulti.html", lang=lang, question=question, answer=answer,
        suggestions=SUGGESTIONS[lang], topic_count=len(FAQ),
    )


@bp.post("/vaulti/speak")
def speak():
    """Synthesize Kenyan TTS for a Vaulti answer (Cognaria)."""
    lang = request.form.get("lang") or session.get("lang", "en")
    lang = "sw" if lang == "sw" else "en"
    text = (request.form.get("text") or "").strip()
    if not text:
        return jsonify(error="No text"), 400
    try:
        result = synthesize(text, lang=lang)
        return jsonify(result)
    except TtsError as exc:
        return jsonify(error=str(exc)), 502
