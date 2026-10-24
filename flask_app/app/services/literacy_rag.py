"""Lightweight keyword RAG over curated Kenyan literacy docs + optional CBK FX."""
from __future__ import annotations

import json
import urllib.error
import urllib.request
from functools import lru_cache
from pathlib import Path

DOCS_DIR = Path(__file__).resolve().parents[2] / "literacy" / "docs"

# topic keywords -> doc stem (without .md)
TOPIC_DOCS = {
    "ipo": "ipo_basics",
    "share": "ipo_basics",
    "hisa": "ipo_basics",
    "dangote": "ipo_basics",
    "nse": "ipo_basics",
    "prospectus": "ipo_basics",
    "stock": "ipo_basics",
    "cma": "regulated_products",
    "sacco": "regulated_products",
    "sasra": "regulated_products",
    "mmf": "regulated_products",
    "money market": "regulated_products",
    "t-bill": "regulated_products",
    "treasury": "regulated_products",
    "bond": "regulated_products",
    "goal": "goal_math",
    "lengo": "goal_math",
    "save": "goal_math",
    "akiba": "goal_math",
    "pledge": "goal_math",
    "scam": "scams",
    "ulaghai": "scams",
    "guaranteed": "scams",
    "pin": "scams",
    "crypto": "scams",
}


@lru_cache(maxsize=1)
def _load_docs() -> dict[str, str]:
    docs = {}
    if not DOCS_DIR.is_dir():
        return docs
    for path in DOCS_DIR.glob("*.md"):
        docs[path.stem] = path.read_text(encoding="utf-8")
    return docs


def retrieve(question: str, limit: int = 2) -> list[str]:
    """Return up to `limit` doc snippets relevant to the question."""
    q = (question or "").lower()
    docs = _load_docs()
    hits: list[tuple[int, str]] = []
    for keyword, stem in TOPIC_DOCS.items():
        if keyword in q and stem in docs:
            hits.append((q.count(keyword), stem))
    # unique stems, highest hit count first
    ordered, seen = [], set()
    for _, stem in sorted(hits, key=lambda x: -x[0]):
        if stem not in seen:
            seen.add(stem)
            ordered.append(docs[stem])
        if len(ordered) >= limit:
            break
    return ordered


def fetch_cbk_fx_summary(timeout: float = 3.0) -> str | None:
    """Optional live CBK indicative rates via Frankfurter (no API key)."""
    url = "https://api.frankfurter.dev/v2/providers/cbk/rates?base=KES"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "ChamaVault/1.0"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, ValueError):
        return None
    rates = data.get("rates") or {}
    if not rates:
        return None
    # Highlight a few currencies Kenyans often care about
    parts = []
    for code in ("USD", "EUR", "GBP", "UGX", "TZS"):
        if code in rates:
            parts.append(f"1 KES ≈ {rates[code]} {code}" if rates[code] < 1
                         else f"1 {code} ≈ {round(1 / rates[code], 4)} KES" if rates[code] else code)
            # Frankfurter with base=KES usually gives foreign per KES; keep raw
            parts[-1] = f"KES→{code}: {rates[code]}"
    date = data.get("date", "")
    return "CBK indicative FX (" + date + "): " + "; ".join(parts[:5]) if parts else None


def build_context(question: str, include_fx: bool = True) -> str:
    """Concatenate RAG snippets for the LLM system prompt."""
    chunks = retrieve(question)
    if include_fx and any(k in (question or "").lower() for k in ("fx", "dollar", "usd", "exchange", "ubadilishaji", "cbk")):
        fx = fetch_cbk_fx_summary()
        if fx:
            chunks.append(fx)
    if not chunks:
        return ""
    return "Grounding notes (education only):\n\n" + "\n\n---\n\n".join(chunks)
