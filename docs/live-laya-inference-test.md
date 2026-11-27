# Live Laya inference test — Laya 421M + v2 two-stage graph
## Status: BLOCKED — NOT RUN LIVE (2026-11-26, ~22:00 IST)

**Live exact-match: NOT MEASURED — 0 of 16 attempted, 0 live runs.**
**Live precision / recall: NOT MEASURED.**
**Live forbidden mappings: NOT MEASURED.**
**No LLaMA work was done, downloaded, or compared in this run, as instructed.**
**The v2 graph file and the backtest file were NOT edited.**

Do NOT quote the earlier 16/16 as a live result. That 16/16 (backtest-laya-vs-llama8b.md §4–5)
was a deterministic graph walk, not live model inference. This file is the live attempt, and
it did not produce live scores.

---

## 1. What was asked

Run LIVE Laya inference through the v2 two-stage graph on the same 16 questions
(K0 known case + H1–H15 held-out, same ground truth as backtest-laya-vs-llama8b.md §3).
Stage 1 = one Laya choice per issue, Stage 2 = the graph recheck, drop on failure.
Score exactly like the backtest: exact section-set match, per-section precision/recall,
forbidden mappings, court correct, escalates correctly.

## 2. What was verified by plain reading (no code executed)

Model on disk, checked 2026-11-26 ~21:58–22:00 IST:
- `~/workspace/models/laya-english/` — `model.safetensors` 804 MB, `config.json`
  (model_type `laya`, architectures `LayaTypedDecisions`), `test.py` (1.9 KB),
  `rl_common.py`, `README.md`, `rl_agent_config.json`, `encoder/config.json`
  (ModernBERT-large, hidden 1024, 28 layers, vocab 50368), `tokenizer/` (tokenizer.json).
- Downloaded 2026-11-26 21:12 IST from PIXMELT/laya English snapshot (official
  convaiinnovations/laya weights had blocked with a 403).
- `rl_agent_config.json`: encoder `answerdotai/ModernBERT-large`, head_layers 2,
  max_len 512, head_max_len 192, temperatures [1.637, 1.251, 1.983].

API as written in the snapshot's `test.py` / `README.md` (plain reading only):
```python
import os
os.environ["HF_HUB_OFFLINE"] = "1"
import laya
agent = laya.load(".")   # loads this directory
result = agent.predict({"body": article}, payload)
# payload: per question {"type": "choice"|"score"|"noul",
#   "instructions": "...", "criteria": {...} or [...]}
# result["answers"][name][type] -> chosen option / score / noul probability
```
Decision model (from `rl_common.py`, plain reading): ModernBERT encoder + 2-layer
Transformer decision head; each option gets a [MASK] marker, head scores markers,
softmax over options. `build_sequence`: `[CLS] <type> instructions [SEP] [MASK] opt0
[MASK] opt1 ... [SEP] state [SEP]`.

Graph v2, checked on disk: `laya-crpc-bns-section-decision-tree-v2.json`, 419 KB,
32 sections, 46 nodes, 77 edges, two-stage design (Stage 1 layman -> legal terms ->
section; Stage 2 recheck inside the section, drop on failure).

## 3. Blocker 1 — execution-risk check on the laya PyPI package (hard stop)

When the `laya` 0.5.5 wheel was downloaded from PyPI to inspect its load API
(`/tmp/laya-pkg/laya-0.5.5-py3-none-any.whl`, 510 KB, downloaded 2026-11-26 16:29 UTC),
the runtime raised a system execution-risk check on that content. The notice
prohibits running, installing, building, testing, importing, loading or sourcing
that content, and prohibits copying it into home/config/PATH/tools, without an
explicit user go-ahead in plain words. No exception was made.

Consequence: `pip install laya` and `import laya` / `laya.load(".")` were NOT run.
No venv was created, no torch/transformers install was started. The wheel and its
extracted copy remain only in ephemeral `/tmp/laya-pkg/` and were not moved anywhere.

This is the same class of gate used before in this workspace: a flagged clone/repo
needs the user's explicit go-ahead before it is run.

**Concrete next step for this blocker:** the user must say in plain words whether
to go ahead with installing and running the `laya` PyPI package (and its
dependencies torch, transformers, safetensors, huggingface_hub, numpy, vegaml,
cryptography — see §4) to load the local 804 MB checkpoint. Until that approval
is given, no live inference step may proceed. The parent agent should ask him
directly; a subagent must not approve this itself.

## 4. Blocker 2 — API version mismatch found by plain reading (must be resolved before any run)

The PyPI metadata read (plain file view, no code run) for `laya` 0.5.5 says:

- Since 0.5.0, `laya.Agent()` loads a NEW Vega engine (frozen 0.8B reader) by
  default, NOT the ModernBERT checkpoint in the snapshot.
- The classic encoder checkpoints are reached only by naming one, e.g.
  `laya.Agent("convaiinnovations/laya")`, or `Router` / `vegaml=False`.
