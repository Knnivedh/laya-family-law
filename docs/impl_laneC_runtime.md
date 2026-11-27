# Lane C — Unified Integration Runtime (`src/laya_integrated.py`)

Owner: Lane C. Contract: C1 (see `docs/impl_swarm_state.md`). Status: **done,
verified on this VM (CPU, no torch)**.

## 1. Choice: new file, not extending `src/laya_v7.py`

`src/laya_v7.py` (`assess_v7`) is the frozen v7 entry point: its modes are
`auto`/`laya`/`structured`/`evidence`, where the neural modes need PIXMELT/laya
or Qwen weights and CUDA, and its output shape is the v7 record
(`kept_ids`, `extractor_mode`, `latency_s`, …). The v7.1 contract needs
different mode semantics (`classifier`/`rule-based`/`auto` keyed on a *trained
v7.1 checkpoint*), the exact 12 C1 output keys, and clean fallback semantics.
Extending `laya_v7.py` would change a frozen file's behaviour for its existing
callers (`tests/v7_backtest.py`, `tests/recall_eval.py`). A new module leaves
every existing caller untouched and keeps the frozen files frozen: Lane C
edited **no** pipeline module and **no** frozen file.

## 2. Architecture

```
question (str)
  │
  ├─► laya_lang_normalizer.detect_script_locale
  │       → language: "en" | "kn" | "kn_roman"   (Kanglish detected, not
  │         misrouted to English)
  │
  ├─► extractor ── mode="classifier" ──► load_checkpoint(path, device="cpu")
  │       │                              + AutoTokenizer(cfg.backbone)
  │       │                              + predict_text(model, tokenizer,
  │       │                                text, cfg)   [C2, Lane B]
  │       │                              → IssueEvidence / FactEvidence
  │       │                                (sex F/M/U → female/male/unknown,
  │       │                                denied issues → negated_issues)
  │       │
  │       └─ mode="rule-based" ──► extract_v7(mode="evidence", device="cpu")
  │                                zero-model grounded evidence extractor —
  │                                the exact path behind the frozen-split
  │                                baseline 261/500 (52.2%)
  │         mode="auto": classifier iff a checkpoint file exists, else
  │         rule-based (fallback_reason set); a checkpoint that exists but
  │         cannot load also falls back in auto, and says so.
  │
  ├─► laya_v7_graph.evaluate_stage2_v7   (Graph v4 — CALLED, not edited)
  │       → kept_ids (sorted in output), court_live, escalation_kinds
  │
  └─► laya_prose_v2.render_prose        (frozen — CALLED, not edited)
          → prose (str; the INVALID_RECORD_HANDOFF text if the renderer
            reports status "error", never a fabricated section)
```

## 3. Interface (contract C1 — as built, no drift)

Python:

```python
from src.laya_integrated import run_question
run_question(text, mode="auto", checkpoint=None) -> dict
```

CLI (from the repo root; also works as `python -m src.laya_integrated`):

```
python3 src/laya_integrated.py --mode {classifier,rule-based,auto}
    [--checkpoint PATH] [--json] "question"
# no positional arg → question read from stdin
python3 src/laya_integrated.py --self-test
```

Output dict keys — exactly these 12, in this order:

| Key | Type | Notes |
|---|---|---|
| `question` | str | input, stripped |
| `language` | str | `"en"` \| `"kn"` \| `"kn_roman"` (normalizer) |
| `extractor` | str | `"classifier"` \| `"rule_based"` |
| `checkpoint` | str \| None | resolved `model.pt` path, only when the classifier actually ran |
| `fallback_reason` | str \| None | set in `auto` when the classifier did not run (no checkpoint, or load failure); `None` in explicit `rule-based` mode (no fallback happened — it was requested) and on classifier success |
| `issues` | dict | `{issue: {"intent", "confidence", "source"}}`, all 11 issues |
| `facts` | dict | `{fact: {"status", "value", "confidence", "source"}}`; `negated_issues` / `open_fact_markers` are graph inputs, not facts, and are excluded |
| `enums` | dict | `{head: {"value", "confidence"}}` for `claimant_sex` (F/M/U), `claimant_role`, `modality_time`. Rule-based: sex/role from grounded facts; `modality_time` defaults to `"present"` confidence 0.0 — explicitly "not detected", not a measured prediction |
| `sections` | list[str] | `kept_ids`, sorted |
| `court` | list[str] | `court_live` from Graph v4 |
| `escalations` | list[str] | escalation **kind strings** (e.g. `"quantum"`, `"safety"`), in Graph v4's canonical order — not the typed dicts |
| `prose` | str \| None | rendered prose; `None` only if rendering itself raises |
| `latency_ms` | float | wall time of the whole `run_question` call, ms, 1 decimal |

