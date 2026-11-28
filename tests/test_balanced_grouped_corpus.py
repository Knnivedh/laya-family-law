import json
import tempfile
import unittest
from pathlib import Path

from scripts.build_balanced_grouped_corpus import build_balanced_corpus
from src.laya_v7_classifier import FACTS, ISSUES, load_corpus_jsonl


class BalancedGroupedCorpusTests(unittest.TestCase):
    def test_balanced_split_eliminates_zero_denied_and_keeps_dev_disjoint(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            manifest = build_balanced_corpus(out, repeats_per_lang=5)
            self.assertEqual(manifest["overlap_vs_grouped_dev"], {
                "shared_ids": 0,
                "shared_blocks": 0,
                "shared_normalized_texts": 0,
            })
            train_recs, rep = load_corpus_jsonl(out / "balanced_train.jsonl")
            self.assertEqual(rep["n_skipped"], 0)
            for issue in ISSUES:
                self.assertTrue(
                    any(r["issues"][issue] == "denied" for r in train_recs),
                    f"Missing denied examples for issue {issue}",
                )
            for fact in FACTS:
                self.assertTrue(
                    any(r["facts"][fact] == "denied" for r in train_recs),
                    f"Missing denied examples for fact {fact}",
                )
            for cfact in ("money_fact", "custody_claim", "residence_claim", "violence", "stridhan_claim"):
                self.assertTrue(
                    any(r["facts"][cfact] == "conflicting" for r in train_recs),
                    f"Missing conflicting examples for {cfact}",
                )


if __name__ == "__main__":
    unittest.main()
