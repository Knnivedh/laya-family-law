import unittest
import json
from http.client import HTTPConnection
from pathlib import Path
from tempfile import TemporaryDirectory
from threading import Thread
from unittest.mock import patch

from src.laya_runtime import assess_turn


DIVORCE = "I want to divorce my husband."
STRIDHAN = "My husband took my gold jewellery and is keeping it."
ARREARS = "My husband has stopped paying the court-ordered maintenance. How do I recover the arrears?"


class ChatRuntimeTests(unittest.TestCase):
    def assess(self, text, state=None, **kwargs):
        return assess_turn(state, text, mode="evidence", device="cpu", **kwargs)

    def test_clarification_is_relevant_to_the_dispute(self):
        result, _ = self.assess(DIVORCE)
        self.assertIn("hma-13", result["kept_ids"])
        self.assertNotIn("demand_made", [
            q["fact_key"] for q in result["pending_clarifications"]
        ])

    def test_mutual_consent_answer_does_not_retract_divorce(self):
        _, state = self.assess(DIVORCE)
        result, _ = self.assess("No.", state, confirmations={"mutual_consent": False})
        self.assertIn("hma-13", result["kept_ids"])
        self.assertNotIn("hma-13b", result["kept_ids"])

    def test_follow_up_preserves_confirmed_answer_and_retires_question(self):
        result, state = self.assess(STRIDHAN)
        self.assertIn("demand_made", [
            q["fact_key"] for q in result["pending_clarifications"]
        ])
        result, state = self.assess("Yes.", state, confirmations={"demand_made": True})
        self.assertNotIn("demand_made", [
            q["fact_key"] for q in result["pending_clarifications"]
        ])
        _, state = self.assess("What are my options?", state)
        self.assertEqual(state.active_facts["demand_made"].source, "user_confirmation")
        self.assertTrue(state.active_facts["demand_made"].value)

    def test_explicit_retraction_retires_divorce(self):
        _, state = self.assess(DIVORCE)
        result, _ = self.assess("Actually, I do not want a divorce.", state)
        self.assertNotIn("hma-13", result["kept_ids"])


class ChatHTTPTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from src.laya_chat_api import make_server

        cls.server = make_server(port=0, extractor_mode="evidence")
        cls.thread = Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.thread.join()
        cls.server.server_close()

    def request(self, path, payload=None):
        conn = HTTPConnection("127.0.0.1", self.server.server_port, timeout=5)
        try:
            if payload is None:
                conn.request("GET", path)
            else:
                conn.request("POST", path, json.dumps(payload), {"Content-Type": "application/json"})
            response = conn.getresponse()
            self.assertEqual(response.getheader("Cache-Control"), "no-store")
            return response.status, json.load(response)
        finally:
            conn.close()

    def test_hma_route_waits_for_applicability_confirmation(self):
        self.assertEqual(self.request("/health")[1]["extractor"], "evidence")
        status, result = self.request("/v1/assess", {"messages": [{"text": DIVORCE}]})
        self.assertEqual(status, 200)
        self.assertEqual(result["status"], "needs_clarification")
        self.assertEqual(result["provisions"], [])
        self.assertEqual(result["questions"][0]["id"], "hma_applicable")
        self.assertIsNone(result["answer"])
        self.assertNotIn(DIVORCE, json.dumps(result))
        status, result = self.request("/v1/assess", {"messages": [
            {"text": DIVORCE}, {"text": "Yes.", "answers": {"hma_applicable": True}},
        ]})
        self.assertEqual(status, 200)
        self.assertEqual(result["provisions"][0]["id"], "hma-13")
        self.assertTrue(result["provisions"][0]["source_url"].startswith("https://www.indiacode.nic.in/"))

    def test_sma_judicial_separation_uses_the_act_named_by_the_user(self):
        status, result = self.request("/v1/assess", {"messages": [{
            "text": "We got married under the Special Marriage Act. I want to apply for judicial separation from my husband.",
        }]})
        self.assertEqual((status, result["status"]), (200, "assessment"))
        self.assertEqual([p["id"] for p in result["provisions"]], ["sma-23"])
        self.assertIn("indiacode.nic.in", result["provisions"][0]["source_url"])
        self.assertIn("Special Marriage Act", result["answer"])

    def test_court_marriage_does_not_establish_which_act_governs(self):
        question = "We had a court marriage. I want to apply for judicial separation from my husband."
        status, result = self.request("/v1/assess", {"messages": [{
            "text": question,
        }]})
        self.assertEqual((status, result["status"]), (200, "needs_clarification"))
        self.assertEqual(result["provisions"], [])
        self.assertIn("hma_applicable", [q["id"] for q in result["questions"]])
        status, result = self.request("/v1/assess", {"messages": [
            {"text": question}, {"text": "Our marriage certificate names the Special Marriage Act."},
        ]})
        self.assertEqual((status, result["status"]), (200, "assessment"))
        self.assertEqual([p["id"] for p in result["provisions"]], ["sma-23"])

    def test_own_hma_statement_can_establish_judicial_separation_route(self):
        status, result = self.request("/v1/assess", {"messages": [{
            "text": "We were married under the Hindu Marriage Act. I want a court order to live apart without ending my marriage.",
        }]})
        self.assertEqual((status, result["status"]), (200, "assessment"))
        self.assertEqual([p["id"] for p in result["provisions"]], ["hma-10"])
        self.assertIn("ground", result["answer"])

    def test_law_stated_in_a_different_persons_case_does_not_apply(self):
        status, result = self.request("/v1/assess", {"messages": [{
            "text": "My cousin said, \"We were married under the Special Marriage Act.\" I want to divorce my husband.",
        }]})
        self.assertEqual((status, result["status"]), (200, "needs_clarification"))
        self.assertEqual(result["questions"][0]["id"], "hma_applicable")

    def test_first_person_act_evidence_blocks_an_inconsistent_confirmation(self):
        status, result = self.request("/v1/assess", {"messages": [
            {"text": DIVORCE},
            {"text": "We got married under the Special Marriage Act.", "answers": {"hma_applicable": True}},
        ]})
        self.assertEqual((status, result["status"]), (200, "needs_review"))
        self.assertEqual(result["provisions"], [])
        self.assertEqual(result["review_reason"], "conflicting_governing_marriage_law")

    def test_explicit_denial_of_domestic_violence_preserves_ordinary_support(self):
        status, result = self.request("/v1/assess", {"messages": [{
            "text": (
                "I have been married for two years. My husband lends me money when I ask. "
                "I want a maintenance order because my salary has reduced. There has been no domestic violence."
            ),
        }]})
        self.assertEqual((status, result["status"]), (200, "assessment"))
        self.assertEqual([p["id"] for p in result["provisions"]], ["bnss-144"])
        self.assertIsNone(result["safety_message"])

    def test_no_shared_household_statement_does_not_convert_child_support_to_dv(self):
        status, result = self.request("/v1/assess", {"messages": [{
            "text": (
                "My former partner will not pay our child expenses. We never lived together or married. "
                "Can I ask for maintenance?"
            ),
        }]})
        self.assertEqual((status, result["status"]), (200, "assessment"))
        self.assertEqual([p["id"] for p in result["provisions"]], ["bnss-144"])

    def test_mixed_law_unknown_and_unprompted_facts(self):
        status, result = self.request("/v1/assess", {"messages": [
            {"text": DIVORCE}, {"text": "No.", "answers": {"hma_applicable": False}},
        ]})
        self.assertEqual((status, result["status"]), (200, "needs_review"))
        self.assertEqual(result["provisions"], [])
        self.assertIsNone(result["answer"])
        for payload in ({}, {"messages": []}, {"messages": [{"text": " "}]}, {
            "messages": [{"text": "Yes", "answers": {"hma_applicable": True}}],
        }):
            with self.subTest(payload=payload):
                self.assertEqual(self.request("/v1/assess", payload)[0], 400)

    def test_does_not_assume_a_forum_on_an_unrecognized_question(self):
        status, result = self.request("/v1/assess", {"messages": [
            {"text": "What taxes do I owe on selling a house?"},
        ]})
        self.assertEqual((status, result["status"]), (200, "needs_review"))
        self.assertEqual(result["forums"], [])
        self.assertIsNone(result["answer"])

    def test_existing_order_uses_requested_action_and_issuing_statute(self):
        for text, expected in (
            ("I have a maintenance order under BNSS section 144. My husband missed the last three payments. How can I recover the arrears?", "bnss-144-3"),
            ("I have a maintenance order under BNSS section 144. My salary has gone down. Can I increase the amount of maintenance?", "bnss-146"),
        ):
            with self.subTest(expected=expected):
                status, result = self.request("/v1/assess", {"messages": [{"text": text}]})
                self.assertEqual((status, result["status"]), (200, "assessment"))
                self.assertEqual([p["id"] for p in result["provisions"]], [expected])

    def test_unknown_order_requires_confirmation_and_old_order_needs_review(self):
        _, result = self.request("/v1/assess", {"messages": [{"text": ARREARS}]})
        self.assertEqual((result["status"], result["provisions"]), ("needs_clarification", []))
        self.assertEqual(result["questions"][0]["id"], "bnss_order")
        _, result = self.request("/v1/assess", {"messages": [
            {"text": ARREARS}, {"text": "Yes.", "answers": {"bnss_order": True}},
        ]})
        self.assertEqual([p["id"] for p in result["provisions"]], ["bnss-144-3"])
        _, result = self.request("/v1/assess", {"messages": [{
            "text": "My husband has not paid maintenance under our CrPC section 125 court order from 2022. How do I recover the arrears?",
        }]})
        self.assertEqual((result["status"], result["provisions"]), ("needs_review", []))

    def test_mixed_order_and_custody_needs_review(self):
        _, result = self.request("/v1/assess", {"messages": [
            {"text": ARREARS + " I also want custody of our children."},
        ]})
        self.assertEqual((result["status"], result["provisions"]), ("needs_review", []))

    def test_urgent_safety_is_returned_before_hma_confirmation(self):
        status, result = self.request("/v1/assess", {"messages": [{
            "text": "My husband threatened to kill me tonight. I want to divorce him.",
        }]})
        self.assertEqual((status, result["status"]), (200, "urgent"))
        self.assertIn("emergency", result["safety_message"])
        self.assertFalse(any(p["id"].startswith("hma-") for p in result["provisions"]))

    def test_urgent_safety_precedes_a_mixed_order_question(self):
        status, result = self.request("/v1/assess", {"messages": [{
            "text": ARREARS + " My husband threatened to kill me tonight.",
        }]})
        self.assertEqual((status, result["status"]), (200, "urgent"))
        self.assertEqual(result["provisions"], [])
        self.assertIn("emergency", result["safety_message"])

    def test_requests_cannot_set_runtime_options_or_overflow_limits(self):
        self.assertEqual(self.request("/v1/assess", {
            "mode": "auto", "messages": [{"text": DIVORCE}],
        })[0], 400)
        self.assertEqual(self.request("/v1/assess", {
            "messages": [{"text": "x" * 70_000}],
        })[0], 413)


    def test_new_maintenance_order_is_not_treated_as_existing_order_enforcement(self):
        status, result = self.request("/v1/assess", {"messages": [{
            "text": "My husband has not paid monthly support for six months. I want to apply for a new BNSS 144 maintenance order for myself.",
        }]})
        self.assertEqual((status, result["status"]), (200, "assessment"))
        self.assertIn("bnss-144", [p["id"] for p in result["provisions"]])
        self.assertNotIn("bnss-144-3", [p["id"] for p in result["provisions"]])
        self.assertNotIn("bnss_order", [q["id"] for q in result["questions"]])


