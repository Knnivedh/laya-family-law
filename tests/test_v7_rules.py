"""Unit and matrix tests for LAYA v7 schema, Graph v4 reachability, and Stage 2 rules."""

from __future__ import annotations

import json
from pathlib import Path
import unittest

from src.laya_v7_graph import (
    audit_graph_reachability,
    evaluate_stage2_v7,
    layer_a_filter_options,
    load_graph_v4,
)
from src.laya_v7_schema import FactEvidence, IssueEvidence, fact_value, proved_true


class V7RulesTests(unittest.TestCase):
    def test_graph_v4_100pct_reachable_from_declared_entry_points(self):
        audit = audit_graph_reachability()
        self.assertEqual(audit["total_nodes"], 66)
        self.assertEqual(audit["reachable_nodes"], 66)
        self.assertEqual(audit["unreachable_nodes"], [])

    def test_unknown_string_never_coerced_to_true(self):
        facts = {
            "in_scope": "unknown",
            "divorce_asked": "unknown",
            "proceeding_pending_hma": "unknown",
            "being_filed": "unknown",
            "decree": "unknown",
            "money_fact": "yes",
            "joint_property_claim": "unknown",
        }
        self.assertFalse(proved_true(facts, "proceeding_pending_hma"))
        self.assertIsNone(fact_value(facts, "joint_property_claim"))
        out = evaluate_stage2_v7({"maintenance", "joint_property"}, facts)
        self.assertEqual(set(out["kept_ids"]), {"bnss-144", "pwdva-20"})

    def test_layer_a_filters_forbidden_options_before_generation(self):
        g = load_graph_v4()
        nodes = {n["node_id"]: n for n in g["nodes"]}
        opts_m, rem_m = layer_a_filter_options(
            "maintenance:maintenance-root",
            nodes["maintenance:maintenance-root"]["options"],
            {"proceeding_pending_hma": False, "decree": False, "claimant_sex": "male", "child_maintenance_only": False},
        )
        self.assertTrue(any("hma" in r.lower() or "male" in r.lower() for r in rem_m))
        self.assertFalse(any("PWDVA" in o for o in opts_m))

        opts_d, rem_d = layer_a_filter_options(
            "procedure:divorce-gate",
            nodes["procedure:divorce-gate"]["options"],
            {"divorce_asked": True, "mutual_consent": True},
        )
        self.assertTrue(any("13B" in o for o in opts_d))
        self.assertFalse(any("Contested divorce" in o for o in opts_d))
        self.assertTrue(rem_d)

    def test_maintenance_applicability_matrix(self):
        # Wife standard
        r1 = evaluate_stage2_v7({"maintenance"}, {"claimant_sex": "female", "money_fact": True})
        self.assertEqual(set(r1["kept_ids"]), {"bnss-144", "pwdva-20"})
        self.assertEqual(r1["court_live"], ["Magistrate"])

        # Male self-maintenance without HMA proceeding -> inapplicable
        r2 = evaluate_stage2_v7({"maintenance"}, {"claimant_sex": "male", "money_fact": True, "child_maintenance_only": False})
        self.assertEqual(r2["kept_ids"], [])

        # Male self-maintenance WITH pending HMA -> HMA 24 only
        r3 = evaluate_stage2_v7({"maintenance"}, {"claimant_sex": "male", "money_fact": True, "proceeding_pending_hma": True})
        self.assertEqual(set(r3["kept_ids"]), {"hma-24"})
        self.assertEqual(r3["court_live"], ["Family Court"])

        # Father claiming for minor child only -> BNSS 144 only (no PWDVA 20)
        r4 = evaluate_stage2_v7(
            {"maintenance"},
            {"claimant_sex": "male", "money_fact": True, "child_maintenance_only": True, "minor_child": True},
        )
        self.assertEqual(set(r4["kept_ids"]), {"bnss-144"})
        self.assertEqual(r4["court_live"], ["Magistrate"])

        # Parent claiming from adult child -> BNSS 144 only
        r5 = evaluate_stage2_v7({"maintenance"}, {"claimant_role": "parent", "money_fact": True})
        self.assertEqual(set(r5["kept_ids"]), {"bnss-144"})

        # Lump sum settlement inside divorce -> HMA 25 only
        r6 = evaluate_stage2_v7(
            {"maintenance", "divorce"},
            {"claimant_sex": "female", "divorce_asked": True, "mutual_consent": True, "lump_sum_settlement": True, "money_fact": True},
        )
        self.assertEqual(set(r6["kept_ids"]), {"hma-25", "hma-13b"})

        # Existing magistrate order arrears/reduction -> BNSS 144 only
        r7 = evaluate_stage2_v7({"maintenance"}, {"claimant_sex": "female", "existing_order_enforcement": True, "money_fact": True})
        self.assertEqual(set(r7["kept_ids"]), {"bnss-144"})

    def test_pwdva_17_18_19_and_22_independence_and_urgent_safety(self):
        # Residence only without violence/coercive eviction -> 17, 19 ONLY (no 18)
        r_res = evaluate_stage2_v7({"residence"}, {"claimant_sex": "female", "residence_claim": True, "explicit_residence_order_only": True})
        self.assertEqual(set(r_res["kept_ids"]), {"pwdva-17", "pwdva-19"})
        self.assertIn("residence", r_res["escalation_kinds"])
        self.assertNotIn("safety", r_res["escalation_kinds"])

        # Violence + compensation without residence -> 18, 22 ONLY (no 17, 19)
        r_vio = evaluate_stage2_v7({"violence", "dv_compensation"}, {"claimant_sex": "female", "violence": True, "dv_injury_comp_asked": True})
        self.assertEqual(set(r_vio["kept_ids"]), {"pwdva-18", "pwdva-22"})
        self.assertIn("safety", r_vio["escalation_kinds"])
        self.assertNotIn("residence", r_vio["escalation_kinds"])

        # Male DV victim -> no PWDVA sections, yet independent urgent safety triggers!
        r_male_dv = evaluate_stage2_v7({"violence"}, {"claimant_sex": "male", "violence": True, "urgent_safety_risk": True})
        self.assertEqual(r_male_dv["kept_ids"], [])
        self.assertIn("safety", r_male_dv["escalation_kinds"])

    def test_hma27_d2_gate_and_joint_property(self):
        # Exclusive Stridhan without HMA -> BNS 316 ONLY
        r1 = evaluate_stage2_v7({"stridhan"}, {"stridhan_claim": True, "stridhan_held_or_disposed": True, "proceeding_pending_hma": False})
        self.assertEqual(set(r1["kept_ids"]), {"bns-316"})

        # Joint property WITHOUT pending/being-filed HMA -> hma-27 conditional (not kept)
        r2 = evaluate_stage2_v7({"joint_property"}, {"joint_property_claim": True, "proceeding_pending_hma": False, "being_filed": False})
        self.assertEqual(r2["kept_ids"], [])
        self.assertEqual(r2["dispositions"]["hma-27"]["status"], "conditional")

        # Joint property WITH being_filed HMA -> hma-27 kept!
        r3 = evaluate_stage2_v7({"joint_property"}, {"joint_property_claim": True, "being_filed": True})
        self.assertEqual(set(r3["kept_ids"]), {"hma-27"})
        self.assertEqual(r3["court_live"], ["Family Court"])
        self.assertIn("fact", r3["escalation_kinds"])

    def test_independent_issues_and_multiturn_fact_override(self):
        # Pending joint property unresolved cannot suppress supported child maintenance
        facts = {
            "claimant_sex": "male",
            "money_fact": True,
            "child_maintenance_only": True,
            "minor_child": True,
            "joint_property_claim": FactEvidence(key="joint_property_claim", status="unknown"),
            "proceeding_pending_hma": False,
        }
        r1 = evaluate_stage2_v7({"maintenance", "joint_property"}, facts)
        self.assertEqual(set(r1["kept_ids"]), {"bnss-144"})

        # User correction turns on being_filed -> adds hma-27 without dropping child maintenance
        facts["joint_property_claim"] = FactEvidence(key="joint_property_claim", status="supported", source="user_confirmation", turn=1)
        facts["being_filed"] = FactEvidence(key="being_filed", status="supported", source="user_confirmation", turn=1)
        r2 = evaluate_stage2_v7({"maintenance", "joint_property"}, facts)
        self.assertEqual(set(r2["kept_ids"]), {"bnss-144", "hma-27"})

    def test_divorce_js_restitution_and_custody_vocab_modes(self):
        r_js = evaluate_stage2_v7({"divorce"}, {"divorce_asked": True, "judicial_separation_only": True})
        self.assertEqual(r_js["kept_ids"], [])

        r_rcr = evaluate_stage2_v7({"restitution"}, {"restitution_asked": True, "divorce_asked": False})
        self.assertEqual(set(r_rcr["kept_ids"]), {"hma-9"})

        r_cust_b = evaluate_stage2_v7({"custody"}, {"custody_claim": True, "proceeding_pending_hma": False}, custody_vocab="v3_bundled")
        self.assertEqual(set(r_cust_b["kept_ids"]), {"gwa-1890", "hmga-1956-s6", "welfare-principle"})

        r_cust_p = evaluate_stage2_v7({"custody"}, {"custody_claim": True, "proceeding_pending_hma": False}, custody_vocab="statutory_primary")
        self.assertEqual(set(r_cust_p["kept_ids"]), {"gwa-1890"})
        self.assertIn("welfare-principle", r_cust_p["applied_principles"])

    def test_prose_v2_safety_and_error_guards(self):
        from src.laya_prose_v2 import prose_forbidden_check, render_prose

        # Unknown string cannot trigger mutual_consent or child wording
        r_unk = render_prose(
            {"kept_ids": ["hma-13b"], "court_live": ["Family Court"], "court_source": "kept", "escalation_kinds": []},
            {"divorce_asked": "yes", "mutual_consent": "unknown", "child_fact": "unknown"},
        )
        self.assertNotIn("13B", r_unk["prose"])
        self.assertNotIn("your child", r_unk["prose"])

        # Recovery escalation without bns-316 must NOT cite Section 316
        r_rec = render_prose(
            {"kept_ids": ["hma-27"], "court_live": ["Family Court"], "court_source": "kept", "escalation_kinds": ["recovery"]},
            {"joint_property_claim": True, "proceeding_pending": True},
        )
        self.assertNotIn("316", r_rec["prose"])
        hits, _ = prose_forbidden_check(r_rec["prose"], ["hma-27"], [], {"joint_property_claim": True, "proceeding_pending": True})
        self.assertEqual(hits, [])

        # Out-of-scope with stale sections never leaks sections
        r_oos = render_prose(
            {"in_scope": False, "kept_ids": ["bnss-144"], "court_live": ["Magistrate"], "court_source": "kept"},
            {},
        )
        self.assertNotIn("144", r_oos["prose"])

        # Invalid enum values return explicit error status and safe handoff
        r_err = render_prose(
            {"kept_ids": ["bnss-144"], "escalation_kinds": ["invented_kind"], "court_live": ["Magistrate"]},
            {},
        )
        self.assertEqual(r_err["status"], "error")
        self.assertNotIn("144", r_err["prose"])

    def test_grounded_isolation_batch_invariance_and_edge_guards(self):
        from src.laya_v7 import assess_v7, assess_v7_batch

        q_cust = "I want my daughter to stay in the house with me after separation."
        q_res = "They changed the lock on our shared house and I cannot enter."
        q_neg = "He has never hit me. What I need is money for our 3-year-old daughter."
        q_oos = "My brother-in-law borrowed 2 lakh rupees from me and refuses to pay it back."
        q_safe = "My husband bought a gold chain lying in our joint locker and there is no dispute about it."
        q_father = "My wife earns well and refuses to pay for our minor daughter's school fees."

        r_cust = assess_v7(q_cust, mode="evidence", custody_vocab="statutory_primary")
        self.assertEqual(set(r_cust["kept_ids"]), {"gwa-1890"})

        r_res = assess_v7(q_res, mode="evidence", custody_vocab="statutory_primary")
        self.assertEqual(set(r_res["kept_ids"]), {"pwdva-17", "pwdva-18", "pwdva-19"})

        r_neg = assess_v7(q_neg, mode="evidence", custody_vocab="statutory_primary")
        self.assertEqual(set(r_neg["kept_ids"]), {"bnss-144", "pwdva-20"})
        self.assertNotIn("pwdva-18", r_neg["kept_ids"])

        r_oos = assess_v7(q_oos, mode="evidence")
        self.assertFalse(r_oos["in_scope"])
        self.assertEqual(r_oos["kept_ids"], [])
        self.assertEqual(r_oos["court_live"], [])

        r_safe = assess_v7(q_safe, mode="evidence")
        self.assertEqual(r_safe["kept_ids"], [])

        r_father = assess_v7(q_father, mode="evidence", custody_vocab="statutory_primary")
        self.assertEqual(set(r_father["kept_ids"]), {"bnss-144"})

        # Batch permutation invariance: order/neighbors never change per-item decisions
        qs_fwd = [q_cust, q_oos, q_neg, q_safe, q_father]
        qs_rev = list(reversed(qs_fwd))
        b_fwd, _ = assess_v7_batch(qs_fwd, mode="evidence", custody_vocab="statutory_primary")
        b_rev, _ = assess_v7_batch(qs_rev, mode="evidence", custody_vocab="statutory_primary")
        for idx, q_item in enumerate(qs_fwd):
            rev_row = b_rev[len(qs_fwd) - 1 - idx]
            self.assertEqual(b_fwd[idx]["kept_ids"], rev_row["kept_ids"])
            self.assertEqual(b_fwd[idx]["court_live"], rev_row["court_live"])
            self.assertEqual(b_fwd[idx]["escalation_kinds"], rev_row["escalation_kinds"])
            self.assertEqual(b_fwd[idx]["prose"], rev_row["prose"])


