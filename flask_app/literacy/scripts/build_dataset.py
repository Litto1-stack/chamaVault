#!/usr/bin/env python3
"""Build Vaulti training CSV from seed pairs + FAQ for Adaption upload.

Usage (from flask_app):
  python literacy/scripts/build_dataset.py
  python literacy/scripts/build_dataset.py --out literacy/vaulti_training.csv
"""
from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "literacy"))

from seed_pairs import iter_training_rows  # noqa: E402


def faq_rows():
    """Mirror local FAQ into training rows so Adaption stays aligned with the app."""
    # Load FAQ module directly to avoid importing the Flask app package.
    import importlib.util

    faq_path = ROOT / "app" / "services" / "vaulti_faq.py"
    spec = importlib.util.spec_from_file_location("vaulti_faq", faq_path)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    FAQ = mod.FAQ

    rows = []
    for topic, (keywords, en, sw) in FAQ.items():
        tip = keywords[0] if keywords else topic
        rows.append({
            "instruction": f"Explain {topic.replace('_', ' ')} for a Kenyan chama member. ({tip})",
            "response": en + " Education only, not financial advice.",
            "lang": "en",
        })
        rows.append({
            "instruction": f"Eleza {topic.replace('_', ' ')} kwa mwanachama wa chama nchini Kenya.",
            "response": sw + " Elimu tu, si ushauri wa kifedha.",
            "lang": "sw",
        })
    return rows


def main():
    parser = argparse.ArgumentParser(description="Build Vaulti Adaption training CSV")
    parser.add_argument(
        "--out",
        type=Path,
        default=ROOT / "literacy" / "vaulti_training.csv",
        help="Output CSV path",
    )
    args = parser.parse_args()

    rows = list(iter_training_rows()) + faq_rows()
    # Deduplicate by instruction text
    seen, unique = set(), []
    for r in rows:
        key = r["instruction"].strip().lower()
        if key in seen:
            continue
        seen.add(key)
        unique.append(r)

    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["instruction", "response", "lang"])
        writer.writeheader()
        writer.writerows(unique)

    print(f"Wrote {len(unique)} rows to {args.out}")
    print("Next: set ADAPTION_API_KEY and run literacy/scripts/train_adaption.py")


if __name__ == "__main__":
    main()
