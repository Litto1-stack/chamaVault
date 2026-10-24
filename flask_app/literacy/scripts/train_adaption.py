#!/usr/bin/env python3
"""Upload Vaulti dataset to Adaption, augment, and run AutoScientist.

Default model: openai/gpt-oss-20b (fast iterate). Promote with:
  python literacy/scripts/train_adaption.py --model Qwen/Qwen3.6-35B-A3B

Requires: pip install 'adaption>=0.7.0' and ADAPTION_API_KEY.

Usage (from flask_app):
  python literacy/scripts/build_dataset.py
  python literacy/scripts/train_adaption.py
  python literacy/scripts/train_adaption.py --download best-checkpoint.tgz
"""
from __future__ import annotations

import argparse
import math
import os
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CSV = ROOT / "literacy" / "vaulti_training.csv"
DEFAULT_MODEL = "openai/gpt-oss-20b"
PROMOTE_MODEL = "Qwen/Qwen3.6-35B-A3B"


def main():
    parser = argparse.ArgumentParser(description="Train Vaulti on Adaption AutoScientist")
    parser.add_argument("--csv", type=Path, default=DEFAULT_CSV)
    parser.add_argument("--model", default=os.environ.get("ADAPTION_MODEL", DEFAULT_MODEL),
                        help=f"Base model id (default {DEFAULT_MODEL}; promote to {PROMOTE_MODEL})")
    parser.add_argument("--max-iterations", type=int, default=3)
    parser.add_argument("--target-win-rate", type=float, default=0.7)
    parser.add_argument("--min-domain-rows", type=int, default=20_000)
    parser.add_argument("--download", type=Path, default=None,
                        help="If set, wait and stream best checkpoint to this path")
    parser.add_argument("--dataset-id", default=None,
                        help="Reuse an existing Adaption dataset id (skip upload)")
    args = parser.parse_args()

    if not os.environ.get("ADAPTION_API_KEY"):
        print("Set ADAPTION_API_KEY first (Adaption Settings → API keys).", file=sys.stderr)
        sys.exit(1)

    try:
        from adaption import Adaption
    except ImportError:
        print("Install adaption: pip install 'adaption>=0.7.0'", file=sys.stderr)
        sys.exit(1)

    client = Adaption()

    if args.dataset_id:
        dataset_id = args.dataset_id
        print(f"Using dataset {dataset_id}")
    else:
        if not args.csv.exists():
            print(f"Missing {args.csv}. Run build_dataset.py first.", file=sys.stderr)
            sys.exit(1)
        print(f"Uploading {args.csv} …")
        dataset = client.datasets.upload_file(
            str(args.csv),
            processing_mode="raw",
            column_mapping={"prompt": "instruction", "completion": "response"},
        )
        dataset_id = dataset.dataset_id
        print(f"Dataset id: {dataset_id}")
        while True:
            status = client.datasets.get_status(dataset_id)
            if status.status == "failed":
                err = status.error_data
                msg = (err and getattr(err, "message", None)) or "unknown error"
                raise RuntimeError(f"Ingestion failed: {msg}")
            if status.row_count is not None:
                print(f"Imported {status.row_count} rows")
                break
            time.sleep(5)

    dataset = client.datasets.get(dataset_id=dataset_id)
    base_rows = dataset.row_count or 0
    domain_rows_to_add = max(0, args.min_domain_rows - base_rows)
    total_domain = base_rows + domain_rows_to_add
    general_rows_to_add = math.ceil(0.4 * total_domain / 0.6) if total_domain else 0
    print(f"Augment plan: +{domain_rows_to_add} domain, +{general_rows_to_add} general")

    print(f"Starting AutoScientist on {args.model} …")
    run = client.autoscientist.create(
        dataset_id=dataset_id,
        model=args.model,
        max_iterations=args.max_iterations,
        target_win_rate=args.target_win_rate,
        augmentation_domain_rows=domain_rows_to_add,
        augmentation_general_rows=general_rows_to_add,
    )
    print(f"Run {run.id} status={run.status}")
    print("Poll in the Adaption app, or re-run with --download PATH after success.")

    if args.download:
        print("Waiting for completion …")
        run = client.autoscientist.wait_for_completion(run.id)
        if run.status != "succeeded":
            raise RuntimeError(f"{run.status}: {getattr(run, 'error', None)}")
        print(f"Best win rate: {getattr(run, 'best_win_rate', None)}")
        if not run.download_available:
            raise RuntimeError("Checkpoint not available for download")
        with client.autoscientist.with_streaming_response.download(run.id) as response:
            response.stream_to_file(str(args.download))
        print(f"Saved {args.download}")
        print("Next: upload the LoRA to Together AI and set VAULTI_MODEL_ID + TOGETHER_API_KEY.")


if __name__ == "__main__":
    main()