- Requires: `torch>=2.0.0`, `transformers>=4.48.0`, `safetensors>=0.4.0`,
  `huggingface_hub>=0.20.0`, `numpy>=1.20.0`, `vegaml>=0.18.0`, `cryptography>=41`.
  Python >=3.10 (this VM: Python 3.12.3, so the floor is met).
- The snapshot's `test.py` uses the old entry point `laya.load(".")`. It is
  NOT established that `laya.load` still exists in 0.5.5, or that 0.5.5 loads
  a local directory in the same way. Installing "latest laya" may therefore
  NOT run the snapshot's test.py as written.

Before any approved run, the loader must be pinned and verified by reading (not
running) the installed package's `load`/`Agent`/`Router` entry points, and the
run must use the classic-encoder path for the local checkpoint
(`laya.Agent("convaiinnovations/laya")`-style or equivalent local-dir load),
with `HF_HUB_OFFLINE=1`. If `laya.load` is gone in 0.5.5, an older pinned
`laya` version matching the snapshot, or a direct torch/transformers load of
`DecisionModel` from the snapshot's own `rl_common.py`, would be needed —
that choice also needs the user's go-ahead, because it runs upstream code.

## 5. Blocker 3 — RAM (would likely block a live load even if approved)

Evidence, 2026-11-26 ~21:58–22:00 IST:
- `free -m`: total 7934 MB, used 7477 MB, free 149 MB, **available 456–538 MB**,
  buff/cache ~600–635 MB, swap total 1023 MB, swap free ~585–600 MB,
  swap used ~434–448 MB, `vm.swappiness = 1`.
- Largest process: hatch daemon, RSS ~407–417 MB. No other large process was
  found (`ps aux` sorted by memory shows only the daemon, systemd, and the
  shell itself); there is nothing safe to free — the ~7 GB "used" is not
  attributable to a killable user process in this cell, and the daemon must
  not be killed. Page cache (~600 MB) is the only reclaimable memory, and the
  kernel reclaims it automatically.
- Model size: 421M params. FP32 weights = ~1.7 GB. FP16/BF16 weights = ~842 MB.
  Plus torch + transformers runtime and activations for a 512-token sequence.
  That exceeds the 456 MB available, and exceeds available + free swap
  (~1.0–1.1 GB) in FP32. FP16 might fit only with heavy swapping, and
  swappiness 1 means the kernel prefers OOM-kill over swapping.
- `torch`, `transformers`, and the `laya` package are NOT installed on this VM.
  Disk is not the blocker (143 GB free).

**Concrete next step for this blocker:** run live inference on a machine with
at least ~4 GB free RAM (16 GB total recommended for CPU inference), or free
RAM on this VM first and retry with an FP16 load, one question at a time,
with swap enabled. Do not attempt an FP32 load on this VM as-is; it is
expected to be OOM-killed.

## 6. Test plan that is ready to run once both blockers clear

Same 16 questions and ground truth as backtest-laya-vs-llama8b.md §3 (reproduced
here so the live run needs no other file):

| ID | Question (layman) | Ground-truth kept sections |
|----|-------------------|----------------------------|
| K0 | My husband left us two years ago and gives no money. I earn forty thousand a month, it is not enough for me and my eight year old daughter. My gold worth five lakh and two lakh cash my parents gave me is with my husband's family and they will not return it. They are throwing me out of the house which is in my husband's name. Who will get my daughter, how do I get my gold back, and which court do I go to? | BNSS 144, PWDVA 20, GWA 1890, HMGA s.6, WELFARE, HMA 27, BNS 316, PWDVA 17, PWDVA 18, PWDVA 19 (10) |
| H1 | My husband has not given me any money for three months. I earn fifteen thousand a month and I have two small children and no case filed anywhere. | BNSS 144, PWDVA 20 |
| H2 | Who will get my six year old son? My husband says as the father he will take him away from me. | GWA 1890, HMGA s.6, WELFARE |
| H3 | My mother gave me gold at my wedding and my in-laws kept it. I have never asked them to return it. | HMA 27, BNS 316 |
| H4 | They changed the lock and I cannot enter my house. The house is in my husband's name. | PWDVA 17, PWDVA 18, PWDVA 19 |
| H5 | I want a divorce from my husband. He beats me, I need money every month and I want my daughter to stay with me. | HMA 13, BNSS 144, PWDVA 20, PWDVA 18, GWA 1890, HMGA s.6, WELFARE |
| H6 | I do not want a divorce. I just want money every month from my husband and to stay in the house with my daughter. | BNSS 144, PWDVA 20, PWDVA 17, PWDVA 18, PWDVA 19 |
| H7 | How do I get my daughter's birth certificate? The hospital did not give us one. | Births and Deaths Act 1969 |
| H8 | I need maintenance but I do not have my husband's salary slips and I do not know what he earns. | BNSS 144, PWDVA 20 |
| H9 | How much money can I get every month from my husband? | BNSS 144, PWDVA 20 |
| H10 | My husband has my gold and I have not asked for it back yet, and he gives no money for me and my child. | HMA 27, BNS 316, BNSS 144, PWDVA 20 |
| H11 | I need money while my case is going on, but I have not filed any case yet. | BNSS 144, PWDVA 20 |
| H12 | My brother and I are fighting over our father's ancestral house. Who owns it and can I stop him selling it? | (none — no family-law section applies) |
| H13 | He beats me, throws me out of the house and gives no money for my son's school fees. | PWDVA 18, PWDVA 17, PWDVA 19, PWDVA 20, BNSS 144 |
| H14 | My divorce case is already going on in the Family Court. I want my son to stay with me and money for his school fees while the case goes on. | HMA 13, HMA 26, HMGA s.6, WELFARE, HMA 24, BNSS 144, PWDVA 20 |
| H15 | He sold my gold without asking me. The gold was given to me by my parents at my wedding. | BNS 316, HMA 27 |

