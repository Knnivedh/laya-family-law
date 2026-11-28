import json
import unittest

from scripts.audit_family_corpus import summarize_rows, synthetic_split_overlap


SCHEMA = {
    "issues": ["maintenance", "custody"],
    "facts": ["minor_child"],
    "intents": ["requested", "denied", "incidental", "uncertain"],
    "fact_states": ["supported", "denied", "unknown", "conflicting"],
    "enums": {"claimant_role": ["parent", "spouse"]},
}


def record(lang, blocks, *, custody="uncertain", family=None):
    meta = {"cluster": "core", "blocks": blocks}
    if family is not None:
        meta["template_family_id"] = family
    return {
        "lang": lang,
        "text": "Raw question that must never be included in a report.",
        "issues": {"maintenance": "requested", "custody": custody},
        "facts": {"minor_child": "unknown"},
        "enums": {"claimant_role": "parent"},
        "meta": meta,
        "spans": [{"key": "maintenance", "kind": "issue", "start": 0, "end": 3, "text": "Raw"}],
    }


class TestCorpusAudit(unittest.TestCase):
    def test_report_exposes_empty_label_buckets_and_span_coverage(self):
        rows = [record("en", ["support"]), record("kn", ["support"], custody="denied")]
        report = summarize_rows(rows, SCHEMA)
        self.assertEqual(report["rows"], 2)
        english = report["by_language"]["en"]
        kannada = report["by_language"]["kn"]
        self.assertEqual(english["scenario_counts"], {"core": 1})
        self.assertEqual(english["issues"]["custody"]["denied"], 0)
        self.assertEqual(kannada["issues"]["custody"]["denied"], 1)
        self.assertEqual(kannada["facts"]["minor_child"]["unknown"], 1)
        self.assertEqual(kannada["spanned_issues"]["maintenance"]["requested"], 1)
        self.assertEqual(kannada["spanned_issues"]["custody"]["denied"], 0)
        self.assertNotIn("Raw", json.dumps(report))

    def test_overlap_distinguishes_labels_and_other_language_rows(self):
        training = [record("en", ["support"], family="one")]
        validation = [
            record("en", ["support"], family="one"),
            record("kn", ["support"], family="one"),
            record("kn", ["support"], custody="denied"),
            record("kn_roman", ["divorce"]),
        ]
        overlap = synthetic_split_overlap(training, validation)
        self.assertEqual(overlap["validation_blocks_seen_in_train"], 1)
        self.assertEqual(overlap["validation_rows_with_seen_block_signature"], 3)
        self.assertEqual(overlap["validation_rows_with_different_language_label_block_match"], 1)
        self.assertEqual(overlap["explicit_groups"]["template_family_id"]["validation_rows_tagged"], 2)
        self.assertEqual(overlap["explicit_groups"]["template_family_id"]["validation_rows_seen_in_train"], 2)

    def test_unlabeled_fields_and_missing_block_metadata_stay_separate(self):
        training = record("en", [])
        validation = record("kn", [])
        del validation["enums"]
        summary = summarize_rows([validation], SCHEMA)
        self.assertEqual(summary["enums"]["claimant_role"]["_missing"], 1)
        overlap = synthetic_split_overlap([training], [validation])
        self.assertEqual(overlap["validation_rows_with_seen_block_signature"], 0)
        self.assertEqual(overlap["validation_rows_with_different_language_label_block_match"], 0)


if __name__ == "__main__":
    unittest.main()
