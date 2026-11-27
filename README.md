# LAYA — Indian Family-Law Classification System

> **A fully interconnected decision graph over the Laya language model that classifies
> complex Indian family-law questions (in plain layman wording, English or Kannada)
> into the exact article / section set that applies — in a fraction of a second
> of model time per decision, with a full legal recheck before anything is returned.**

**Status — read this first (2026-11-27):** the system scores **9.0/10 live on the
16-question regression set** (16/16 exact; 9.8 raw, capped at 9.0 because prose,
fresh held-out, Kannada and confirmation re-run are not measured yet). The
**230-question brutal backtest is RUNNING LIVE in Colab right now** — its results
are NOT in this repo yet and will be added under `results/` when the run finishes.
Nothing in this README claims a result that has not been measured live. Where a
piece is missing, it says so.

**This repo is public so another AI agent can pick the system up cold.** If you are
that agent: start at [§1 Start here](#1-start-here-for-another-agent), then
[§4 How to run it](#4-how-to-run-it), then [§9 Pending tasks](#9-pending-tasks-end-to-end)
for what to do next. You need nothing from the owner to start — but you MUST read
the frozen-file hashes in §3 before running anything, and you MUST NOT edit any
frozen file.

---

## 1. Start here (for another agent)

1. **Clone this repo.** Everything you need is in it except the model weights
   (808 MB — deliberately NOT in the repo; see step 2).
2. **Fetch the model.** The notebooks download it themselves in Colab:
   `snapshot_download(repo_id='PIXMELT/laya')` from Hugging Face, then load the
   **classic encoder checkpoint only** (`laya.load(dir)` or
   `laya.Agent(dir, vegaml=False)`). Fallback named checkpoint:
   `laya.Agent('convaiinnovations/laya', vegaml=False)`.
   - Pin `laya==0.5.5`, `torch`, `transformers`, `safetensors`, `huggingface_hub`.
   - **Never load the Vega engine** (the 0.8B reader `laya.Agent()` loads by
     default) — that is a different model and would produce fake scores. The
     notebooks contain a guard that refuses a Vega-only load.
   - Background: the official Laya repo blocked weight downloads with HTTP 403,
     so the PIXMELT/laya snapshot on Hugging Face is the working source.
   - Classic checkpoint = ModernBERT encoder, architecture `LayaTypedDecisions`,
     ~421M parameters.
3. **Open the newest notebook in Google Colab:**
   `notebooks/live-laya-colab-test-v6-brutal.ipynb`
   (live copy: https://colab.research.google.com/drive/1kA784vVpU87S34og9CpuQcRvUPTj8yKa).
   Runtime: CPU. Full brutal run ≈ 4 hours at ~60 s/question.
4. **Upload the two files the notebook asks for** (via the Colab file picker in
   the cells that request them): `graph/laya-crpc-bns-section-decision-tree-v3.json`
   and `test-bank/brutal-bank-v1-frozen.json`. The notebook verifies their SHA-256
   hashes itself — if a hash does not match, STOP and report; do not continue.
5. **Run all cells, in order, with no edits and no tuning between batches.**
   Each batch cell downloads its per-batch result JSON immediately — save each
   one into `results/` as it lands (a crash loses at most one batch).
6. **Score with the frozen formula in §6.** Report the numbers exactly as the
   notebook prints them. Never present a predicted/offline number as a live one.

---

## 2. What this system is and why it exists

A fresh English retest of the owner's Indian family-law chatbot (2026-11-26)
rated it **4/10 overall** (English 8/10, legal accuracy 3/10, completeness 3/10,
reasoning 2/10). The failures were legal, not linguistic:

- Wrong case law for the wrong issue (*Rajnesh v. Neha* cited for Stridhan;
  *Satish Chander Ahuja* cited for custody).
- Sections listed that nobody asked for (HMA ss.13/13B when no divorce was asked).
- Wrong forum and wrong statute (birth certificate put under HMA instead of the
  Births and Deaths Registration Act; wife's residence called "tenancy rights";
  the user asked to pick the court).
- Missing at the right time: BNSS s.144 / CrPC s.125 and PWDVA s.20 (maintenance),
  HMA s.26 / Guardians and Wards Act (custody), HMA s.27 and IPC s.406 / BNS s.316
  (Stridhan), PWDVA ss.17–20 (residence).

The fix is **not** a bigger prompt. It is a **decision graph** that defines every
section in full detail — what it is, when it is used, what must be true before it
can fire, and how it relates to every other section — with the language model
making one small typed decision per issue inside that graph, and the graph
rechecking the result before anything is returned.

---

## 3. How it works — layer by layer

```
User question (layman English / Kannada)
        │
        ▼
┌───────────────────────────── Stage 0 ─────────────────────────────┐
│ Fact extraction (PLANNED — NOT BUILT YET, see §9)                  │
│ 10 atomic facts, three-state (supported / contradicted / unknown),  │
│ with evidence spans. Today the pipeline uses HAND-ANNOTATED facts   │
│ (an oracle ceiling — see "Honest limits" in §7).                    │
└─────────────────────────────┬───────────────────────────────────────┘
                              ▼
┌───────────────────────────── Stage 1 ─────────────────────────────┐
│ Layman → article-section mapping (the model decides)                │
│ • 126 layman phrases, 19 mappings, 156 synonyms (Kannada for the   │
│   top phrases) map everyday wording to legal terms.                 │
│ • One Laya typed decision per issue: the model picks one option     │
│   and the pipeline records the option AND its probabilities.        │
│ • Issues: maintenance, Stridhan, custody, residence, divorce,      │
│   violence/protection, birth certificate, procedure, quantum,       │
│   court/forum, demand, safety, fact.                                │
└─────────────────────────────┬───────────────────────────────────────┘
                              ▼
┌───────────────────────────── Stage 2 ─────────────────────────────┐
│ Recheck + interconnection (the graph decides)                       │
│ • 121 recheck rules across 16 sections.                             │
│ • Divorce gate first: HMA ss.13/13B fire ONLY when divorce is       │
│   actually asked.                                                   │
│ • HMA s.24 dropped with no proceeding pending; HMA s.25 dropped     │
│   with no decree; custody to exactly one primary route; Stridhan   │
│   co-fires civil return + BNS s.316; residence fires PWDVA         │
│   ss.17+18+19 together; quantum is always escalated, never          │
│   invented.                                                         │
│ • D2 gate (HMA s.27): DROP (do not escalate) when no proceeding is  │
│   pending or being filed — see ground-truth/.                       │
│ • Forbidden mappings (6) are checked BEFORE the recheck and again   │
│   after it; any hit is a failure, not a warning.                    │
└─────────────────────────────┬───────────────────────────────────────┘
                              ▼
        Exact section set + court + escalate?  (+ per-question latency)
```

### The decision graph

| Version | File | Sections | Nodes | Edges | Status |
|---|---|---|---|---|---|
| v1 | `graph/laya-crpc-bns-section-decision-tree-v1.json` | — | — | — | Superseded |
| v2 | `graph/laya-crpc-bns-section-decision-tree-v2.json` | 32 | 46 | 77 | Previous live version |
| **v3** | `graph/laya-crpc-bns-section-decision-tree-v3.json` | **34** | **48** | **79** | **Current — used by the v6 notebook** |

v3 = v2 + the D2 gate patch applied + two new sections: `hma-9` (HMA s.9,
restitution of conjugal rights — for bank question B-018) and `pwdva-22`
(PWDVA s.22, compensation orders — for B-019). Full change log:
`graph/graph-v3-change-log.md`. Each section entry carries all 14 schema fields
plus a choice-type `laya_question`.

Graph-walk test (graph logic simulation, NOT live Laya): v1 15/34 → v2 33/34;
Kannada 0/5 → 5/5.

### Evidence gates (the v5 precision fixes — why v5 went 10/16 → 16/16)

1. **Evidence gates** — new facts `money_fact` / `gold_fact`; maintenance and
   Stridhan fire only when the fact is true (removed 8 false positives).
2. **Custody gate** — custody fires only on an explicit who-gets-the-child clause.
3. **Single-issue guard** — when exactly one issue clears, other issues need a
   lift ≥ 0.80 to fire.
4. **H14 exclusive primary route** — proceeding pending → HMA s.26 only, GWA dropped.

All four are implemented in the notebooks (Cells 6–7 of v5/v6), not as a
standalone library — see `src/README.md`.

### The notebook harness

The live pipeline currently lives in the Colab notebooks (`notebooks/`), built
by the deterministic builder scripts in `src/` (re-running a builder reproduces
its notebook byte-identically — verified by SHA-256). Each notebook:

1. installs pinned deps, 2. inspects the `laya` API, 3. downloads + loads the
   classic checkpoint (with the Vega guard), 4. uploads + hash-verifies the graph
   and the test files, 5. runs Stage 1 typed decisions per question, 6. runs the
   Stage 2 graph recheck, 7. scores exact-match / precision / recall / court /
   escalates / forbidden / silent / model errors, and 8. downloads result JSONs.

**Frozen-file discipline (non-negotiable):** the graph, ground truth, brutal
bank and sealed sets are frozen with SHA-256 hashes. The notebook asserts the
hashes at load. Never edit a frozen file to make a run pass — if a hash fails,
stop and report.

---

## 4. How to run it

### The 16-question regression (fast check, ~15–20 min on CPU)

1. Colab → upload `notebooks/live-laya-colab-test-v5-precision.ipynb`
   (live copy: https://colab.research.google.com/drive/1WkA_j2NvB_-fiUdGbcoViFrjpA6oZDN-).
2. Runtime → Run all. Upload `graph/laya-crpc-bns-section-decision-tree-v2.json`
   when Cell 5 asks (v5 uses v2; v6 uses v3).
3. Expected: **16/16 exact** under the corrected ground truth (see §5).

### The full brutal backtest (the real test, ~4 h on CPU)

Follow `docs/brutal-v6-build-report.md` §4 (the live-run sheet) exactly:

1. Colab → upload `notebooks/live-laya-colab-test-v6-brutal.ipynb`.
   Do NOT create a new notebook or edit its code.
2. Runtime → Run all. Cells 1–4: environment, install, API inspect, model load.
3. Cell 5 → upload graph v3. Must print the `(34, 48, 79)` assert PASS and SHA
   `67bf2b04…`. If not, STOP.
4. Cell 5b → upload the frozen bank. Must verify SHA `934a2b22…` and 230 questions.
5. Cells 6–8: 16-question regression (expected 16/16 under the re-base — if not,
   record it and continue; do not edit anything).
6. Cells 9–18: batches B1–B10 in order (B1–B9: 25 each, B10: 5).
   **No tuning between batches.** Each batch cell saves + downloads its
   per-batch JSON immediately — download each file as it lands.
7. Cells 19–21: sealed sets (upload `sealed-fresh-20.json` +
   `sealed-kannada-8.json` at Cell 19, verify SHAs, then run).
8. Cell 22 (final): cumulative scoring + pass/fail. Download the final JSON and
   the regression JSON, and file them under `results/`.

### Rebuilding a notebook

```bash
python3 src/build_laya_v6_brutal.py   # regenerates notebooks/live-laya-colab-test-v6-brutal.ipynb
```

Re-running a builder must reproduce the notebook byte-identically (same SHA-256);
if it does not, the builder or the notebook was edited — stop and investigate.

---

## 5. Ground truth and the HMA 27 settlement

- **Current ground truth:** `ground-truth/ground-truth-v2-hma27-A.json` —
  **53 sections** (was 57), SHA-256
  `87818b1b659583bf06a25280a6b53dabedf65f29cab99058f02b8ed31c9ac97e`.
  Erratum: `ground-truth/ground-truth-v2-erratum.md`.
- **What changed (D1 Option A, decided 2026-11-27):** HMA s.27 was REMOVED from
  K0, H3, H10, H15 with no replacement. Verified against the judgment
  *Astha Thakur v. Dhananjay Kanwar*, FAO (FC) No. 29 of 2022, HP High Court,
  decided 31 Dec 2025 (2025:HHC:46178): the s.27 application there was filed
  **during the divorce petition's pendency**, not freestanding — so a freestanding
  s.27 label in the ground truth was wrong. Full report:
  `ground-truth/hma27-settlement-report.md`.
- **D2 gate (ships only with D1, never alone):** `ground-truth/hma27-D2-gate.patch`
  (SHA-256 `6349c922…`) — R-HMA27-04 escalate → drop; the "alternatively…" limb
  deleted; co-fire rule + BNS 316 exclusion amended; new frozen fact
  `being_filed` (True only on a stated / will-file / instructed-filing statement;
  "I want a divorce" does not count).
- **Effect:** the v3/v4r/v5 live runs were scored under the OLD ground truth and
  are invalidated as live results under the corrected GT; the re-base (offline
  estimate, NOT a live result) is v4r 10/16 and v5 16/16 with D2. The next live
  run must use the corrected GT — that is what the v6 notebook does.
- **Sealed sets were NOT touched by D1-A** — they still carry pre-D1-A HMA 27
  (F8/F9/F10/F16, KN3); scored as frozen with GT-rule notes, never edited.

---

## 6. Scoring — the frozen rating formula

Full definition: `docs/laya-10-10-gate-definition.md`. Do not change it without a
signed amendment (one is already prepared but NOT applied: G2 fresh set 16 → 20,
see `docs/brutal-v6-build-report.md` §8).

```
Rating = 10 × [0.60·E + 0.15·Rm + 0.10·Pm + 0.075·C + 0.075·S] − 0.5·Fb − 1.0·Fp
  E  = exact / 16        Rm = mean recall       Pm = mean precision
  C  = court / 16        S  = escalates / 16
  Fb = forbidden-before-recheck count   Fp = prose-forbidden count
Clamped to [0, 10], rounded to 1 decimal.
```

**Caps:** Fp ≥ 1 → ≤ 5.0; Fb ≥ 1 → ≤ 9.0; prose not measured → ≤ 9.0; fresh
held-out not run/passed → ≤ 9.0; Kannada not run/passed → ≤ 9.0; no confirmation
re-run → ≤ 9.0; ≥ 3 model errors → ≤ 5.0. **10/10 additionally requires every
gate row to pass** (16/16 + sealed fresh 20/20 + Kannada 8/8 + prose renderer +
confirmation re-run).

**Brutal-230 pass bar** (`docs/brutal-test-200-plan.md` §3.2): ≥ 200/230 exact,
micro-F1 ≥ 0.95, court and escalates ≥ 200, zero silent / forbidden / model
errors, no category below 75%.

**Statistics honesty:** even 230/230 proves only ~98.4% at 95% confidence, not
99% (~300 failure-free trials would be needed for a 99% claim).

---

## 7. Live results so far (measured in Colab, CPU, laya 0.5.5)

| Run | Date (IST) | Notebook | Exact | Micro-F1 | Court | Escalates | Rating (frozen formula) |
|---|---|---|---|---|---|---|---|
| v1 | 2026-11-26 | v1 | 5/16 | 0.510 | 10/16 | 11/16 | **3.3/10** |
| v3 | 2026-11-26 | v3-empty5 | 5/16 | 0.767 | 11/16 | 14/16 | **5.0/10** |
| v4r | 2026-11-27 | v4r-residence-only | 10/16 | 0.905 | 13/16 | 14/16 | **7.3/10** |
| **v5** | **2026-11-27** | **v5-precision** | **16/16** | **1.000** | **16/16** | **12/16** | **9.8 raw → capped 9.0/10** |
| v6 brutal | in progress | v6-brutal | — | — | — | — | — |

Result files: `results/live-laya-colab-results-v{1,3,4r,5}.json/.md`.
Live notebook copies: v1 https://colab.research.google.com/drive/1pY2WJAyN0vyEvk462prTeTswROQSLnTa ·
v3 https://colab.research.google.com/drive/1vXB7ckTFKhscsHH1zbVdKV13ovGpnntr ·
v4r https://colab.research.google.com/drive/1GcSvGZbluEn4UsqkgYm-MoQYtnLE4bgK ·
v5 https://colab.research.google.com/drive/1WkA_j2NvB_-fiUdGbcoViFrjpA6oZDN- ·
v6 https://colab.research.google.com/drive/1kA784vVpU87S34og9CpuQcRvUPTj8yKa

### Honest limits — do not soften these

- **v5's 16/16 is an oracle ceiling, not generalisation proof.** The evidence
  gates run on hand-annotated facts, and the 16 questions are now a frozen
  regression set. The brutal 230 is the first real test.
- **The v5 fixes mostly do not generalise as shipped** (custody regex overfit,
  guard margin 0.0105, H1 knife-edge 0.0052, divorce-gate sub-choice wrong 8/9).
  See `docs/v6-deep-dive-report.md`.
- **Escalates fell 14/16 → 12/16 in v5** (H2, H4, H7, H15) because the false
  maintenance fires that carried the quantum boilerplate are now gated out.
- **Latency gate FAILS on CPU:** v5 mean 61.93 s/question (max 138.2 s) vs the
  ≤ 15 s budget. Only a recorded T4 GPU run can pass it; sub-second
  classification is not achievable with this model/setup.
- **v6 brutal ceiling is 228/230, not 230/230:** B-018 (`hma-9`) and B-019
  (`pwdva-22`) are guaranteed misses — graph v3 adds only Stage-2 leaf nodes;
  no Stage 1 route emits them yet.
- **Known scoring gaps in v6:** `fact` kind (44 uses; 7 fact-only questions are
  guaranteed misses), `procedure` non-birth branches (30), `court` forum-ask (6),
  `demand` (B-010/B-135), safety (B-108). Recorded, never silently mapped to True.
- **Pre-existing graph defects (v2, untouched):** 3 edges point at non-nodes
  (`escalate_clarify`, `bns-316`, `escalate_demand_first`) and a wrong id
  (`hmga-6` in bnss-144's related_sections; real id `hmga-1956-s6`).
- **Sealed maintenance-only court scores will show systematic misses** (sealed GT
  expects Family Court; the pipeline follows the 16-set Magistrate convention).
- **ChatGPT's Sukhdev Singh v. Sukhbir Kaur (Feb 2025) citation for HMA 25 is
  unverified — verify before citing.** Both model consultations (Gemini + ChatGPT)
  agree the gates are an oracle upper bound; their summaries are in `docs/`.

---

## 8. Repository layout

```
laya-family-law/
├── README.md                     # this file — start here
├── .gitignore                    # model weights + caches are never committed
├── graph/                        # the decision graph (the heart of the system)
│   ├── laya-crpc-bns-section-decision-tree-v1.json
│   ├── laya-crpc-bns-section-decision-tree-v2.json   # 32 sections / 46 nodes / 77 edges
│   ├── laya-crpc-bns-section-decision-tree-v3.json   # 34 / 48 / 79 — CURRENT
│   ├── graph-v3-change-log.md
│   ├── lanes/                    # per-issue lane outputs (custody, maintenance, procedure, residence, stridhan)
│   └── v2-lanes/                 # v2 build lanes: phrasebook, Stage-1 mapping, Stage-2 recheck, adversarial tests
├── ground-truth/                 # frozen ground truth + the HMA 27 settlement
│   ├── ground-truth-v2-hma27-A.json                 # 53 sections, SHA 87818b1b…
│   ├── ground-truth-v2-erratum.md
│   ├── hma27-D2-gate.patch / hma27-D2-gate-validation.md
│   ├── hma27-rebase-report.md / hma27-settlement-report.md
├── test-bank/                    # the brutal test bank (frozen — never edit)
│   ├── brutal-bank-v1-frozen.json                   # 230 questions, SHA 934a2b22…
│   ├── brutal-bank-v1-draft.json
│   ├── brutal-bank-freeze-note.md / brutal-bank-second-rater-report.md / brutal-bank-adjudication.md
│   └── sealed/                   # sealed held-out sets: fresh-20 + Kannada-8 + freeze note
├── notebooks/                    # live Colab notebooks v1–v6 (the pipeline lives here)
├── src/                          # deterministic notebook builders + graph merge/replay helpers
├── docs/                         # gate definition, 10/10 plan, v5/v6 reports, consultations, designs
└── results/                      # live Colab result JSONs + summaries (v1, v3, v4r, v5; v6 to come)
```

**Frozen-file hashes (verify before any run):**

| File | SHA-256 |
|---|---|
| `graph/laya-crpc-bns-section-decision-tree-v3.json` | `67bf2b04ca946f7c7fa3062068e01ce051fbce8f4d740c281afe6fff841c34a5` |
| `graph/laya-crpc-bns-section-decision-tree-v2.json` | `c7e095ad185242e9360d8b9f180fefff894f5677b52d188174413a32a2704255` |
| `ground-truth/ground-truth-v2-hma27-A.json` | `87818b1b659583bf06a25280a6b53dabedf65f29cab99058f02b8ed31c9ac97e` |
| `test-bank/brutal-bank-v1-frozen.json` | `934a2b2265ac137c96939e1fbeca3682a037010e42f972bfd459c2fcac4ec717` |
| `test-bank/sealed/sealed-fresh-20.json` | `1d8b5dc376e711c3ac6ead4424bb2d8ce52b07552b9a533ad86e0616dbcf8837` |
| `test-bank/sealed/sealed-kannada-8.json` | `2f652af1123a22441cc4158ddf480ef0981aa923858bbcb9dc3622f5e5c25853` |
| `notebooks/live-laya-colab-test-v6-brutal.ipynb` | `d6ee579534b5f2ac0b836f834954afe73fd5480d0da7a7a9fc5bec6e2461ff98` |

**NOT in this repo (deliberately):** the 808 MB model weights
(`PIXMELT/laya` snapshot — fetch as in §1); the original retest evidence PDFs
(~40 MB of screenshot-proof PDFs — binary, kept locally by the owner).

---

## 9. Pending tasks, end to end

Every item states its honest status. **Missing ≠ done. In progress ≠ done.**

### P0 — The brutal backtest (the accuracy number for integration)

| # | Task | Status |
|---|---|---|
| P0.1 | **Brutal 230 live Colab run** — v6 notebook, 10 batches (B1–B9 of 25, B10 of 5), no tuning between batches; per-batch JSONs filed in `results/` as they land | **IN PROGRESS (live since 2026-11-27 ~10:56 IST, ~4 h CPU)** |
| P0.2 | 16-question regression under corrected GT (Cell 8 of the v6 notebook) — expected 16/16 per the offline re-base | IN PROGRESS (same run, Cell 8) |
| P0.3 | Sealed fresh-20 live score (Cell 20) — measured number only until the G2 amendment (16 → 20) is signed | IN PROGRESS (same run, Cell 20) |
| P0.4 | Sealed Kannada-8 live score (Cell 21) | IN PROGRESS (same run, Cell 21) |
| P0.5 | Per-question latency for every question + G14 verdict (mean ≤ 15 s, max ≤ 30 s) | IN PROGRESS — **expected FAIL on CPU** (v5 mean 61.93 s) |
| P0.6 | Final cumulative scoring + pass/fail vs the brutal pass bar (§6) + Wilson interval + brutal rating (capped 9.0, Fp NOT MEASURED) | WAITING on P0.1 |
| P0.7 | **Confirmation re-run** — the full gate a second time, zero code changes, frozen hashes | PLANNED, NOT RUN (only after P0.6) |
| P0.8 | Gate-row pass/fail table for every row G1–G16 (see `docs/brutal-v6-build-report.md` §7) | IN PROGRESS (produced by the v6 notebook's final cell) |

### P1 — Missing pieces that cap the score

| # | Task | Status |
|---|---|---|
| P1.1 | **Prose renderer** — turns the classified payload into user-facing prose without inventing law (designs exist: `docs/prose-renderer-design.md`, `docs/v6-lane4-prose-latency.md`, ChatGPT "Approved Legal Payload", Gemini "Plan-Realize-Verify"). Until it exists and is measured, Fp is NOT MEASURED and the rating is capped at 9.0 | **MISSING — NOT BUILT** |
| P1.2 | **Automatic Stage-0 fact extraction** — replaces the hand-annotated oracle facts with a real extractor (10 atomic facts, three-state supported/contradicted/unknown, evidence spans; cheapest path per ChatGPT: frozen-encoder heads on the 421M ModernBERT; per Gemini: ABSENT/BACKGROUND/OPERATIVE frame + soft gating). Needs 200–400 labelled questions in scenario families | **MISSING — NOT BUILT** (agreed next build after the brutal run) |
| P1.3 | **Typed escalations (D5/D9)** — replace the boolean escalate with typed kinds (custody, residence, recovery, procedure, fact, …) to lift escalates from 12/16 toward 16/16. Designed in `docs/v6-deep-dive-report.md` + both model consultations; the v6 notebook already scores BOTH boolean and kinds | DESIGNED, NOT BUILT |
| P1.4 | **T4 GPU run for the latency gate (G14)** — needs owner approval; T4 timings are unverified, no T4 numbers claimed | NOT RUN — needs approval |
| P1.5 | **Stage 1 routes for `hma-9` and `pwdva-22`** — new issue prompt + Stage-2 route so B-018/B-019 can be answered at all (raises the brutal ceiling from 228/230 to 230/230) | MISSING — needs a pipeline change |

### P2 — Verification and correctness

| # | Task | Status |
|---|---|---|
| P2.1 | Kannada C13 native-speaker confirmation (second rater verified at working-reading level only) | OPEN |
| P2.2 | G2 amendment sign-off (fresh set 16 → 20; prepared text in `docs/brutal-v6-build-report.md` §8 — gate file NOT rewritten until signed; never trim 20 → 16) | PREPARED, NOT SIGNED |
| P2.3 | Fix the 3 dangling graph edges + wrong `hmga-6` id (§7) | OPEN (recorded, untouched in v3) |
| P2.4 | Re-verify the un-verified citations (ChatGPT's Sukhdev Singh v. Sukhbir Kaur, Feb 2025, for HMA 25; Balkrishna / Babulal / Krishna Kumar Gupta for HMA 27) before citing | OPEN |
| P2.5 | Verify the HMA 27 judgment paras 3–13, 15–17, 19 in full (settlement relied on the operative finding) | OPEN |
| P2.6 | B-022 / hma-25 flagged as thinnest use in the bank (kept by both raters + adjudicator — watch it in the brutal results) | OPEN — watch item |

### P3 — After the brutal run

| # | Task | Status |
|---|---|---|
| P3.1 | File all v6 batch + final result JSONs in `results/` and update the §7 table with the measured brutal numbers | WAITING on P0.1 |
| P3.2 | Fix whatever the brutal run exposes — one fix round, then a fresh confirmation re-run (P0.7). Never tune between batches of the same run | WAITING on P0.6 |
| P3.3 | Generalisation fixes from the v6 deep dive (custody-regex overfit, guard margin, H1 knife-edge, divorce-gate sub-choice) | DESIGNED in `docs/v6-deep-dive-report.md`, NOT BUILT |
| P3.4 | Standalone pipeline source (today the pipeline lives only in the notebooks + builders; `src/` has no runnable classifier yet) | MISSING — see `src/README.md` |

---

## 10. Working rules for this repo

1. **Frozen files are frozen.** Graph, ground truth, brutal bank, sealed sets —
   verify by SHA-256 before use, never edit to make a run pass.
2. **Live numbers only.** A predicted, offline, or re-based number is labelled
   exactly that. A live number names its notebook, date, runtime and result file.
3. **No tuning between batches** of a scored run. A failure found in batch 2 is
   NOT fixed before batch 3.
4. **Missing is reported as missing**, never faked, never silently mapped to True.
5. **Second-opinion discipline:** anything an outside model suggests must be
   checked against this repo's own numbers before use; no private material goes
   into outside models.
6. **Results land in `results/`** with the notebook version, date and runtime in
   the filename, and the §7 table in this README is updated in the same commit.

---

## 11. Background reading

- Fresh retest that started this work (Nov 2026): `docs/test-report.md`,
  `docs/test-report-v2-layman.md`
- 10/10 plan: `docs/laya-10-10-exact-plan.md` · Gate: `docs/laya-10-10-gate-definition.md`
- v5 precision merge: `docs/v5-precision-report.md` · v6 deep dive: `docs/v6-deep-dive-report.md`
- Brutal test design: `docs/brutal-test-200-plan.md` · v6 build: `docs/brutal-v6-build-report.md`
- Model consultations: `docs/chatgpt-v6-consultation.md`, `docs/gemini-v6-consultation.md`
- The cancelled LLaMA head-to-head: `docs/backtest-laya-vs-llama8b.md`
  (owner cancelled it 2026-11-26 — only Laya inference is tested now)

## 12. Licence

No licence file is included yet. All rights reserved by the owner unless a
licence is added later.
