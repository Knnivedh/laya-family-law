"""Phase A gate A3 — clause-supervision audit checker.

Flags any clause-loss site that assigns QUESTION-LEVEL labels to EVERY
clause. The rule (GPT-RERUN §4/§13, binding): never copy question-level
labels onto every clause for local span training — that teaches the model
background clauses express requested issues. Use annotated evidence spans
or multiple-instance learning; where clause-level labels are unavailable,
mask that loss and rely on question-level supervision.

Checks (all read-only; this script never edits the audited files):

  C1  COPY — a site that broadcasts a question-level label to all clauses.
      Currently: ``src/laya_v7_classifier.py::encode_labels`` marks EVERY
      clause ``hypothetical=1`` when the question-level enum
      ``modality_time`` is ``hypothetical``/``quoted``. Found -> exit 1.
  C2  VACUOUS — a gate column with zero positive supervision in the whole
      corpus (``third_party``: the schema has no third-party span label, so
      the head trains on all-zero targets and can never fire).
  C3  UNMASKED-PAD — a clause loss computed over padded clause slots
      (gate BCE in ``scripts/train_v71_classifier.py`` is unmasked; the
      span BCE next to it IS masked by ``span_valid``).
  C4  NO-CLAUSE-LOSS — clause issue/fact logits are computed in
      ``forward`` but never enter any loss (only the full-question logits
      do), so fusion at inference uses clause predictions with zero
      clause-local supervision.
  C5  SPAN-COVERAGE — records carrying no spans at all (span head trains
      on the rest only) — informational.

Exit code: 1 iff a C1 copying site is found (the gate's pass check is
"0 sites assign question labels to all clauses"); 0 otherwise. C2–C5 are
reported as findings for Lane B regardless of the exit code.

Pure python — no torch needed. Run from the repo root:

    python3 scripts/check_clause_supervision.py
    python3 scripts/check_clause_supervision.py --train-file data/synthetic_v7_1/train.jsonl --val-file data/synthetic_v7_1/validation.jsonl
"""

from __future__ import annotations

import argparse
import ast
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from laya_v7_classifier import encode_labels, load_corpus_jsonl  # noqa: E402

CLASSIFIER_PATH = REPO_ROOT / "src" / "laya_v7_classifier.py"
TRAIN_PATH = REPO_ROOT / "scripts" / "train_v71_classifier.py"


def check_c1_copy(classifier_src: str) -> list[str]:
    """Find question-level -> all-clauses broadcasts in encode_labels."""
    findings: list[str] = []
    tree = ast.parse(classifier_src)
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == "encode_labels":
            src = ast.get_source_segment(classifier_src, node) or ""
            # The known broadcast: modality_time (question-level enum) sets
            # row[1] = 1 for EVERY clause row.
            if re.search(r'modality_time.*hypothetical.*quoted', src, re.S) and \
                    re.search(r"for row in gate:\s*\n\s*row\[1\] = 1", src):
                findings.append(
                    "C1 COPY (src/laya_v7_classifier.py::encode_labels, "
                    "lines ~678-680): if the question-level enum "
                    "modality_time is 'hypothetical'/'quoted', EVERY clause "
                    "row gets gate[hypothetical]=1 — a question-level label "
                    "copied to all clauses, including requested clauses in "
                    "mixed-modality questions. The gate then learns "
                    "'requested clause => hypothetical' on those records.")
            # Generic tripwire: any other `for row in gate: row[i] = 1`
            # whose guard reads a record-level (non-span, non-clause)
            # value.
            for m in re.finditer(r"for row in gate:\s*\n(\s*row\[\d+\] = 1)",
                                 src):
                if "row[1] = 1" not in m.group(0):
                    findings.append(
                        f"C1 COPY (generic): all-clause gate assignment: "
                        f"{m.group(0).strip()!r}")
    return findings


def check_c3_unmasked_pad(train_src: str) -> list[str]:
    findings: list[str] = []
    if re.search(r"loss_gate = bce\(out\[\"clause_gate_logits\"\], b_in\[\"gate\"\]\)",
                 train_src):
        findings.append(
            "C3 UNMASKED-PAD (scripts/train_v71_classifier.py:752): "
            "loss_gate = BCE(clause_gate_logits, gate) is computed over the "
            "FULL [B, max_c, 3] tensor, including padded clause slots "
            "(gate rows for padding are all-zero targets, logits come from "
            "pad tokens). The span loss two lines below IS masked "
            "(span_valid, :757-760); the gate loss is not. Padded slots "
            "inject all-zero supervision into the gate head every step.")
    return findings


