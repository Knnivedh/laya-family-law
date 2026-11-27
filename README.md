# LAYA — Indian Family-Law Classification System

> **A fully interconnected decision graph over the Laya language model that classifies
> complex Indian family-law questions (in plain layman wording, English or Kannada)
> into the exact article / section set that applies — in a fraction of a second
> of model time per decision, with a full legal recheck before anything is returned.**

**Status — read this first (2026-11-27, post-v6 brutal run):** on the **16-question
dev regression set** (`v2` D1-A GT), the live v6 pipeline holds **`16/16` exact
(`13/16` court, `16/16` esc-bool, `11/16` esc-kinds, `9.9` raw → capped `9.0/10`)**.
On the **230-question out-of-sample brutal bank** (run live locally on RTX 5050 GPU),
`v6-brutal` scored **`79/230` (`34.3%`) exact**, **micro-F1 `0.629`**, **`75` silent**,
**`5` pre-recheck forbidden (`Fb`)**, **`1.9/10` (`FAIL`)**, plus **`5/20` sealed fresh**
and **`1/8` sealed Kannada** (`0.43s/Q` mean GPU latency). All `v6-brutal` JSON/MD outputs
are now filed in `results/`, **Graph v4** (`34/66/99`, 0 dangling edges) and **Prose
Renderer v2** (`src/laya_prose_v2.py`, `246/246` `Fp=0`) are built & unit-tested, and
the full updated problems/tasks ledger lives in §9 and
`docs/pending-tasks-and-problems-ledger.md`. Nothing in this README claims an unmeasured
result; where a piece is missing or verified only on a probe/subset, it says so.

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
| v2 | `graph/laya-crpc-bns-section-decision-tree-v2.json` | 32 | 46 | 77 | Previous live version (frozen) |
| v3 | `graph/laya-crpc-bns-section-decision-tree-v3.json` | 34 | 48 | 79 | Frozen baseline used by the v6 notebook |
| **v4** | **`graph/laya-crpc-bns-section-decision-tree-v4.json`** | **34** | **66** | **99** | **Built & verified (`tests/test_graph_v4.py`); fixes all v3 dangling edges/typos & specifies Stage 2 v4 routing (`docs/v4-decision-graph-architecture.md`) — pending v7 runtime integration** |

v3 = v2 + the D2 gate patch applied + `hma-9` and `pwdva-22` leaf stubs (`graph/graph-v3-change-log.md`).
v4 = v3 built deterministically by `src/build_graph_v4.py` (`graph/graph-v4-change-log.md`): repairs all 3 pre-existing dangling edges, fixes `'hmga-6' -> 'hmga-1956-s6'`, canonicalizes all `related_sections` and `laya_question` fields, and adds `+18` nodes / `+20` edges for `hma-9`, `pwdva-22`, `hma-13b`, `hma-25` settlements, `hma-27` joint property, `claimant-applicability-gate` (`C8` male/parent), `pwdva-17/19` vs `18` independence, and empty-GT leaves.

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

## 7. Live results so far (Colab CPU v1–v5 & Local RTX 5050 GPU v6-brutal)

