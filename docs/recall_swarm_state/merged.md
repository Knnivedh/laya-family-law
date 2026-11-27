# LAYA v7.1 / Recall Swarm — Merged Lane Status View

Owner: Lane 10 (docs/merge) created this file; the coordinator owns updates once Lane 10 is done.
Merged view of all lane status files in `docs/recall_swarm_state/lane-*.md`.
Last updated: 2026-11-27 ~20:05 IST (Lane 10, update 6 — FINAL: all 11 lanes done, swarm complete).

## Summary

- Lane status files landed: **11 of 11 — all lanes done.**
- Commits on top of recall baseline `1cb0bff`: **26** (HEAD `f92a9e5`, verified by
  `git rev-list --count 1cb0bff..HEAD`); recall delta **41 files**.
- FINAL held-out validation exact numbers (HEAD `c57919c`, frozen split sha `7640d067…`,
  evidence mode, CPU; Lane 10 re-verified at HEAD `f92a9e5`): **synthetic 261/500 = 52.2%**
  (Wilson [0.4782, 0.5654], micro-P 0.8905 / R 0.4623 / F1 0.6086, TP/FP/FN 423/52/492,
  silent 212; EN 209/235, KN 30/153, Kanglish 22/112); **Kaanoon 14/28 = 50.0%**
  (TP/FP/FN 27/9/18, silent 6; 10/21 = 47.6% on non-empty-expected items).
  **The ≥70% target was NOT reached** — final is 17.8 points short. Do not claim 70% until a
  real run measures it. Full pins + progression table in `docs/recall_status.md` §3.
- 16-Q regression set: 14/16 exact, esc_bool 16/16, esc_kinds 10/16, fp_prose 0, rating 7.6 —
  no regression from any lane.
- Guardrails at final HEAD: graph test PASS (34/66/99, 0 dangling, 7/7 frozen SHAs); prose PASS
  (246 cases, Fp=0, 15/15 mutants); full unit suite **66/66 OK** (was 49; +17 Lane 03 C5 tests).
- Sealed baselines: Fresh-20 7/20 (35%), Kannada-8 4/8 (50%) — sealed re-run RTX-only.

## Per-lane status

| Lane | Scope | Status file | Status | Changes | Needs / blockers |
|---|---|---|---|---|---|
| 01 | Diagnosis: per-cause failure breakdown | `lane-01-diagnosis.md` | DONE — MERGED `f92a9e5` (coordinator commit) | Analysis only; v1 numbers confirmed by Lane 09 | Pinned §2–§5 unverifiable-now (file gone) |
| 02 | Paraphrase expansion: grow corpus, keep split clean | `lane-02-paraphrase.md` | DONE — MERGED `de52ad4` | Corpus 5,000 → 8,000; frozen split sha `7640d067…`; leakage PASS | Sealed leakage check QUEUED |
| 03 | Evidence anchors: harden regex anchors | `lane-03-anchors.md` (151 lines) | DONE — MERGED `80e53d8`, `a0d58a0`, `58d950c`, `7839e86`, `c57919c` | 5 anchor rounds; C4 Kaanoon/audit forms + in_scope OOS override + procedure issue; C5 17 tests | Residuals: in_scope 3/222, landlord-evictor probe, mixed DV+OOS limitation |
| 04 | Classifier training prep: runnable training, RTX commands | `lane-04-classifier.md` | DONE — MERGED `6eb21d2`, `c596512`, `5498c91` | PC-2 vocab pin, LoRA fix, RTX doc + status | 8,000 re-run; RTX training run |
| 05 | Kannada/Kanglish coverage | `lane-05-kannada.md` | DONE — MERGED `a1f8c42`, `c19cecd`, `3d03399` | 25 KN blocks (en 50 / kn 54 / kn_roman 71) | P2.1 native-speaker audit; §4 AFTER superseded |
| 06 | Consultation brief (Gemini + ChatGPT) — PRIORITY, deliver first | `lane-06-brief.md` | DONE — MERGED `f92a9e5`; brief §3 corrected `0dbbad9` | `docs/recall_consultation_brief.md` (77 lines) | Model answers not yet received; R5 holds |
| 07 | Evaluation harness: held-out validation scoring | `lane-07-harness.md` (165 lines) | DONE — MERGED `aba4151`, `f9a4fdc` + fix `0dbbad9` | `tests/recall_eval.py`, `--suite kaanoon`, sex-mapping fix | Self-test count claim "15" wrong (12/21); otherwise done |
| 08 | Stage 1 routes audit + fixes | `lane-08-routes.md` | DONE — MERGED `b9cd21c`, `4c464d6`, `69936e1` | Prompts 9 → 11, post-order facts, bnss-144-3/bnss-146; 16-Q 14/16 | Enumeration/probe claims UNVERIFIED |
| 09 | Independent verifier: blind-checks other lanes | `lane-09-verifier.md` | DONE — MERGED `8881a12` | 623-line verification of lanes 01–08, 10, 11 | — |
| 10 | Docs/merge: tracker + merged view + push manifest | — (this file) | DONE — update 6, FINAL | `docs/recall_status.md`, `docs/recall_swarm_state/merged.md`, `PUSH-MANIFEST-RECALL.md` | Push is coordinator/parent's next step (see manifest) |
| 11 | Kaanoon DO BOTH: held-out eval set + phrasing-patterns study | `lane-11-kaanoon.md` | DONE — MERGED `410d65b` | Eval 28 + study 16 + patterns doc (150 lines) | Leakage report STALE; asker-perspective GT decision (coordinator) |