class IntegratedAuditTests(unittest.TestCase):
    def test_integrated_classifier_uses_checkpoint_calibration(self):
        from src import laya_integrated
        from src.laya_v7_classifier import ClassifierConfig

        prediction = {
            "issues": {"divorce": {"intent": "requested", "confidence": 0.62,
                                   "probs": {"requested": 0.62, "uncertain": 0.38}}},
            "facts": {"divorce_asked": {"state": "supported", "confidence": 0.61,
                                      "probs": {"supported": 0.61, "unknown": 0.39}}},
        }
        with TemporaryDirectory() as folder:
            checkpoint = Path(folder) / "model.pt"
            checkpoint.touch()
            checkpoint.with_name("thresholds.json").write_text(json.dumps({
                "temperature_issue": 1.25, "temperature_fact": 1.4,
                "tau_0_issue": 0.7, "tau_0_fact": 0.7,
            }), encoding="utf-8")
            with patch.object(laya_integrated, "_load_classifier", return_value=(
                object(), object(), ClassifierConfig(),
            )), patch("src.laya_v7_classifier.predict_text", return_value=prediction) as predict:
                result = laya_integrated.run_question(DIVORCE, mode="classifier", checkpoint=checkpoint)
            self.assertEqual(predict.call_args.args[3].temperature_issue, 1.25)
            self.assertEqual(result["issues"]["divorce"]["intent"], "uncertain")
            self.assertEqual(result["facts"]["divorce_asked"]["status"], "unknown")
            self.assertEqual(result["sections"], [])

    def test_empty_pre_gate_candidates_are_measurable(self):
        from tests.v7_backtest import compute_fb

        scored = compute_fb({"kept_ids": [], "candidates_before_gate": []})
        self.assertTrue(scored["fb_measured"])
        self.assertEqual(scored["fb_count"], 0)

    def test_integrated_backtest_measures_gated_candidates(self):
        from src.laya_integrated import run_question
        from tests.integrated_backtest import _fb_fp_for_row

        result = run_question(STRIDHAN, mode="rule-based")
        _, fb_measured, _, fp, fp_measured = _fb_fp_for_row(result)
        self.assertTrue(fb_measured)
        self.assertTrue(fp_measured)
        self.assertEqual(fp, 0)

    def test_chat_result_accepts_classifier_extractor(self):
        from src.laya_chat_api import _chat_result

        sample = {
            "error": None,
            "extractor_mode": "classifier",
            "kept_statutory_ids": ["bnss-144"],
            "pending_clarifications": [],
            "escalation_kinds": [],
            "prose": "Eligible maintenance section: BNSS Section 144.",
            "prose_fp_hits": [],
            "in_scope": True,
            "dispositions": {"bnss-144": {"reason_codes": ["maintenance_requested"]}},
            "turn_id": 1,
            "lang": "kn",
            "court_live": ["Magistrate"],
        }
        payload = _chat_result(sample, hma_applicable=None)
        self.assertEqual(payload["status"], "assessment")
        self.assertEqual(payload["extractor"], "classifier")
        self.assertEqual([p["id"] for p in payload["provisions"]], ["bnss-144"])

    def test_non_hma_personal_marriage_law_avoids_hma_prompt_and_keeps_bnss(self):
        from src.laya_chat_api import assess_conversation

        res = assess_conversation(
            {"messages": [{"text": "We married under Muslim personal law by nikah. I want a divorce."}]},
            extractor_mode="evidence",
        )
        self.assertEqual(res["status"], "needs_review")
        self.assertEqual(res.get("review_reason"), "unsupported_personal_marriage_law")
        self.assertEqual(res.get("personal_law_regimes"), ["muslim"])
        self.assertEqual(res["questions"], [])

        maint = assess_conversation(
            {"messages": [{"text": "We married under Muslim law by nikah. My husband stopped giving monthly maintenance."}]},
            extractor_mode="evidence",
        )
        self.assertIn("bnss-144", [p["id"] for p in maint["provisions"]])

    def test_adoption_order_routes_to_district_magistrate_review(self):
        from src.laya_chat_api import assess_conversation

        res = assess_conversation(
            {"messages": [{"text": "How do I apply for an adoption order under CARA in Family Court?"}]},
            extractor_mode="evidence",
        )
        self.assertEqual(res["status"], "needs_review")
        self.assertEqual(res.get("review_reason"), "adoption_district_magistrate_jurisdiction")
        self.assertEqual(res["forums"], ["District Magistrate"])

    def test_senior_citizens_act_requires_election_before_bnss144(self):
        from src.laya_chat_api import assess_conversation

        first = assess_conversation(
            {"messages": [{"text": "I filed a claim before the Maintenance Tribunal under the Senior Citizens Act and also want monthly maintenance."}]},
            extractor_mode="evidence",
        )
        self.assertEqual(first["status"], "needs_clarification")
        self.assertEqual(first["questions"][0]["id"], "senior_citizens_election")
        self.assertEqual(first["provisions"], [])

        second = assess_conversation(
            {"messages": [
                {"text": "I filed a claim before the Maintenance Tribunal under the Senior Citizens Act and also want monthly maintenance."},
                {"text": "I am proceeding only under BNSS 144.", "answers": {"senior_citizens_election": True}},
            ]},
            extractor_mode="evidence",
        )
        self.assertEqual(second["status"], "assessment")
        self.assertIn("bnss-144", [p["id"] for p in second["provisions"]])

    def test_pre_july_2024_savings_and_rbd_subroute_metadata(self):
        from src.laya_chat_api import assess_conversation

        savings = assess_conversation(
            {"messages": [{"text": "My husband took my gold stridhan in an IPC 406 offence committed before 1 July 2024."}]},
            extractor_mode="evidence",
        )
        self.assertTrue(savings.get("pre_july_2024_savings"))
        self.assertIn("BNSS s.531", savings.get("statutory_note", ""))

        rbd = assess_conversation(
            {"messages": [{"text": "We need a delayed registration birth certificate for our baby after one year."}]},
            extractor_mode="evidence",
        )
        b_prov = [p for p in rbd["provisions"] if p["id"] == "births-deaths-act-1969"]
        self.assertEqual(len(b_prov), 1)
        self.assertEqual(b_prov[0].get("subroute"), "section_13_delayed_registration")


if __name__ == "__main__":
    unittest.main()
