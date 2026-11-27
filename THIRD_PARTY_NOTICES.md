# Third-Party Notices — LAYA v7.1

Date checked: **2026-11-27** (all licenses below were verified against the
Hugging Face model card / LICENSE file of each repository on that date;
source URLs are given per row). Licenses change: re-verify against the
upstream card before any release, and before training on any of these
weights.

> **License allowlist for production / CI (plan §7.4): Apache-2.0, MIT, or
> BSD-3-Clause ONLY.** Anything else — in particular CC-BY-NC — must never
> appear in the default runtime or CI. The CI license gate (Lane 10) must
> block it.

## Production-path models (permissive)

| Model (Hugging Face ID) | Role in LAYA v7.1 | License (verified 2026-11-27) | Source |
|---|---|---|---|
| `google/muril-base-cased` | **RECOMMENDED primary direct bilingual encoder** (V71-P3-1): fine-tune target for EN + KN + Kanglish Stage 0/1 heads. 237M params, pre-trained on 17 Indian languages **and their transliterated counterparts** — the only candidate with native romanized-Indic pretraining. | **Apache-2.0** — card metadata `license: apache-2.0` | https://huggingface.co/google/muril-base-cased/blob/main/README.md |
| `jhu-clsp/mmBERT-base` | Runner-up direct bilingual encoder (ModernBERT arch, 307M, 1800+ languages, 8k context). Also the encoder inside `convaiinnovations/laya` multilingual (322M). | **MIT** — see correction note below. The plan (§3.2) claimed Apache-2.0; that claim is **not supported** by the evidence found: the official card body carries no license section, its only license mention is `license="mit"` in the reranking code example, and two independent derivative NOTICEs state the card declares MIT. Treat as MIT; re-confirm via the Hub API `cardData.license` before training. | https://huggingface.co/jhu-clsp/mmBERT-base |
| `FacebookAI/xlm-roberta-base` | Fallback direct bilingual encoder (279M, 100 languages incl. Kannada). Well-understood, no Indic-specific transliteration pretraining. | **MIT** — card metadata `license: mit` | https://huggingface.co/FacebookAI/xlm-roberta-base/blob/main/README.md |
| `FacebookAI/xlm-roberta-large` | Larger fallback encoder (560M) if base underperforms. Same license, ~4x compute of base. | **MIT** — Hub license tag `mit` | https://huggingface.co/FacebookAI/xlm-roberta-large |
| `BAAI/bge-m3` | Evaluated candidate; embedding model (567M, 100+ languages, 8k context), not an MLM encoder — usable as a retrieval-style encoder only with adaptation, not a drop-in classification backbone. | **MIT** — card metadata `license: mit` | https://huggingface.co/BAAI/bge-m3 |
| `answerdotai/ModernBERT-large` | Teacher backbone family (English-only; the current `PIXMELT/laya` English checkpoint is a ModernBERT-large fine-tune, 421M). | **Apache-2.0** — "We release the ModernBERT model architectures, model weights, training codebase under the Apache 2.0 license." | https://huggingface.co/answerdotai/ModernBERT-large (via unsloth/ModernBERT-large card copy) |
| `microsoft/deberta-v3-large` | Teacher alternative (plan §1.2, V71-P1-3): English-only, 304M backbone + 131M embeddings. | **MIT** — card metadata `license: mit` | https://huggingface.co/microsoft/deberta-v3-large/blob/main/README.md |
| `PIXMELT/laya` | Current v7 English Stage 0/1 teacher (421M, ModernBERT-large backbone, revision `29a1a48862bf4a92935c5a7162e1f88a05fc7440`). | **Apache-2.0** — card: "Apache-2.0 — unchanged from the upstream `convaiinnovations/laya` checkpoint." | https://huggingface.co/PIXMELT/laya |
| `convaiinnovations/laya` (multilingual subfolder) | Multilingual Laya checkpoint (322M, mmBERT-base encoder). Historical reference only: scored 6/16 EN / 0/16 KN on C13 (plan §3.1) — do not use as the Kannada path. | **Apache-2.0** (checkpoint) over an **MIT** encoder (`jhu-clsp/mmBERT-base`) — both notices must be preserved. | https://huggingface.co/convaiinnovations/laya |

