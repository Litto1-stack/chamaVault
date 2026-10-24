# Vaulti literacy training (Adaption)

1. Build CSV: `python literacy/scripts/build_dataset.py`
2. Train: set `ADAPTION_API_KEY`, then `python literacy/scripts/train_adaption.py`
3. Promote quality: `--model Qwen/Qwen3.6-35B-A3B`
4. Download LoRA: `--download best-checkpoint.tgz`
5. Host on Together AI; set `TOGETHER_API_KEY` and `VAULTI_MODEL_ID` in the app.

Curated RAG snippets live in `literacy/docs/` and are loaded at answer time by `app/services/literacy_rag.py`.
