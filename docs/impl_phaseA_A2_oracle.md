# Phase A gate A2 — Graph-oracle harness

- **Lane:** A (implementation swarm)
- **Date:** 2026-11-27
- **Script:** `scripts/run_graph_oracle.py` (pure python, no torch)
- **Verdict: OPEN (harness built; full oracle blocked on human annotation)**
  — the smoke test that could run, ran in degraded mode: **9/16 exact**.

## The harness

`scripts/run_graph_oracle.py` implements the four configurations
(ChatGPT §4.1, GPT-RERUN §10 — P0):

| Config | Issues | Facts | Status here |
|---|---|---|---|
| GG | gold | gold | ran in DEGRADED mode (see below) |
| GP | gold | predicted | NOT RUN — no prediction file, no gold issues |
| PG | predicted | gold | NOT RUN — same |
| PP | predicted | predicted | NOT RUN — same |

Usage:

```bash
# Degraded smoke test on what exists today (16-Q legacy GT):
python3 scripts/run_graph_oracle.py --legacy-16q \
    --gold ground-truth/ground-truth-v2-hma27-A.json \
    --gold-provenance independent
# Full four-config oracle on an independently annotated dev set:
python3 scripts/run_graph_oracle.py --gold dev-gold.json \
    --pred-file dev-predictions.json --gold-provenance independent
```

Exit codes: 0 = GG 100% on independent gold; 1 = GG < 100% (ceiling
measured); 2 = usage/environment error; 3 = tautology / unverified
provenance — no pass may be claimed.

## Tautology check (GPT-RERUN §10, binding)

The harness requires `--gold-provenance` (`independent` /
`graph-derived` / `unknown`) and ALSO scans the gold file for
graph-generation markers (`generated_by` / `source` / `generator` /
`provenance` fields naming Graph v4). If provenance is
`graph-derived` — or a marker says so — it prints `TAUTOLOGY` and
exits 3, refusing to claim a pass. If provenance is `unknown` and GG
is 100%, it exits 3 as well (a 100% oracle on unverified labels proves
nothing). Verified on this VM:

```bash
python3 scripts/run_graph_oracle.py --legacy-16q \
    --gold ground-truth/ground-truth-v2-hma27-A.json \
    --gold-provenance graph-derived
# TAUTOLOGY: ... Refusing to score a pass (exit 3).  -> exit 3 ✓
```

Two related guards:

- The harness **refuses files without an explicit per-record
  `expected_sections`** — which is why the synthetic corpus can never
  be gold here: `data/synthetic_v7_1/validation.jsonl` carries no
  `expected_sections`, and the only way to derive expected sections
  from it (`tests/recall_eval.py::expected_sections`) runs Graph v4
  on the gold labels — graph-derived by construction. The frozen-split
  261/500 is therefore NOT an oracle result; it measures extraction
  against graph-generated labels.
- The 16-Q `gt_ids` themselves are independently annotated (rater GT
  from Colab Cell 6, v1 GT — not graph output), so the degraded run
  below is not tautological on the section side. What is missing is
  independent gold *Stage-1 inputs*, not independent sections.

## Does the 16-Q GT carry gold issues/facts? NO

`ground-truth/ground-truth-v2-hma27-A.json` (16 questions) has, per
question: `id`, `question`, `gt_sections`, `gt_ids`, `gt_court`,
`gt_escalates`, `gt_escalation_kinds`, `facts`, `gt_notes`. The
`facts` dict is a **legacy 8-key** annotation, present on all 16:

`divorce_asked`, `proceeding_pending`, `decree`, `demand_made`,
`violence`, `residence_claim`, `money_fact`, `gold_fact` (16/16 each).

There is **no `issues` field, no `enums` field, no `being_filed`,
no `custody_claim`, no `birth_cert_asked`, no `joint_property_claim`,
no claimant sex/role** — on any of the 16. The full oracle (GG with
gold issues + full 28 facts + enums) therefore cannot run on this
file.

## Degraded smoke test — 9/16 exact (a lower bound, not the oracle)

Command (exit 1, as designed — see caveat below):

```bash
python3 scripts/run_graph_oracle.py --legacy-16q \
    --gold ground-truth/ground-truth-v2-hma27-A.json \
    --gold-provenance independent
# GG gold/gold: 9/16 exact (56.2%)
```

Legacy mapping used: `gold_fact` → `stridhan_claim`,
`proceeding_pending` → `proceeding_pending_hma`; booleans →
`supported`/`denied`; `in_scope` = supported; sex/role = unknown;
issues = {} (absent). All 7 misses are missing sections, 0 extra
sections (no false positives):

| Miss | Missing sections | Missing input that would trigger them |
|---|---|---|
| K0 | gwa-1890, hmga-1956-s6, welfare-principle, pwdva-18 | `custody_claim` (custody triple); violence/coercive fact for pwdva-18 |
| H2 | gwa-1890, hmga-1956-s6, welfare-principle | `custody_claim` |
| H4 | pwdva-18 | violence/coercive fact (legacy `violence` is false here) |
| H5 | gwa-1890, hmga-1956-s6, welfare-principle | `custody_claim` |
| H6 | pwdva-18 | violence/coercive fact |
| H7 | births-deaths-act-1969 | `birth_cert_asked` (not a legacy key) |
| H14 | hma-26, hmga-1956-s6, welfare-principle | `custody_claim` + `being_filed`/pending-HMA context |

Interpretation: the 9/16 is a **missing-input artifact**, not a
measured graph ceiling. Every miss traces to a trigger the legacy
file cannot express. In particular the custody triple
(gwa-1890 + hmga-1956-s6 + welfare-principle) is 3 of the 7 misses'
core — it needs `custody_claim`, which no legacy key carries. The
harness exit code 1 in degraded mode must NOT be quoted as "the
oracle fails / the graph caps at 56%". It says: *with facts-only
legacy input, the graph recovers 9/16; the other 7 need gold issues
that do not exist yet.*

## What is OPEN (human gate)

1. **Independent annotation of gold Stage-1 inputs** for a dev set:
   gold issues (11) + gold facts (28) + gold enums for the 16-Q
   (re-annotation of the existing 16, by a human annotator who has
   not seen classifier predictions), or — better, per the plan — a
   fresh independent dev set (Phase D's 300-item holdout is the same
   shape of work; the oracle dev set can be its first slice).
   Until then GP/PG/PP cannot run and GG cannot be claimed.
2. **Annotator provenance must be recorded** in the gold file
   (`provenance` field: who annotated, when, from what source) so
   the harness's tautology check has something real to verify.
3. **Do not "complete" the 16-Q gold by running the graph** (that
   would be the tautology this gate exists to prevent) and do not
   use the evidence-mode extractor's outputs as "gold" either —
   they are predictions, not annotation.

## Lane B / coordinator notes

- The oracle's GG/PG split is the diagnostic that separates "Stage 1
  is wrong" from "the graph cannot express the answer". Once gold
  inputs exist, run all four configs before any further graph
  discussion: if GG is 100% but PP is low, the problem is Stage 1;
  if GG is < 100%, record the ceiling per plan §9 risk 1 and
  re-scope — do not compensate by distorting fact predictions.
- Known interaction with A1: 21 graph keys have no classifier
  producer, so a PG/PP run on classifier predictions will
  systematically miss the branches those keys gate
  (`interim_only_asked`, post-order split facts, `*_negated`). The
  oracle will show that as a Stage-1 gap; the fix belongs in the
  schema/adapter (A1), not in the oracle.
