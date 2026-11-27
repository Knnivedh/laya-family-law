# Lane 06 — V71-P3 Multilingual + Licensing — Status

Lane: 06 · Plan: docs/10x_plane.md §3 (V71-P3-1..V71-P3-3) · Date: 2026-11-27
Working copy: `~/workspace/laya-v71-work` (baseline bc7f40f). No git write
commands run (coordinator owns commit/push). No frozen file touched;
`test_graph_v4.py` PASS (7/7 SHAs intact), `test_prose_renderer_v2.py`
PASS (246 cases, Fp=0) after my changes.

## Files delivered (Lane 06 only)

- `src/laya_lang_normalizer.py` (new)
- `src/laya_lang_pack.py` (new)
- `LICENSE` (new — **DRAFT, pending owner confirmation, see flag below**)
- `THIRD_PARTY_NOTICES.md` (new)
- This status file: `docs/10x_swarm_state/lane-06-p3.md`

No other lane's files edited. No sealed test-bank file opened.

## 1. License verification table (checked 2026-11-27, HF model card / LICENSE file)

| Model | Verified license | Permissive? | Source |
|---|---|---|---|
| `BAAI/bge-m3` | MIT (`license: mit`) | Yes | https://huggingface.co/BAAI/bge-m3 |
| `FacebookAI/xlm-roberta-base` | MIT (`license: mit`) | Yes | https://huggingface.co/FacebookAI/xlm-roberta-base/blob/main/README.md |
| `FacebookAI/xlm-roberta-large` | MIT (Hub tag `mit`) | Yes | https://huggingface.co/FacebookAI/xlm-roberta-large |
| `google/muril-base-cased` | Apache-2.0 (`license: apache-2.0`) | Yes | https://huggingface.co/google/muril-base-cased/blob/main/README.md |
| `jhu-clsp/mmBERT-base` | **MIT — CORRECTION, see below** | Yes | https://huggingface.co/jhu-clsp/mmBERT-base |
| `ai4bharat/indictrans2-indic-en-dist-200M` | MIT (`license: mit` + full MIT LICENSE file) | Yes | https://huggingface.co/ai4bharat/indictrans2-indic-en-dist-200M/blob/main/README.md |
| `Qwen/Qwen2.5-1.5B-Instruct` | Apache-2.0 (LICENSE file, © 2024 Alibaba Cloud) | Yes | https://huggingface.co/Qwen/Qwen2.5-1.5B-Instruct/blob/main/LICENSE |
| `Qwen/Qwen3-1.7B` | Apache-2.0 (Hub metadata, license link to `Qwen/Qwen3-1.7B/blob/main/LICENSE`) | Yes | https://huggingface.co/Qwen/Qwen3-1.7B |
| `answerdotai/ModernBERT-large` | Apache-2.0 ("We release … under the Apache 2.0 license") | Yes | https://huggingface.co/answerdotai/ModernBERT-large |
| `microsoft/deberta-v3-large` | MIT (`license: mit`) | Yes | https://huggingface.co/microsoft/deberta-v3-large/blob/main/README.md |
| `PIXMELT/laya` | Apache-2.0 (unchanged from upstream `convaiinnovations/laya`) | Yes | https://huggingface.co/PIXMELT/laya |
| `convaiinnovations/laya` (multilingual) | Apache-2.0 checkpoint over MIT encoder (`jhu-clsp/mmBERT-base`) — both notices apply | Yes | https://huggingface.co/convaiinnovations/laya |
| `facebook/nllb-200-distilled-600M` | **CC-BY-NC-4.0** (`license: cc-by-nc-4.0`; card: "a research model and is not released for production deployment") | **No — RETIRED from default** | https://huggingface.co/facebook/nllb-200-distilled-600M/blob/main/README.md |

Nothing is marked UNVERIFIED: every candidate above was checked against
its Hugging Face card / LICENSE file on 2026-11-27.

### ⚠️ Correction: plan §3.2's mmBERT license claim is wrong

The plan lists `jhu-clsp/mmBERT-base` as **Apache-2.0**. Lane 06 could
not verify that. The official card fetched 2026-11-27 has no license
section; its only license string is `license="mit"` in the reranking
code example, and two independent derivative NOTICEs (LiteRT
Laya-Multilingual NOTICE; YunkunSong laya-heart NOTICE) state the card
declares **MIT**. This lane records mmBERT-base as **MIT** and flags the
plan text for correction at merge. **Re-confirm via the Hub API
(`cardData.license`) immediately before any training run** — license is
a property of the checkpoint, not the family (cf. Qwen2.5-3B, which
alone in its family carries the noncommercial `qwen-research` license).

## 2. Primary encoder recommendation

**Primary: `google/muril-base-cased` (Apache-2.0).** Reasons:

1. Only candidate pre-trained on 17 Indian languages **and their
   transliterated counterparts** — directly addresses Kanglish, the
   hardest P3 failure mode, without a translation pivot.
