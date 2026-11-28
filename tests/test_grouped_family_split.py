import unittest

from scripts.build_grouped_family_split import grouped_split, verify_split


def sample(case_id, lang, blocks, text):
    return {
        "id": case_id,
        "lang": lang,
        "text": text,
        "issues": {"divorce": "requested"},
        "meta": {"blocks": blocks, "split": "train"},
    }


class TestGroupedFamilySplit(unittest.TestCase):
    def test_template_links_and_normalized_duplicates_stay_together(self):
        rows = [
            sample("1", "en", ["a"], "Example one"),
            sample("2", "kn", ["a", "b"], "Kannada case 1"),
            sample("3", "en", ["b"], "example two"),
            sample("4", "kn", ["c"], "  Example\u00a0 TWO  "),
            sample("5", "en", ["d"], "Example three"),
            sample("6", "kn", ["d"], "Kannada case 2"),
        ]
        train, dev = grouped_split(rows, ["divorce"], dev_size=2, tolerance=0)
        self.assertEqual({row["id"] for row in dev}, {"5", "6"})
        self.assertEqual(len(train), 4)
        self.assertEqual(rows[-1]["meta"]["split"], "train")
        self.assertEqual(verify_split(train, dev)["shared_normalized_texts"], 0)
        self.assertEqual(verify_split(train, dev)["shared_recorded_blocks"], 0)

    def test_infeasible_layout_fails_instead_of_leaking(self):
        rows = [
            sample("1", "en", ["a"], "Example one"),
            sample("2", "kn", ["a"], "Example two"),
        ]
        with self.assertRaisesRegex(ValueError, "grouped split"):
            grouped_split(rows, ["divorce"], dev_size=1, tolerance=0)

    def test_verification_detects_text_leaks_without_shared_blocks(self):
        train = [sample("1", "en", ["a"], "Equivalent\tinput")]
        dev = [sample("2", "kn", ["b"], "equivalent input ")]
        with self.assertRaisesRegex(ValueError, "overlap"):
            verify_split(train, dev)


if __name__ == "__main__":
    unittest.main()