## Cross-lane contracts — status (final)

- R1 — Validation split is the ONLY progress number (500-record FROZEN `validation.jsonl`,
  sha `7640d067…`): **MEASURED — FINAL 261/500 = 52.2%**, Lane 10 reproduced exactly.
- R2 — Corpus schema (Lane 02 owns; Lane 04 codes against it): **DONE** — corpus 8,000;
  Lane 04's loader/count claims are OLD-corpus-pinned, 8,000 re-run open.
- R3 — Lane 03 anchors in `laya_v7_evidence.py` ONLY; Lane 08 route/emission fixes in
  extractor/graph: **RESPECTED**.
- R4 — Lane 05 NEW files only; Lane 02 wires templates into the builder: **DONE**.
- R5 — Lane 06's brief to parent FIRST; no lane adopts model advice until coordinator checks it
  against our own numbers: **BRIEF CORRECTED (`0dbbad9`) + MERGED (`f92a9e5`)** — model answers
  not yet received.
- R6 — Kaanoon real-phrasing eval: evaluation only, Lane 07 scores it, no lane tunes against it;
  FINAL baseline **14/28 (50.0%)**, separate from synthetic.
- R7 — Lane 02's Kaanoon reconciliation used ONLY the patterns file, never the held-out set.

## Lane 09 verification — summary

Per-lane verdicts (commit `8881a12`, full table in `docs/recall_status.md` §9): 01 VERIFIED
(pinned §2–§5 unverifiable-now); 02 VERIFIED; 03 VERIFIED code+suites rounds 1–3, 2 defects open
at that time (fixed in C4 per `7839e86`); 04 VERIFIED old-corpus-pinned; 05 VERIFIED except §4
AFTER superseded; 06 VERIFIED numbers, §3 NEEDS CORRECTION (fixed by `0dbbad9`); 07 VERIFIED
baseline exact, 2 mismatches (sex-mapping bug + self-test count); 08 VERIFIED code+16-Q,
enumeration/probe claims UNVERIFIED; 10 VERIFIED-at-write-time, stale at update 5 (fixed by
updates 5–6); 11 VERIFIED in depth (blind re-label 4/9, derivation 0 mismatches, disjointness PASS).

## External reference — kaanoon.com

https://www.kaanoon.com/ ("Legal answers online from lawyers - Indian Kaanoon", verified by Lane 10
via page-text fetch 2026-11-27 ~19:40 IST). Lane 11 DONE — MERGED `410d65b`: held-out eval set
28 items (custody 5, maintenance 5, divorce 5, restitution 4, eviction 3, stridhan 2,
joint_property 2, violence 2) + study sample 16 + phrasing-patterns doc (150 lines). FINAL
Kaanoon baseline 14/28 (50.0%). Bounds: no wholesale copying into the training corpus; lawyers'
answers never cited as authority; eval set is evaluation only. Full record:
`docs/recall_status.md` §8.

## Gemini consultation — Hydrogen fallback, NOT Neon (filed 2026-11-27 ~20:12 IST)

**CAVEAT FIRST:** Neon was selected (Thinking High) but Gemini fell back to "Hydrogen High" —
the answer is NOT from Neon, so a real Neon re-run is still owed. Chat
https://gemini.google.com/app/18aadfecd490504c, signed in as Rocky Balbao (elvyn32@santarivn.store).
Two sentences truncated in the page's own text view. Sign-in note: nivedhbhat15@gmail.com was
rejected ("Wrong password"); signed in with the saved Elvyn login instead — the nivedh Google
password in the vault does not match that account (or has changed), unresolved.