| Run | Date (IST) | Notebook / Set | Exact | Micro-F1 | Court | Escalates | Latency Mean | Rating (frozen formula) |
|---|---|---|---|---|---|---|---|---|
| v1 | 2026-11-26 | v1 (`16-Q`, Colab CPU) | 5/16 | 0.510 | 10/16 | 11/16 | — | **3.3/10** |
| v3 | 2026-11-26 | v3-empty5 (`16-Q`, Colab CPU) | 5/16 | 0.767 | 11/16 | 14/16 | — | **5.0/10** |
| v4r | 2026-11-27 | v4r (`16-Q`, Colab CPU) | 10/16 | 0.905 | 13/16 | 14/16 | 57.6s | **7.3/10** |
| v5 | 2026-11-27 | v5-precision (`16-Q`, Colab CPU, old 57-sec GT) | 16/16 | 1.000 | 16/16 | 12/16 | 61.93s | **9.8 raw → capped 9.0/10** |
| v6-reg | 2026-11-27 | v6-brutal (`16-Q` `v2` D1-A GT, RTX 5050 GPU) | **16/16** | **1.000** | 13/16 | 16/16 bool (`11/16` kinds) | **0.52s** | **9.9 raw → capped 9.0/10** |
| **v6-brutal** | **2026-11-27** | **v6-brutal (`Brutal-230` frozen, RTX 5050 GPU)** | **79/230 (34.3%)** | **0.629** (`TP 225/FP 75/FN 190`) | **152/230** | **144/230 bool** (`48/230` kinds) | **0.43s** (`1.00s` max) | **1.9/10 (`FAIL`)** |
| v6-fresh | 2026-11-27 | v6-brutal (`Sealed Fresh-20`, RTX 5050 GPU) | 5/20 | 0.635 | 8/20 | 17/20 bool (`6/20` kinds) | 0.45s | **3.6/10** *(measured only)* |
| v6-kn | 2026-11-27 | v6-brutal (`Sealed Kannada-8`, RTX 5050 GPU) | 1/8 | 0.083 | 1/8 | 1/8 bool (`1/8` kinds) | 0.57s | **1.4/10** *(measured only)* |

Result files: `results/live-laya-colab-results-v{1,3,4r,5}.json/.md`, `results/live-laya-colab-results-v6-brutal-final.json`, `results/live-laya-colab-results-v6-brutal.md`, `results/live-laya-colab-results-v6-brutal-B{1..10}.json`, `results/live-laya-colab-results-v6-brutal-regression.json/.md`, and `results/live-laya-colab-results-v6-sealed-{fresh-20,kannada-8}.json`. Local RTX 5050 (`bf16`) vs Colab CPU (`v5`) matched within `mean_abs_diff = 0.002306` across all 160 raw `16-Q` prompts with `0` fired-issue diffs.
Live notebook copies: v1 https://colab.research.google.com/drive/1pY2WJAyN0vyEvk462prTeTswROQSLnTa ·
v3 https://colab.research.google.com/drive/1vXB7ckTFKhscsHH1zbVdKV13ovGpnntr ·
v4r https://colab.research.google.com/drive/1GcSvGZbluEn4UsqkgYm-MoQYtnLE4bgK ·
v5 https://colab.research.google.com/drive/1WkA_j2NvB_-fiUdGbcoViFrjpA6oZDN- ·
v6 https://colab.research.google.com/drive/1kA784vVpU87S34og9CpuQcRvUPTj8yKa

### Honest limits — measured in the live brutal run

- **v5/v6's `16/16` did NOT generalise to unseen paraphrases (`79/230 = 34.3%`, `5/20` fresh, `1/8` Kannada):**
  Out of `60` English silent (`kept=[]`) brutal questions (`75` total incl. `15` Kannada), **`35/60` already had full-text Laya `stage1_raw >= threshold`** before the v5 English regex gates zeroed them (`_CUSTODY_PATTERNS` caused `37/41` `gwa-1890` misses and `0/20` on `C5`; `money_fact` caused `17/16` `bnss-144`/`pwdva-20` misses and `0/8` on `C12`; `gold_fact` blocked all `8` `hma-27` joint flat/property items; `residence_claim` blocked `13` `pwdva-17/19` items).