class V7EvidenceAnchorTests(unittest.TestCase):
    """Lane 03 (recall swarm, C4): regression tests for the hardened
    evidence anchors in src/laya_v7_evidence.py. Fact-level checks use
    extract_grounded_v7 directly; a few end-to-end checks use assess_v7
    (mode="evidence") to pin the graph-visible behaviour, including the
    H13 guard: "money for my son's school fees" with NO exclusivity
    signal must NOT set child_maintenance_only (that would gate out
    pwdva-20 monetary relief for the wife)."""

    def _fact(self, text, key):
        from src.laya_v7_evidence import extract_grounded_v7

        return extract_grounded_v7(text)["facts"][key].status

    def _issue(self, text, key):
        from src.laya_v7_evidence import extract_grounded_v7

        return extract_grounded_v7(text)["issues"][key].intent

    def test_lockout_and_residence_story_forms(self):
        self.assertEqual(self._issue("He locked the door and would not let me in.", "residence"), "requested")
        self.assertEqual(self._fact("He locked the door and would not let me in.", "coercive_eviction_or_lockout"), "supported")
        self.assertEqual(
            self._issue("My mother-in-law asked me to leave my matrimony house and I was not taken back.", "residence"),
            "requested",
        )

    def test_dv_compensation_and_its_negation(self):
        self.assertEqual(
            self._issue(
                "He keeps beating me and fractured my hand. I want compensation for this mental harassment.",
                "dv_compensation",
            ),
            "requested",
        )
        # Explicitly declined compensation must not mint the claim, even
        # though "violence" is present in the same sentence.
        self.assertEqual(
            self._issue("I am not asking for compensation. I only want the violence at home to stop.", "dv_compensation"),
            "uncertain",
        )
        self.assertEqual(
            self._issue("I am not asking for compensation. I only want the violence at home to stop.", "violence"),
            "requested",
        )
        # Bare "violence" (not just "violent") is a violence signal.
        self.assertEqual(self._issue("I only want the violence at home to stop.", "violence"), "requested")

    def test_explicit_residence_order(self):
        self.assertEqual(
            self._fact("The court passed an order saying I can live in the house.", "explicit_residence_order_only"),
            "supported",
        )

    def test_stridhan_held_safe_and_refusal(self):
        self.assertEqual(self._issue("He will not give the gold back.", "stridhan"), "requested")
        # Gold safe with her parents = no claim (issue negated by design).
        self.assertEqual(self._issue("My stridhan is kept with my parents for safety.", "stridhan"), "denied")
        self.assertEqual(
            self._fact("My stridhan is kept with my parents for safety.", "stridhan_safe_in_own_possession"),
            "supported",
        )
        # An explicit refusal beats a possession statement in the same text.
        self.assertEqual(
            self._issue("He will not give the gold back. My stridhan is with my parents for safety.", "stridhan"),
            "requested",
        )
        # "Still with them" is held, even with no demand yet made.
        self.assertEqual(
            self._fact("Please help me. My gold is still with them, but I have never demanded it.", "stridhan_claim"),
            "supported",
        )

    def test_restitution_not_custody(self):
        self.assertEqual(
            self._issue("I want my husband to return home and live with me as husband and wife.", "restitution"),
            "requested",
        )
        self.assertEqual(
            self._issue("I want my husband to return home and live with me as husband and wife.", "custody"),
            "uncertain",
        )

    def test_decree_forms(self):
        self.assertEqual(self._fact("The court gave the divorce decree.", "decree"), "supported")

    def test_child_only_decimal_age_minor_speaker_and_nothing_for_myself(self):
        self.assertEqual(
            self._fact("I want maintenance only for my 2.5 yrs old son.", "child_maintenance_only"),
            "supported",
        )
        self.assertEqual(
            self._fact("I am 15 years old. Can I ask for support for myself?", "child_maintenance_only"),
            "supported",
        )
        self.assertEqual(
            self._fact("I am a 4-year-old child, and my father gives nothing for my studies. I need maintenance for my education.", "child_maintenance_only"),
            "supported",
        )
        # "nothing for myself" is a child-only signal, not a self-ask.
        self.assertEqual(
            self._fact("I want maintenance only for my child's education, nothing for myself.", "child_maintenance_only"),
            "supported",
        )
        # ...while a plain self-ask is not child-only.
        self.assertEqual(
            self._fact("I want maintenance for myself, not for my child.", "child_maintenance_only"),
            "denied",
        )

    def test_judicial_separation_paraphrase(self):
        self.assertEqual(
            self._fact(
                "We have been living apart for two years under a court order, but I do not want a divorce.",
                "judicial_separation_only",
            ),
            "supported",
        )
        self.assertEqual(
            self._issue(
                "We have been living apart for two years under a court order, but I do not want a divorce.",
                "divorce",
            ),
            "denied",
        )

    def test_nobody_negation_masks(self):
        # Coordinated denial: neither violence nor coercive lockout may fire.
        self.assertEqual(self._issue("Nobody has hit me or locked me out.", "violence"), "denied")
        self.assertEqual(
            self._fact("Nobody has hit me or locked me out.", "coercive_eviction_or_lockout"),
            "denied",
        )

    def test_mutual_and_divorce_soft_negations(self):
        self.assertEqual(self._fact("He refuses to agree to a mutual divorce.", "mutual_consent"), "denied")
        self.assertEqual(self._issue("She is not agreeing for the divorce.", "divorce"), "denied")
        self.assertEqual(
            self._issue("She will not agree to end the marriage, so a divorce is not possible now.", "divorce"),
            "denied",
        )

    def test_oos_override_and_rescue(self):
        self.assertEqual(self._fact("My wife's manager harasses her at work.", "in_scope"), "denied")
        self.assertEqual(
            self._fact(
                "My husband beats me and will not give my stridhan back. My husband's landlord also threatens us.",
                "in_scope",
            ),
            "supported",
        )

    def test_procedure_issue(self):
        self.assertEqual(
            self._issue("How do I proceed legally? What is the time limit to appeal?", "procedure"),
            "requested",
        )
        self.assertEqual(
            self._fact("What papers do I need to file a case for maintenance?", "procedure_how_to_asked"),
            "supported",
        )

    def test_h13_no_exclusivity_no_child_only(self):
        # Regression guard (16-Q H13): "money for my son's school fees"
        # with no "only" anywhere is a complaint about unpaid child
        # expenses, NOT a child-only claim. child_only=True here gates out
        # pwdva-20 for the wife (14/16 -> 13/16 on 2026-11-27).
        self.assertEqual(
            self._fact(
                "He beats me, throws me out of the house and gives no money for my son's school fees.",
                "child_maintenance_only",
            ),
            "denied",
        )

    def test_school_fees_pending_existing_order_interim(self):
        self.assertEqual(
            self._fact(
                "He is only paying her school fees excluding school bus transport, school dress.",
                "school_fees_fact",
            ),
            "supported",
        )
        self.assertEqual(self._fact("My divorce case goes on.", "proceeding_pending_hma"), "supported")
        self.assertEqual(
            self._fact(
                "The court ordered my husband to pay maintenance but he has not paid since January.",
                "existing_order_enforcement",
            ),
            "supported",
        )
        self.assertEqual(self._fact("What support can I get during the case?", "interim_asked"), "supported")

    def test_joint_name_and_final_settlement_and_kaanoon_custody(self):
        self.assertEqual(self._issue("Our flat is in joint name.", "joint_property"), "requested")
        self.assertEqual(
            self._issue("My husband agreed to pay 14 lakh final settlement to end the litigations.", "divorce"),
            "requested",
        )
        self.assertEqual(self._issue("He is not ready to give me my son.", "custody"), "requested")

    def test_end_to_end_h13_keeps_pwdva20(self):
        from src.laya_v7 import assess_v7

        r = assess_v7(
            "He beats me, throws me out of the house and gives no money for my son's school fees.",
            mode="evidence",
        )
        self.assertEqual(
            set(r["kept_ids"]), {"bnss-144", "pwdva-17", "pwdva-18", "pwdva-19", "pwdva-20"}
        )

    def test_end_to_end_lockout_and_child_only_father(self):
        from src.laya_v7 import assess_v7

        r = assess_v7("He locked the door and would not let me in.", mode="evidence")
        self.assertEqual(set(r["kept_ids"]), {"pwdva-17", "pwdva-18", "pwdva-19"})
        r = assess_v7(
            "My wife earns well and refuses to pay for our minor daughter's school fees.",
            mode="evidence",
        )
        self.assertEqual(set(r["kept_ids"]), {"bnss-144"})


if __name__ == "__main__":
    unittest.main()
