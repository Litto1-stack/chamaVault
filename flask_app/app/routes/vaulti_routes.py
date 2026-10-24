"""Vaulti coach page; answers as JSON for the chat box or as a normal page without JavaScript."""
from flask import Blueprint, g, jsonify, render_template, request, session

from ..services.vaulti import get_coach
from ..services.vaulti_faq import FAQ

bp = Blueprint("vaulti", __name__)
SUGGESTIONS = {"en": ["How do I improve my score?", "How do I avoid M-Pesa scams?", "What is a money market fund?",
                      "How does compound interest work?"],
               "sw": ["Nitaboreshaje alama yangu?", "Nijikinge vipi na ulaghai wa M-Pesa?", "SACCO ni nini?",
                      "Bajeti ninaipangaje?"]}


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
    return render_template("vaulti.html", lang=lang, question=question, answer=answer,
                           suggestions=SUGGESTIONS[lang], topic_count=len(FAQ))