- **Kannada (`C13` `1/16`, `Sealed Kannada-8` `1/8`):** English regex gates + English-only `PIXMELT/laya` missed `28/28` C13 GT sections (passing only empty `B-218`). Probe testing (`docs/v7-multilingual-prose-latency-design.md`) shows `convaiinnovations/laya` `multilingual` fails (`0/16–6/16`), whereas sentence-split `NLLB-200-distilled-600M` + generic tail-drop + `PIXMELT/laya` reaches **`14/16` (`0.949` F1, `0` silent)** on `C13`.
- **Stage 1 zero-shot plateau vs v7 Stage 0/1 training (`docs/v7-stage1-semantic-probes.md`):** Removing regex vetoes in GPU probes (`102-Q`) lifted recall to `89.3%` (`Silent=1/94`), `birth_certificate` to `1.000`, `joint_property` to `1.000`, and `custody` to `0.893`, **but** zero-shot precision capped at `0.702` (`0.786` F1) — confirming trained Stage 0/1 heads (`P1.2`) are required for `>=0.95` F1.
- **Stage 2 & Graph v3 gaps exposed (`Fb=5`, `C7/C8/C12`):** Old `stage2()` lacks `hma-13b` (`FN=5`), `hma-9` (`B-018`), `pwdva-22` (`B-019`), `hma-25` lump-sum settlements (`FN=4`), `hma-27` joint property (`FN=8`), male/parent claimant exclusions (`C8`), `pwdva-17/18/19` decoupling, and Layer A `hma-24` filtering (`Fb=5`). All structural fixes are now encoded in `graph/laya-crpc-bns-section-decision-tree-v4.json` and `docs/v4-decision-graph-architecture.md`.
- **Latency (`G14`):** **Passes cleanly on RTX 5050 GPU** (`0.43s/Q` mean, `1.00s` max on `v6-brutal`; `0.303s/Q` mean warmed `fp16` `predict_batch`), **FAILS on CPU** (`61.93s/Q` Colab CPU `v5`; `17.8s/Q` local 4Q CPU sample). Colab T4 `fp16` timing remains unverified.
- **Post-D1-A 16-Q & Brutal GT splits (`D-V4-1..4`):** `16-Q` `H3/H10/H15` kept `['Family Court', 'Magistrate']` despite D1-A leaving `bns-316` (`13/16` court), and `16-Q` omitted `safety` (`11/16` kinds). `brutal-bank-v1-frozen` omits `hmga-1956-s6` & `welfare-principle` (`5` pure vocab misses; `84/230` without them).
- **Pre-existing v2/v3 graph defects kept intact inside frozen `v2`/`v3` files** and **fixed in `graph/laya-crpc-bns-section-decision-tree-v4.json`**.
- **Prose renderer & doc bug fix:** Cell 9 prose wasn't wired into `v6` (`9.0` cap remains); a deterministic `Fp=0` renderer + verifier (`src/laya_prose_v2.py`) is now built & unit-tested (`246/246`, fixing a pre-D1-A `HMA s.27` leak found in `docs/v6-lane4-prose-latency.md` §2.3.3).
- **ChatGPT's Sukhdev Singh v. Sukhbir Kaur (Feb 2025) citation for HMA 25 remains unverified.**

---

## 8. Repository layout