Stage 1 (live, per question): one Laya `choice` question per issue —
maintenance, custody, Stridhan, residence, violence, divorce, birth certificate —
with the question text as the `body` state, exactly as the v2 graph's nodes
specify (root `root:issue-classification` first, then each selected lane's
choice nodes). Record the model's actual chosen option and its probabilities,
not a rule-based pick. A `noul` question may be used only where a node is
typed `noul` in the graph.

Stage 2 (graph recheck, deterministic, applied to the LIVE Stage-1 picks only):
divorce gate first, then prerequisite / exclusion / related-section / co-fire /
guardrail / court, in the lane-3 order. HMA 24 dropped with no proceeding
pending, HMA 25 dropped with no decree, custody to exactly one primary
(HMA 26 if a proceeding is pending, else GWA 1890), Stridhan co-fire
HMA 27 + BNS 316, residence completed as PWDVA 17+18+19, quantum always
escalated, never invented. A section failing its recheck is DROPPED with a
reason. This recheck must not be used to substitute for Stage 1: if live
Stage 1 picks nothing, the question scores as a miss, not as a graph rescue.

Scoring (per question, then aggregate): exact section-set match (yes/no),
per-section precision = TP/(TP+FP), recall = TP/(TP+FN), forbidden mappings
counted separately — (1) Rajnesh v. Neha for Stridhan, (2) Satish Chander Ahuja
for custody, (3) HMA 13/13B with no divorce asked, (4) residence called
"tenancy rights", (5) asking the user to pick the court, (6) birth certificate
under HMA — court correct (graph picks the court; H7 = Registrar, not a court;
H12 = out of scope), escalates correctly (quantum/income/school fees asked,
salary slips never demanded, written demand first for Stridhan where none was
made). Report live load time, dtype, RAM at load, and per-question latency.
Report the live numbers side by side with the walk 16/16; do not replace the
walk numbers silently.

## 7. Per-question live results

None. No live inference ran. Table intentionally left empty — no scores are
invented, and no graph-walk numbers are presented here as live numbers.

| ID | Live Stage-1 picks (model) | Live sections after Stage 2 | GT | Exact | Precision | Recall | Forbidden | Court | Escalates |
|----|---------------------------|-----------------------------|----|-------|-----------|--------|-----------|-------|-----------|
| K0–H15 | not run | not run | see §6 | not measured | not measured | not measured | not measured | not measured | not measured |

Aggregate live: exact 0/16 attempted (0 runs), micro precision/recall not
measurable, forbidden total not measurable, court 0/16 measured, escalates
0/16 measured.

## 8. What was NOT done

- No LLaMA 8B work, download, or comparison (cancelled by the user 2026-11-26
  ~21:58 IST; recorded in MEMORY.md).
- No edit to `laya-crpc-bns-section-decision-tree-v2.json` or to
  `backtest-laya-vs-llama8b.md`.
- No `pip install laya`, `pip install torch`, no venv created, no model load,
  no inference call. The only package action was `pip download --no-deps laya`
  to inspect metadata, which is the action that triggered the execution-risk
  check; that wheel was not installed, imported, or moved out of `/tmp`.
- No scores were invented and no graph walk was run as a substitute for live
  inference.

## 9. Files

- This report: `~/workspace/goals/english-family-law-chatbot-retest/files/laya-graph/live-laya-inference-test.md`
- Machine-readable results: `~/workspace/goals/english-family-law-chatbot-retest/files/laya-graph/live-laya-inference-test.json`
- Sources (unchanged): `~/workspace/models/laya-english/` (model + test.py + rl_common.py),
  `~/workspace/goals/english-family-law-chatbot-retest/files/laya-crpc-bns-section-decision-tree-v2.json`,
  `~/workspace/goals/english-family-law-chatbot-retest/files/laya-graph/backtest-laya-vs-llama8b.md`