## Translation backup only (permissive; never an end-task classifier)

| Model (Hugging Face ID) | Role in LAYA v7.1 | License (verified 2026-11-27) | Source |
|---|---|---|---|
| `ai4bharat/indictrans2-indic-en-dist-200M` | Optional `--mode translate_fallback` backup, sentence-level literal translation ONLY, strictly on C13 if a dialect gap needs an English pivot (V71-P3-1). | **MIT** — card metadata `license: mit`; repo contains a full MIT LICENSE file, Copyright (c) AI4Bharat | https://huggingface.co/ai4bharat/indictrans2-indic-en-dist-200M/blob/main/README.md and https://huggingface.co/ai4bharat/indictrans2-indic-en-dist-200M/blob/main/LICENSE |
| `Qwen/Qwen2.5-1.5B-Instruct` | Optional LoRA-fine-tuned sentence-level literal translator backup (same restricted role as IndicTrans2). | **Apache-2.0** — repo LICENSE file, Copyright 2024 Alibaba Cloud | https://huggingface.co/Qwen/Qwen2.5-1.5B-Instruct/blob/main/LICENSE |
| `Qwen/Qwen3-1.7B` | Current `structured`-mode slot extractor (already in `src/laya_v7_extractor.py`, revision `70d244cc86ccca08cf5af4e1e306ecf908b1ad5e`); also a translator-backup candidate. | **Apache-2.0** — Hub metadata `license: apache-2.0`, license link to `Qwen/Qwen3-1.7B/blob/main/LICENSE` | https://huggingface.co/Qwen/Qwen3-1.7B |

## RETIRED from the default path — research-only, noncommercial

| Model (Hugging Face ID) | Status | License (verified 2026-11-27) | Source |
|---|---|---|---|
| `facebook/nllb-200-distilled-600M` | **RETIRED from the production default** (V71-P3-1). Currently the default in `src/laya_v7_extractor.py:24` (`NLLB_MODEL_ID`) — see the patch spec in `docs/10x_swarm_state/lane-06-p3.md` for its removal. If retained at all, only behind an explicit `--allow-nc-research` flag for reproducibility, never in default mode or CI. 1,186 MB fp16, ~2.39s GPU / ~2.76s/Q CPU translation latency, and known translation loss (ಕೇಳಿಲ್ಲ → "didn't hear it", ಅತ್ತೆಯ → "aunt"). | **CC-BY-NC-4.0** — card metadata `license: cc-by-nc-4.0`; card states "NLLB-200 is a research model and is not released for production deployment." Noncommercial use only. | https://huggingface.co/facebook/nllb-200-distilled-600M/blob/main/README.md |

## Notes

- **mmBERT correction (2026-11-27):** plan §3.2 lists `jhu-clsp/mmBERT-base`
  as Apache-2.0. Lane 06 could not verify that: the official card fetched
  2026-11-27 shows no license section and its only license string is
  `license="mit"` (reranking example), and the LiteRT Laya-Multilingual
  NOTICE plus the YunkunSong laya-heart NOTICE both state the mmBERT card
  declares MIT. The plan text should be corrected to MIT at merge, and the
  Hub API value re-checked immediately before any training run.
- **Qwen2.5-3B warning (not used here):** within the Qwen2.5 family the 3B
  instruct checkpoint alone carries the noncommercial `qwen-research`
  license while 0.5B/1.5B/7B/14B/32B are Apache-2.0. License is a property
  of the checkpoint, not the family — always verify the exact checkpoint.
- **This file is not legal advice.** It records what Lane 06 checked, when,
  and where. The repository owner must confirm the LICENSE choice
  (see `LICENSE`, pending owner confirmation) and re-verify every weight
  license before release.