```
laya-family-law/
├── README.md                     # this file — start here
├── .gitignore                    # model weights + caches are never committed
├── graph/                        # the decision graph (the heart of the system)
│   ├── laya-crpc-bns-section-decision-tree-v1.json
│   ├── laya-crpc-bns-section-decision-tree-v2.json   # 32 sections / 46 nodes / 77 edges (frozen)
│   ├── laya-crpc-bns-section-decision-tree-v3.json   # 34 / 48 / 79 (frozen baseline)
│   ├── laya-crpc-bns-section-decision-tree-v4.json   # 34 / 66 / 99 — 0 dangling edges (next live build)
│   ├── graph-v3-change-log.md / graph-v4-change-log.md
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
├── src/                          # notebook builders, Graph v4 builder, Lane 4 Prose v2, local brutal runner/analyzer
├── tests/                        # offline integrity & verification tests (test_graph_v4.py, test_prose_renderer_v2.py)
├── docs/                         # gate definition, 10/10 plans, v4/v7 blueprints, Stage 1 probes, pending ledger
└── results/                      # live result JSONs + summaries (v1, v3, v4r, v5 Colab + v6-brutal RTX 5050)
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

Every item states its verified live state (full cross-cutting audit in
[`docs/pending-tasks-and-problems-ledger.md`](docs/pending-tasks-and-problems-ledger.md)).
**Missing ≠ done. Built-in-unit-test ≠ verified end-to-end live.**

### P0 — The brutal backtest (completed locally on RTX 5050 GPU; confirmation re-run pending v7)

| # | Task | Status |
|---|---|---|
| P0.1 | **Brutal 230 live run** — v6 notebook (`B1–B10`, no tuning between batches), filed in `results/` | **DONE (RTX 5050 GPU)** — `79/230` exact (`34.3%`), micro-F1 `0.629`, `75` silent, `Fb=5`, **`1.9/10` (`FAIL`)** |
| P0.2 | 16-question regression under corrected `v2` D1-A GT (Cell 8) | **DONE** — `16/16` exact (`13/16` court, `16/16` esc-bool, `11/16` esc-kinds, `9.0/10` capped) |
| P0.3 | Sealed fresh-20 live score (Cell 20) — measured number only until G2 amendment signed | **DONE** — `5/20` exact, micro-F1 `0.635`, `8/20` court, `17/20` esc-bool, `3` silent, `Fb=1` |
| P0.4 | Sealed Kannada-8 live score (Cell 21) | **DONE** — `1/8` exact (`KN5` `hma-13`), micro-F1 `0.083`, `6` silent |
| P0.5 | Per-question latency & `G14` verdict (mean ≤ 15 s, max ≤ 30 s) | **DONE (RTX 5050 passes `0.43s/Q` mean / `1.00s` max)**; CPU fails (`17.8s/Q` local, `61.93s/Q` Colab); Colab T4 still unverified |
| P0.6 | Final cumulative scoring + pass/fail vs §6 bar + Wilson interval + filing | **DONE** (`results/live-laya-colab-results-v6-brutal-final.json` & `.md`) |
| P0.7 | **Confirmation re-run** — the full gate a second time on fixed `v7`, zero code changes, frozen hashes | **OPEN** (blocked on building `v7` fixes) |
| P0.8 | Gate-row pass/fail evaluation vs §3.2 (`11/12` checked criteria failed in v6, `prose` unmeasured) | **DONE** |

### P1 — Architecture & model upgrades to lift `1.9/10` brutal → `10/10` (`v7`)

| # | Task | Status |
|---|---|---|
| P1.1 | **Prose renderer & automated `Fp=0` check** (`G12`) | **BUILT & UNIT-TESTED** — `src/laya_prose_v2.py` + `tests/test_prose_renderer_v2.py` (`246/246` + `15/15` mutants pass, `Fp=0`, fixed `HMA s.27` leak in `v6-lane4`); **needs wiring into `v7` live notebook + blind rater audit** |
| P1.2 | **Stage 0/1 semantic fact & issue extraction** (replacing English regex vetoes that caused `35/60` English silent misses) | **PROBED ON GPU (`v1–v4`) + DESIGNED** (`docs/v7-stage1-semantic-probes.md`: cuts English silent `60 -> 1/94`, `89.3%` recall, `0.786` zero-shot F1); **head training on clean synthetic data NEEDED** to push precision `0.70 -> >=0.95` |
| P1.3 | **Graph v4 Stage 2 routing, Claimant-Sex/Role (`C8`), `PWDVA 17/18/19` split, Layer A (`Fb=0`), & 9-kind `escalate_v4`** | **GRAPH BUILT & ARCHITECTED** (`graph/laya-crpc-bns-section-decision-tree-v4.json`, `docs/v4-decision-graph-architecture.md`); **runtime Python `stage2_v4` / `court_for_v4` implementation PENDING** |
| P1.4 | **Colab T4 GPU `fp16` latency & accuracy parity run** (`G14` cloud verification) | **OPEN** — RTX 5050 GPU already passes `0.303s/Q` batched (`docs/v7-multilingual-prose-latency-design.md`); Colab T4 needs cloud verification |
| P1.5 | **Stage 1/2 routes for `hma-9`, `pwdva-22`, `hma-13b`, `hma-25` settlements, `hma-27` joint property** | **NODES WIRED IN GRAPH v4**; Stage 1/2 Python runtime + trained heads **PENDING** |
| P1.6 | **Kannada `C13` / `G3` sentence-split `NLLB + PIXMELT` bilingual routing** | **PROBED (`14/16 = 87.5%` exact, `0.949` F1, `0` silent on `C13`, `0.35s/Q`)** in `docs/v7-multilingual-prose-latency-design.md`; **integration into `v7` runtime PENDING** |

### P2 — Verification, governance & ground-truth alignment

| # | Task | Status |
|---|---|---|
| P2.1 | Kannada C13 native-speaker confirmation | OPEN |
| P2.2 | G2 amendment sign-off (`16 -> 20` fresh set) + `D-V4-1..4` (`H3/H10/H15` `16-Q` court, `16-Q` `safety` kind, brutal custody vocab `hmga-1956-s6`/`welfare-principle`, `hma-25` settlement `Fb` rule) | OPEN (documented in `docs/v4-decision-graph-architecture.md` §7) |
| P2.3 | Fix the 3 pre-existing v2/v3 dangling graph edges + `'hmga-6'` typo + non-canonical `related_sections` | **DONE in Graph v4** (`src/build_graph_v4.py`, `tests/test_graph_v4.py`); `v2`/`v3` remain untouched frozen snapshots |
| P2.4 | Independent verification of citations (*Sukhdev Singh v. Sukhbir Kaur*, *Balkrishna / Babulal / Krishna Kumar Gupta*) | OPEN |
| P2.5 | Full HMA 27 judgment paras 3–13, 15–17, 19 check | OPEN |
| P2.6 | `B-022` / `hma-25` settlement watch item (failed in `v6` due to `decree=False` Layer A veto) | DIAGNOSED; solved in Stage 2 `v4` (`lump_sum_settlement`) |

### P3 — Packaging, `v7` build & confirmation

| # | Task | Status |
|---|---|---|
| P3.1 | File all `v6-brutal` JSONs + summary into `results/` and update §7 + §9 | **DONE** |
| P3.2 | Implement full `v7` pipeline (`Stage 0/1` trained heads + `NLLB` Kannada Stage 0 + `Stage 2 v4` + `laya_prose_v2` + `predict_batch`), run live 274-Q verification + `P0.7` confirmation re-run | **NEXT BUILD MILESTONE** |
| P3.3 | Stage 1 regex-overfit / guard-margin / sub-choice generalisation fixes | PROBED (`docs/v7-stage1-semantic-probes.md`); merges into P3.2 |
| P3.4 | Standalone Python package in `src/` | **PARTIAL** — `src/build_graph_v4.py`, `src/laya_prose_v2.py`, `src/run_v6_brutal_local.py`, `src/analyze_v6_brutal.py` now in `src/` + `tests/`; full unified classifier `v7` next |

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
- 10/10 plans & blueprints: `docs/laya-10-10-exact-plan.md`, `docs/laya-10-10-gate-definition.md`,
  `docs/v4-decision-graph-architecture.md`, `docs/v7-stage1-semantic-probes.md`,
  `docs/v7-multilingual-prose-latency-design.md`, `docs/pending-tasks-and-problems-ledger.md`
- Live brutal summary & prior deep dives: `results/live-laya-colab-results-v6-brutal.md`,
  `docs/v5-precision-report.md`, `docs/v6-deep-dive-report.md`, `docs/brutal-v6-build-report.md`
- Brutal test design: `docs/brutal-test-200-plan.md`
- Model consultations: `docs/chatgpt-v6-consultation.md`, `docs/gemini-v6-consultation.md`
- The cancelled LLaMA head-to-head: `docs/backtest-laya-vs-llama8b.md`
  (owner cancelled it 2026-11-26 — only Laya inference is tested now)

## 12. Licence

No licence file is included yet. All rights reserved by the owner unless a
licence is added later.