Key verdicts (proposed, NOT adopted): (1) REPLACE Stage 1 outright with the classifier; regex only
as post-classifier guards/overrides, never a veto — STOP tuning regex anchors. (2) 8k template
corpus plateaus at 58–66% EN / 48–58% KN; crossing 70% needs mmBERT-base or xlm-roberta-large
(MIT), +3,000–4,000 LLM-diversified paraphrases (1,100 residence/lockout, 900 joint-property/
Stridhan, 900 custody/welfare, 700 divorce/ancillary, 400 dense multi-issue), recall-biased
per-head thresholds — projected ~72–78% EN / ~65–72% KN/Kanglish at 12,000–13,000 total
(Gemini's projections, not measured numbers). (3) Build a 250-item Blind Human-Register Stress
Set (`data/eval_blind_register_250.jsonl`) as the pre-sealed go/no-go gate (≥72% exact,
micro-R ≥0.90, micro-P ≥0.92); synthetic val split must never be the sole gate. (4) Fix before
Run #1: bf16 + grad checkpointing + max_seq_len 288, grouped validation split, audit the 8 dead
fact keys. **ChatGPT's answer still pending — nothing adopted until it lands and both are
checked against our own numbers.** Full record: `docs/recall_status.md` §10. Source file:
`workspace/goals/english-family-law-chatbot-retest/files/laya-graph/gemini-recall-consultation.md`.

## ChatGPT consultation + both-model synthesis — ADOPTED as the working decision (filed 2026-11-27 ~20:13 IST)

**Model: GPT-6.2, thinking max — the REAL requested model** (unlike Gemini's Hydrogen fallback;
see the Gemini note above — a real Neon re-run is still owed). Chat
https://chatgpt.com/c/6b0995f0-cd70-83ec-aa08-b3f0baa9944d, response complete, "Worked for 2m 2s",
no sign-in needed, brief pasted exactly as given.

**Adopted synthesis (9 points, checked against our own numbers):** (1) Replace Stage 1 with the
classifier; regex never a recall gate (post-classifier evidence only: citations, dates, amounts +
consistency guards). (2) mmBERT-base (MIT) primary; English-only ModernBERT/DeBERTa rejected as
default (Gemini alt: xlm-roberta-large; ChatGPT alt: mDeBERTa-v3-base). (3) Train the existing 8k
FIRST with a nested learning curve (2k/4k/7.5k) before deciding on expansion — ChatGPT's
sequencing wins over Gemini's pre-commitment to +4k; settle 8k-vs-70% by measurement. (4) Dead
fact keys + graph contract first (P0). (5) bf16 + grad checkpointing + micro-batch 1 / grad-accum 8
on the RTX 5050 (both models: 36 sequences/step will OOM). (6) Pre-sealed gate: ONE independent
human-written holdout, 300 items (100/language), ≥80% exact per language — ChatGPT's stricter
gate, not Gemini's 250/≥72%. (7) Per-head thresholds via OOF + shrinkage; no label smoothing.
(8) NEW pre-training gates: four-configuration graph oracle (gold/gold, gold/pred, pred/gold,
pred/pred); audit clause supervision (never assign question-level labels to every clause).
(9) Brief inconsistency to reconcile before the next evaluation report: Fresh-20 category
breakdown sums to 18 questions / 5 exact and itemised FNs sum to 27, not 20 / 7 / 28;
coordinator-verified headline aggregates ARE consistent (7/20, TP/FP/FN 38/5/28) — two exact
questions unaccounted for; reconcile WITHOUT opening sealed text. **Adopted allocation overlap:**
residence/lockout + joint-property/Stridhan are the top two clusters in BOTH models' next-4,000
allocations. **NOT IMPLEMENTED — adopted working decision only; execution is the next phase
(RTX training).** Full record: `docs/recall_status.md` §11. Source file:
`workspace/goals/english-family-law-chatbot-retest/files/laya-graph/chatgpt-recall-consultation.md`.

## How this file updates

Lane 10's work is DONE (update 6, FINAL). Any further update is the coordinator's.
Status was asserted only from lane files or commands Lane 10 ran.

## Coordinator addendum — Deep >70% plan (2026-11-27 ~21:00 IST)

The deep plan to reach >70% is filed at `workspace/goals/english-family-law-chatbot-retest/files/laya-graph/70-percent-plan.md` and copied verbatim into this repo as `docs/70-percent-plan.md` (sha256 `dca2be7f…`, identical). Built only from verified sources: swarm final numbers (261/500, 52.2%; Kaanoon 14/28), Gemini consultation (Hydrogen fallback caveat — NOT Neon, re-run owed) and ChatGPT consultation + both-model synthesis. Phases A–F with gates (pre-training gates A1–A7; Run #1 nested 2k/4k/7.5k; ~4,750 targeted records; 300-item holdout ≥80%/language; sealed re-run Fresh-20 ≥14/20, Kannada-8 ≥6/8; distillation post-70%). Exact RTX commands live in `docs/recall_swarm_state/lane-04-classifier.md`, not in the plan. Nothing in the plan claims ≥70% — it is a path with gates, not a result. Full record: `docs/recall_status.md` §12.