2. Apache-2.0 matches the repo LICENSE direction (no MIT/Apache mixing
   question for the primary path).
3. Smallest serious candidate (~237M params, BERT arch) — best CPU
   latency outlook of the permissive encoders, relevant to the G14
   < 0.5s/Q CPU bar.
4. Proven in production-adjacent Indic work (Hinglish language ID,
   Indic NER/PII fine-tunes inherit its Apache-2.0).

**Runner-up: `jhu-clsp/mmBERT-base` (MIT, 307M, ModernBERT, 8k context,
1800+ languages)** if MuRIL underperforms on Kannada — but note the
Laya multilingual fine-tune on this encoder scored 0/16 on KN prompts
(plan §3.1), so the encoder alone is not evidence; it needs the same
bilingual fine-tune and an A/B against MuRIL on the RTX 5050.
**Fallback: `FacebookAI/xlm-roberta-base` (MIT, 279M)** — well-understood,
no Indic transliteration pretraining. `BAAI/bge-m3` (MIT, 567M) is an
embedding model, not a drop-in MLM classification backbone; deprioritise.
**Translation backup (only if a dialect gap needs an English pivot,
sentence-level literal translation only, never end-task classifier):
`ai4bharat/indictrans2-indic-en-dist-200M` (MIT) first; Qwen2.5-1.5B /
Qwen3-1.7B (Apache-2.0) LoRA second.**

This recommendation is architectural, not empirical: the A/B
(MuRIL vs mmBERT vs XLM-R-base on the Lane 02 bilingual corpus) still
needs the RTX 5050 run (Lane 03 / Lane 08).

## 3. Normalizer — `src/laya_lang_normalizer.py`

Pure Python, no torch. `detect_script_locale(raw_text, explicit_locale)`
is a superset of the v7 return value: `{"lang", "script",
"code_mix_ratio"}` with `lang ∈ {en, kn, kn_roman}`,
`script ∈ {latin, kannada, mixed}`, `code_mix_ratio ∈ [0, 0.5]`
(min-script letter share; 0.0 = single script).

- Mixed-script: Kannada Unicode + Latin letters → `kn` / `mixed`;
  English legal insertions (maintenance, divorce, school fees) are
  expected and do not flip the language.
- Kanglish: morphological suffix + stopword scoring (suffixes
  -uttilla, -uttiddare, -abeku, -beku, -illa, -inda, -akke; roots
  nanna, ganda, hendati, magu, magalu, maga, mane, chinna, hana,
  hodeyu, …). Verdict needs score ≥ 3 AND (≥ 1 strong whole-word hit
  OR ≥ 2 distinct suffix-hit tokens).
- Zero-FP protection: `stridhan, streedhan, mangalsutra, panchayat,
  taluk` (+ variants) are stripped before scoring; English
  "-illa" words (vanilla, gorilla, villa) are exempt. Verified in the
  self-test: a stridhan/mangalsutra/panchayat/taluk sentence scores 0
  and stays `en`.
- `kannada_fact_hints(text)`: verification-only signals —
  `demand_made=False` on ಕೇಳಿಲ್ಲ / ಕೇಳಲಿಲ್ಲ / kelilla (matches
  evidence.py:561), `violence_hint` / `eviction_hint` on Kannada +
  roman violence/eviction stems, with `matched_spans` for audit.
  Absence of a stem is never a denial; hints never set a fact alone.
- `split_script_segments(text)`: maximal same-script runs, lossless
  (join == input), English tokens preserved verbatim.
- Self-test: `python3 -m src.laya_lang_normalizer` — **all checks passed**
  (9 detect cases incl. plan §3.2 Kanglish examples, hint cases,
  split round-trip). `python3 -m py_compile` clean for both new modules.

## 4. LanguagePack — `src/laya_lang_pack.py`

`LanguagePack` dataclass per plan §3.2: `lang_code, unicode_range,
sentence_split_regex, roman_detector, negation_demand_lexicon,
template_catalog, benchmark_manifest, native_audit_signoff` (+ `todo`
flag, `ready_for_production` property, `detect()` passthrough).

- `kn`: fully defined (Kannada range U+0C80–U+0CFF, demand/violence/
  residence negation lexicon, prose template pointers, C13 / Sealed
  Kannada-8 / Kanglish-suite benchmark manifest). `native_audit_signoff`
  is empty — P2.1 is still open; `ready_for_production` is False until
  the signed native audit lands.
- `en`: fully defined (Latin ranges, demand lexicon, 16-Q / Brutal-230 /
  Sealed Fresh-20 manifest).
- `hi, ta, te, ml, mr`: explicit TODO stubs. `get_language_pack(code)`
  raises ValueError on a stub unless `allow_stub=True` (research only,
  never production). Verified: `hi` correctly refused; `list_ready_packs()`
  returns `['en', 'kn']`.