def check_c4_no_clause_loss(train_src: str, classifier_src: str) -> list[str]:
    findings: list[str] = []
    if "clause_issue_logits" in classifier_src and \
            "clause_issue_logits" not in train_src.split("def train")[1].split("loss_issue")[0]:
        pass  # structural check below is the authoritative one
    train_body = train_src[train_src.index("def train"):]
    loss_section = train_body[train_body.index("loss_issue"):]
    loss_section = loss_section[:loss_section.index("loss = (w[\"issue\"")]
    if "clause_issue_logits" not in loss_section and \
            "clause_fact_logits" not in loss_section:
        findings.append(
            "C4 NO-CLAUSE-LOSS (scripts/train_v71_classifier.py:745-762): "
            "loss_issue / loss_fact use ONLY the full-question logits "
            "(out['issue_logits'] / out['fact_logits']). The per-clause "
            "logits (out['clause_issue_logits'] / out['clause_fact_logits'], "
            "built in src/laya_v7_classifier.py forward ~994-1014) never "
            "enter any loss — no clause-local supervision exists for them. "
            "Fusion at inference (train.py:694-695 evaluate, classifier.py "
            "predict_text :1114-1116) still max-pools over these clause "
            "predictions. With the landed 1-pass default the clause "
            "vectors come from span-pooling the SAME trained encoding "
            "(not separate clause encodings), so the encoder itself is "
            "trained — but no loss term is ever computed on the clause "
            "logits, so the fused 'requested' score still rests on "
            "clause predictions with zero direct clause supervision.")
    return findings


def check_c2_c5_corpus(train_file: str, val_file: str) -> list[str]:
    findings: list[str] = []
    for path in (train_file, val_file):
        recs, _ = load_corpus_jsonl(path)
        n_nospan = sum(1 for r in recs if not r["spans"])
        tp_rows = hyp_rows = denied_rows = span_rows = tot_rows = 0
        for r in recs:
            lab = encode_labels(r)
            for row in lab["gate"]:
                tot_rows += 1
                denied_rows += row[0]
                hyp_rows += row[1]
                tp_rows += row[2]
            span_rows += sum(lab["span_mask"])
        findings.append(
            f"C2/C5 corpus {Path(path).name}: n={len(recs)} records, "
            f"{n_nospan} with NO spans (span head trains on the rest); "
            f"clause rows={tot_rows}, span_mask=1 rows={span_rows}, "
            f"gate denied=1 rows={denied_rows} (span-derived, clause-local "
            f"— legitimate), gate hypothetical=1 rows={hyp_rows} (ALL from "
            f"the C1 question-level broadcast), gate third_party=1 rows="
            f"{tp_rows}.")
        if tp_rows == 0:
            findings.append(
                f"C2 VACUOUS (in {Path(path).name}): third_party gate column "
                "has ZERO positive rows in the whole split — the corpus "
                "schema carries no third-party span label "
                "(classifier.py encode_labels docstring admits this), so "
                "the gate head's third column trains on all-zero targets "
                "and can never fire. Either add third-party span labels or "
                "drop the column; do not let a never-firing veto look like "
                "a safety feature.")
    return findings


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Clause-supervision checker (A3).")
    ap.add_argument("--train-file", default="data/synthetic_v7_1/train.jsonl")
    ap.add_argument("--val-file", default="data/synthetic_v7_1/validation.jsonl")
    args = ap.parse_args(argv)

    classifier_src = CLASSIFIER_PATH.read_text(encoding="utf-8")
    train_src = TRAIN_PATH.read_text(encoding="utf-8")

    print("Clause-supervision audit (A3) — read-only check")
    print(f"  classifier: {CLASSIFIER_PATH.relative_to(REPO_ROOT)}")
    print(f"  train script: {TRAIN_PATH.relative_to(REPO_ROOT)}")
    print()
    c1 = check_c1_copy(classifier_src)
    c3 = check_c3_unmasked_pad(train_src)
    c4 = check_c4_no_clause_loss(train_src, classifier_src)
    c25 = check_c2_c5_corpus(args.train_file, args.val_file)

    for block in (c1, c3, c4, c25):
        for line in block:
            print(f"  - {line}")
    print()
    # Legitimate clause-local supervision (for the record):
    print("  Legitimate clause-local supervision found (not flagged):")
    print("    * gate denied=1: span-derived — a span naming a fact/issue "
          "the corpus marks 'denied' marks its clause (encode_labels).")
    print("    * span_mask: span-derived — 1 iff a corpus span falls in "
          "the clause (encode_labels); span BCE is masked to real "
          "clauses (train.py:757-760).")
    print("    * issue/fact heads: question-level supervision on the FULL "
          "encoding only (train.py:745-747) — legitimate as question-level "
          "loss; it is NOT clause supervision.")
    print()
    if c1:
        print(f"FAIL: {len(c1)} site(s) assign question-level labels to all "
              "clauses. A3 gate NOT passed (exit 1).")
        return 1
    print("PASS: 0 sites assign question labels to all clauses (exit 0).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