Exit codes: 0 success; 2 for `--mode classifier` with no checkpoint
(`FileNotFoundError` in the API) and for a checkpoint that exists but cannot
run here (no torch — `RuntimeError` in the API), both with a clear message
("no trained checkpoint found; run the Colab notebook first or use --mode
rule-based"). Empty question → exit 2.

Checkpoint resolution (`--checkpoint` / `checkpoint=`): a `model.pt` file, a
`.../best` directory, or a `models/<name>` directory (`best/model.pt`
appended). Default: `models/v71-classifier/best/model.pt` (C2 layout:
`model.pt` + `config.json` + `thresholds.json` in that directory).
`load_checkpoint` reads the config from inside `model.pt`; per-head
thresholds from `thresholds.json` are consumed by Lane B's calibration /
predict path, not re-implemented here. Loaded classifiers are cached per
path in-process, so repeated `run_question` calls do not reload the model.

## 4. Classifier-path notes / drift watch

* Coded against the C2 signatures as they stand at HEAD `90e20c5`:
  `load_checkpoint(path, *, device=...) -> (model, cfg)` and
  `predict_text(model, tokenizer, text, config=None)`. Lane B is editing
  `src/laya_v7_classifier.py` in parallel; the classifier import is **lazy**
  (inside the classifier path only), so a Lane B mid-edit breakage cannot
  break the rule-based path. If Lane B changes either signature, adapt at
  merge time — the conversion function to update is
  `_classifier_to_stage1` in `src/laya_integrated.py`.
* The classifier's 28 facts flow to Graph v4 as-is (including `in_scope`,
  so an out-of-scope prediction takes the OOS branch); `stridhan_held_or_disposed`
  is derived by the graph's own legacy normalisation, as for the rule-based path.
* `predict_text` spans carry no fact/issue key, so no span is attached to any
  `IssueEvidence`/`FactEvidence` — spans are not in the C1 output.
* On this VM the classifier path is **untestable** (no torch): it raises a
  clear `RuntimeError` rather than a fake score. First real classifier run
  is Lane D's Colab notebook.

## 5. Verification (this VM, CPU, no torch)

* `python3 -m py_compile src/laya_integrated.py` — OK.
* `python3 src/laya_integrated.py --self-test` — runs end to end, 3
  hand-written questions (written for this test, NOT copied from any test
  bank, sealed set, or the 16-Q set):
  * EN (mother, 10-year-old son, husband moved out, no money, rent + school
    costs): `language=en`, `extractor=rule_based`, sections
    `[bnss-144, pwdva-20]`, court `[Magistrate]`, escalations `[quantum]`,
    latency 5.2 ms.
  * Kannada script (own wording: husband pays no maintenance, daughter
    lives with speaker, can she go to court?): `language=kn`,
    sections `[]`, escalations `[procedure, court]`, latency 1.8 ms.
    **Known gap, not hidden:** the evidence extractor's anchors are English
    regexes and evidence mode runs no translation, so Kannada-script input
    extracts nothing — consistent with the frozen-split per-language numbers
    (KN 30/153, recall_status.md §3). The classifier path is the fix for
    this; the runtime reports the empty result honestly.
  * Kanglish (own wording, same situation): `language=kn_roman`, sections
    `[bnss-144, pwdva-20]`, court `[Magistrate]`, escalations `[quantum]`,
    latency 0.9 ms (the English token "maintenance" matches the anchors).
* `--mode classifier` with no checkpoint → exit 2 with the exact message
  above. `--mode auto` on a plain question → `rule_based` with
  `fallback_reason` naming the missing default checkpoint path. Stdin input
  and `python -m src.laya_integrated` both work; `--json` output keys are
  exactly the 12 C1 keys.
* 16-Q spot-check (`mode="auto"`, questions read from frozen
  `ground-truth/ground-truth-v2-hma27-A.json`, read-only): **14/16 exact**,
  latency 0.6–7.3 ms per question, all `rule_based` with `fallback_reason`
  set. Misses are the two known baseline misses — H6 (missing `pwdva-18`)
  and H14 (missing `hma-13`) — identical to the recorded 14/16 baseline
  (recall_status.md §3). No regression, no improvement claimed.
* Guardrails: `python3 tests/test_graph_v4.py` PASS (34 sections / 66 nodes
  / 99 edges, 0 dangling, 7/7 frozen hashes intact);
  `python3 tests/test_prose_renderer_v2.py` PASS (246 cases, Fp=0,
  quality_flags=0, 15/15 mutants); `python3 -m unittest discover -s tests
  -p "test_*.py"` — Ran 66 tests, OK.

## 6. What Lane E (harness) needs to know

* Import `run_question` from `src.laya_integrated` (repo root on `sys.path`;
  the module inserts it itself, so `python3 tests/integrated_backtest.py`
  can import it directly). Do **not** subprocess the CLI for scoring — the
  function returns the dict.
* Score from `result["sections"]` (sorted `kept_ids`); `result["court"]` and
  `result["escalations"]` (kind strings) are the other scored fields.
  `result["issues"]` / `result["facts"]` are plain-JSON projections, safe to
  serialise as-is.
* In `mode="auto"` on this VM every call returns `extractor="rule_based"`
  with `fallback_reason` set — that is the honest rule-based baseline
  (261/500 frozen split), not a classifier result. When a checkpoint exists,
  `auto` returns `extractor="classifier"` and `checkpoint` set; the
  classifier is loaded once and cached per path.
* `run_question` raises `ValueError` on an empty question,
  `FileNotFoundError` in `mode="classifier"` with no checkpoint, and
  `RuntimeError` when a checkpoint exists but cannot load (no torch). The
  CLI maps the latter two to exit 2.
* The runtime does **not** refuse sealed paths itself — that guard lives in
  the harness (C3). Do not point it at sealed files.