## 5. LICENSE — ⚠️ PENDING OWNER CONFIRMATION

`LICENSE` is drafted as **Apache-2.0** (contract C5, plan's permissive
direction), full standard text, copyright line "Copyright 2026 LAYA
Contributors", with an explicit NOTE block at the end stating it is a
draft pending owner confirmation. **The owner must confirm (a) Apache-2.0
itself and (b) the copyright holder name/year before release.** Do not
treat this file as the owner's final licensing decision. `THIRD_PARTY_NOTICES.md`
carries the same caveat ("not legal advice").

## 6. Extractor patch spec — NLLB retirement (for Lane 01 to apply; DO NOT edit by Lane 06)

File: `src/laya_v7_extractor.py` (Lane 01's file). Precise change:

1. Delete / deprecate `NLLB_MODEL_ID = "facebook/nllb-200-distilled-600M"`
   (line 24) as the default. Replace with:
   `TRANSLATE_FALLBACK_MODEL_ID = "ai4bharat/indictrans2-indic-en-dist-200M"`
   (MIT, verified) as the only translation-backup default.
2. Gate all NLLB use behind an explicit flag, e.g.
   `allow_nc_research: bool = False` on `extract_v7_batch` / `extract_v7`,
   plumbed from a CLI `--allow-nc-research` flag. When False, `_load_nllb`,
   `translate_kannada_batch`, and `translate_kannada_to_english` must
   never be called; when True, log a warning that CC-BY-NC-4.0 weights
   are research-only and must not ship.
3. Change the default `kannada_strategy` from `"nllb_then_en"` to
   `"direct"` (direct bilingual encoder path, V71-P3-1): Kannada/Kanglish
   text goes to the Stage 0/1 encoder with `is_kannada=True` /
   `lang ∈ {kn, kn_roman}` from the new normalizer, and `translated_text`
   stays `None` on that path.
4. Replace the local `detect_script_locale` (lines 68–73) with
   `from .laya_lang_normalizer import detect_script_locale` — the new
   function is a superset (adds `code_mix_ratio`, `kn_roman`), so the
   existing `loc["lang"] == "kn"` checks keep working; add
   `loc["lang"] in {"kn", "kn_roman"}` wherever Kannada routing is meant
   (notably the `kn_indices` translation branch, which must then be
   deleted or moved under the research flag, and `is_kn` in
   `extract_v7_batch`).
5. `laya_available()` / `available_on_cuda()` unchanged in this patch
   (Lane 01 owns the CPU-availability fix, V71-P1-1 §3).
6. After applying: run the CI license gate (Lane 10) — default config
   must contain zero CC-BY-NC model IDs — plus `test_graph_v4.py` and
   `test_prose_renderer_v2.py`.

## 7. Blockers / what needs RTX or a human

- **RTX 5050 (not this VM):** encoder A/B (MuRIL vs mmBERT vs XLM-R-base)
  on the Lane 02 bilingual corpus; Kannada latency re-measurement
  (target < 50ms/Q GPU, < 0.5s/Q CPU); Sealed Kannada-8 / C13 re-runs
  after the bilingual fine-tune. No neural work was attempted here
  (no GPU/torch on this VM, per guardrails).
- **Human — repo owner:** confirm Apache-2.0 + copyright holder for
  `LICENSE` (flagged above); correct plan §3.2 mmBERT license to MIT.
- **Human — P2.1 native Kannada speaker:** sign-off still open for the
  `kn` pack (`native_audit_signoff` empty by design), the Kannada prose
  templates (Lane 09), and the Kanglish held-out suite (n ≥ 30).
- **Lane 01:** apply the §6 extractor patch (NLLB retirement).
- **Lane 02:** Kanglish / colloquial Kannada augmentation axes from
  plan §3.2 feed the corpus; this lane's suffix/stopword lists are the
  seed, not a substitute for that corpus.
- **Lane 10:** CI license-allowlist gate must block CC-BY-NC in default
  mode (contract in `THIRD_PARTY_NOTICES.md`).

## 8. Verification log (this lane, 2026-11-27)

- `python3 -m py_compile src/laya_lang_normalizer.py src/laya_lang_pack.py` — clean.
- `python3 -m src.laya_lang_normalizer` — self-test all checks passed.
- `python3 tests/test_graph_v4.py` — PASS: 34 sections / 66 nodes / 99 edges, 0 dangling, 7/7 frozen hashes intact.
- `python3 tests/test_prose_renderer_v2.py` — PASS: 246 cases, Fp=0, quality_flags=0, 15/15 mutants.
- `git status` — only Lane 06 files are new from this lane (`LICENSE`,
  `THIRD_PARTY_NOTICES.md`, `src/laya_lang_normalizer.py`,
  `src/laya_lang_pack.py`); no tracked file modified. Other untracked
  files present belong to concurrently running lanes.
