#!/usr/bin/env python3
"""LAYA v7.1 V71-P1-2 — clean synthetic + hard-negative corpus builder.

Generates a deterministic, seeded 8,000-example bilingual (EN + KN + Kanglish)
training/validation corpus PURELY from statutory grammars, paraphrase templates
and hard-negative perturbations. NEVER from test banks: no test-bank, ground-truth
or fixture question text is read, copied or paraphrased by this builder. Every
sentence below was written fresh from the statutory concepts (BNSS s.144 / s.144(3)
/ s.146, HMA ss.9/13/13B/24/25/26/27, PWDVA ss.17/18/19/20/22, GWA 1890, HMGA
s.6, BNS s.316, Births & Deaths Act 1969) and the hard-negative clusters in
docs/10x_plane.md §1.2 (V71-P1-2). Leakage is verified afterwards by
scripts/check_ngram_leakage.py (0 word 8-grams, cosine < 0.90).

Record schema (contract C2, docs/10x_swarm_state.md):
    {id, lang, text,
     issues: {issue: intent},          # all 11 issues, 4-class intent
     facts:  {fact: state},            # all 28 facts, 4-state
     enums:  {claimant_sex, claimant_role, modality_time},
     spans:  [{key, kind, text, start, end}],
     meta:   {cluster, blocks, split}}  # extra bookkeeping; Lane 03 may ignore

ISSUES (11): maintenance, custody, residence, divorce, stridhan, joint_property,
    violence, dv_compensation, restitution, birth_certificate, procedure.
    Intent: requested | incidental | denied | uncertain.
    - requested: the user asks for that remedy now.
    - incidental: mentioned as background/context, not asked now
      (e.g. "my divorce case is pending" while asking for maintenance).
    - denied: explicitly not wanted / negated ("I do not want a divorce").
    - uncertain: not mentioned / cannot be determined from the text.
    OOS (out-of-scope) records use "uncertain" for every issue and carry the
    signal in facts.in_scope = "denied".

FACTS (28): divorce_asked, mutual_consent, judicial_separation_only,
    restitution_asked, proceeding_pending_hma, being_filed, decree, money_fact,
    lump_sum_settlement, existing_order_enforcement, interim_asked,
    custody_claim, child_fact, minor_child, child_maintenance_only,
    school_fees_fact, child_safety_risk, residence_claim,
    coercive_eviction_or_lockout, explicit_residence_order_only, violence,
    dv_injury_comp_asked, stridhan_claim, stridhan_sold_or_mortgaged,
    demand_made, joint_property_claim, birth_cert_asked, in_scope.
    State: supported | denied | unknown | conflicting.
    Mapping notes for Lane 03 / Lane 01 (evidence.py names in brackets):
    - interim_asked == evidence interim_only_asked (interim relief while an
      HMA proceeding is pending); interim_asked "supported" also implies
      proceeding_pending_hma "supported" in these templates.
    - stridhan "safe in my own possession" is encoded as stridhan_claim
      "denied" (no claim), NOT as a separate fact.
    - urgent_safety_risk (graph dead key) is NOT a corpus fact; it is
      derivable as violence "supported" OR child_safety_risk "supported".
    - domestic_relationship, forum_question_asked, procedure_how_to_asked,
      first_demand_never_made, no_dispute_empty are NOT corpus facts; the
      procedure issue + in_scope + role/sex enums carry that signal.
    - school_fees_fact covers "school fees / tuition" mentions; a record may
      mention school fees only as the reason for a child-only maintenance ask.

ENUMS:
    claimant_sex:  "F" | "M" | "U"  (U = unknown/unstated)
    claimant_role: "spouse" | "parent" | "child" | "other"
                   ("other" also covers genuinely unstated role; "child" is
                   used only when the claimant speaks as the child.)
    modality_time: "present" | "past" | "future" | "hypothetical" | "quoted"

Span markup inside templates: [[key:phrase]] where key is a fact or issue
name; the builder strips the markup and records exact char offsets.

Languages: "en" (English), "kn" (Kannada script), "kn_roman" (Kanglish:
Romanised Kannada, often code-mixed with English legal words).
Kannada templates are plain, everyday Kannada written for this corpus; they
have NOT had a native-speaker audit yet — P2.1 should audit them before any
training run treats the KN split as gold (see lane status file).

Determinism: random.Random(SEED); same seed + same code => byte-identical
JSONL. No network, no GPU, no torch, stdlib only.

FREEZE (coordinator, 2026-11-27): once data/synthetic_v7_1/validation.jsonl
exists it is FROZEN — a rebuild regenerates train.jsonl only and never
rewrites validation.jsonl (see main(); --new-split only when the
coordinator orders a new split version). manifest.json records
frozen_validation_sha256 / frozen_validation_at / frozen_validation_note;
all validation-split numbers are measured against that exact file.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import random
import re
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

SEED = 7102
N_TOTAL = 8000
N_VAL = 500

ISSUES = [
    "maintenance", "custody", "residence", "divorce", "stridhan",
    "joint_property", "violence", "dv_compensation", "restitution",
    "birth_certificate", "procedure",
]
FACTS = [
    "divorce_asked", "mutual_consent", "judicial_separation_only",
    "restitution_asked", "proceeding_pending_hma", "being_filed", "decree",
    "money_fact", "lump_sum_settlement", "existing_order_enforcement",
    "interim_asked", "custody_claim", "child_fact", "minor_child",
    "child_maintenance_only", "school_fees_fact", "child_safety_risk",
    "residence_claim", "coercive_eviction_or_lockout",
    "explicit_residence_order_only", "violence", "dv_injury_comp_asked",
    "stridhan_claim", "stridhan_sold_or_mortgaged", "demand_made",
    "joint_property_claim", "birth_cert_asked", "in_scope",
]
INTENTS = ("requested", "incidental", "denied", "uncertain")
FACT_STATES = ("supported", "denied", "unknown", "conflicting")

# ---------------------------------------------------------------- slots
# {child_age} digit, {child_word} son/daughter/child, {amount} monthly income
# phrase, {duration} "for X" phrase, {gold_value} stridhan value phrase.
SLOTS = {
    "en": {
        "child_age": ["3", "4", "5", "6", "7", "8", "9", "10", "11", "12",
                    "13", "14", "15", "16"],
        "child_word": ["daughter", "son", "child"],
        "amount": ["twenty thousand rupees", "forty thousand rupees",
                   "fifty thousand rupees", "thirty thousand rupees",
                   "sixty thousand rupees", "twenty-five thousand rupees"],
        "duration": ["two years", "three years", "four years", "five years",
                     "six months", "one year", "eight months", "two months",
                     "nine months"],
        "gold_value": ["five lakh rupees", "two lakh rupees",
                       "three lakh rupees", "one lakh rupees",
                       "four lakh rupees"],
    },
    "kn": {
        "child_age": ["3", "4", "5", "6", "7", "8", "9", "10", "11", "12",
                    "13", "14", "15", "16"],
        "child_word": ["ಮಗಳು", "ಮಗ", "ಮಗು"],
        "amount": ["ಇಪ್ಪತ್ತು ಸಾವಿರ ರೂಪಾಯಿ", "ನಲವತ್ತು ಸಾವಿರ ರೂಪಾಯಿ",
                   "ಐವತ್ತು ಸಾವಿರ ರೂಪಾಯಿ", "ಮೂವತ್ತು ಸಾವಿರ ರೂಪಾಯಿ",
                   "ಅರವತ್ತು ಸಾವಿರ ರೂಪಾಯಿ", "ಇಪ್ಪತ್ತೈದು ಸಾವಿರ ರೂಪಾಯಿ"],
        "duration": ["ಎರಡು ವರ್ಷಗಳಿಂದ", "ಮೂರು ವರ್ಷಗಳಿಂದ",
                     "ನಾಲ್ಕು ವರ್ಷಗಳಿಂದ", "ಐದು ವರ್ಷಗಳಿಂದ",
                     "ಆರು ತಿಂಗಳಿಂದ", "ಒಂದು ವರ್ಷದಿಂದ",
                     "ಎಂಟು ತಿಂಗಳಿಂದ", "ಎರಡು ತಿಂಗಳಿಂದ"],
        "gold_value": ["ಐದು ಲಕ್ಷ ರೂಪಾಯಿ", "ಎರಡು ಲಕ್ಷ ರೂಪಾಯಿ",
                       "ಮೂರು ಲಕ್ಷ ರೂಪಾಯಿ", "ಒಂದು ಲಕ್ಷ ರೂಪಾಯಿ",
                       "ನಾಲ್ಕು ಲಕ್ಷ ರೂಪಾಯಿ"],
    },
    "kn_roman": {
        "child_age": ["3", "4", "5", "6", "7", "8", "9", "10", "11", "12",
                    "13", "14", "15", "16"],
        "child_word": ["magalu", "maga", "magu"],
        "amount": ["twenty thousand rupees", "forty thousand rupees",
                   "fifty thousand rupees", "thirty thousand rupees",
                   "sixty thousand rupees", "twenty-five thousand rupees"],
        "duration": ["two years inda", "three years inda", "four years inda",
                     "five years inda", "six months inda", "one year inda",
                     "eight months inda", "two months inda"],
        "gold_value": ["five lakh rupees", "two lakh rupees",
                       "three lakh rupees", "one lakh rupees",
                       "four lakh rupees"],
    },
}

# ---------------------------------------------------------------- blocks
# B(id, cluster, en=[...], kn=[...], ro=[...], issues={...}, facts={...},
#   enums={...})
# cluster: core | combo | hn_a | hn_b | hn_c | hn_d | hn_e | hn_f | neg | conflict


def B(bid, cluster, en, kn, ro, issues=None, facts=None, enums=None):
    return {"id": bid, "cluster": cluster, "en": en, "kn": kn, "ro": ro,
            "issues": issues or {}, "facts": facts or {},
            "enums": enums or {}}


F = "F"
M = "M"
SPOUSE = {"claimant_sex": F, "claimant_role": "spouse"}
SPOUSE_M = {"claimant_sex": M, "claimant_role": "spouse"}

BLOCKS = {}
def _reg(b):
    BLOCKS[b["id"]] = b
    return b

# --- core: maintenance -------------------------------------------------
_reg(B("maint_wife", "core",
    en=["My husband [[money_fact:has stopped giving me any money]] to run the home. I need [[maintenance:maintenance]] from him.",
        "My husband earns {amount} a month but [[money_fact:sends me nothing]] for food and rent."],
    kn=["ನನ್ನ ಗಂಡ [[money_fact:ಮನೆಗೆ ಹಣ ಕೊಡುತ್ತಿಲ್ಲ]]. ನನಗೆ [[maintenance:ಜೀವನಾಂಶ]] ಬೇಕು.",
        "ನನ್ನ ಗಂಡ ತಿಂಗಳಿಗೆ {amount} ಸಂಪಾದಿಸುತ್ತಾನೆ, ಆದರೆ [[money_fact:ನನಗೆ ಏನೂ ಕೊಡುವುದಿಲ್ಲ]]."],
    ro=["Nanna ganda [[money_fact:mane nadisalu hana koduvudannu nillisidanu]]. Nanage [[maintenance:jeevanamsha]] beku.",
        "Nanna ganda tingalige {amount} sampadistane, adare [[money_fact:nanage enu koduvudilla]]."],
    issues={"maintenance": "requested"},
    facts={"money_fact": "supported", "in_scope": "supported"},
    enums=dict(SPOUSE)))
_reg(B("maint_child_only", "core",
    en=["I want [[maintenance:maintenance]] only for my {child_age}-year-old {child_word}, for [[school_fees_fact:school fees]] and food.",
        "My husband gives nothing for our {child_word}. I need money only for the [[school_fees_fact:child's school fees]]."],
    kn=["ನನಗೆ {child_age} ವರ್ಷದ {child_word}ಗಾಗಿ ಮಾತ್ರ [[maintenance:ಜೀವನಾಂಶ]] ಬೇಕು, [[school_fees_fact:ಶಾಲಾ ಶುಲ್ಕ]] ಮತ್ತು ಊಟಕ್ಕಾಗಿ.",
        "ನನ್ನ ಗಂಡ ನಮ್ಮ {child_word}ಗೆ ಏನೂ ಕೊಡುವುದಿಲ್ಲ. [[school_fees_fact:ಮಗುವಿನ ಶಾಲಾ ಶುಲ್ಕ]]ಕ್ಕಾಗಿ ಮಾತ್ರ ಹಣ ಬೇಕು."],
    ro=["Nanage {child_age} varshada {child_word}gagi matra [[maintenance:jeevanamsha]] beku, [[school_fees_fact:shala shulka]] mattu utakkagi.",
        "Nanna ganda namma {child_word}ge enu koduvudilla. [[school_fees_fact:maguvina shala shulka]]kkagi matra hana beku."],
    issues={"maintenance": "requested"},
    facts={"money_fact": "supported", "child_maintenance_only": "supported",
           "child_fact": "supported", "minor_child": "supported",
           "school_fees_fact": "supported", "in_scope": "supported"},
    enums=dict(SPOUSE)))
_reg(B("maint_lump_sum", "core",
    en=["I want a [[lump_sum_settlement:lump sum]] payment instead of monthly [[maintenance:maintenance]] from my husband.",
        "Can I ask for a [[lump_sum_settlement:one-time lump sum settlement]] rather than monthly support?"],
    kn=["ತಿಂಗಳ [[maintenance:ಜೀವನಾಂಶ]] ಬದಲು ನನಗೆ [[lump_sum_settlement:ಒಟ್ಟು ಹಣ]] ಬೇಕು.",
        "ತಿಂಗಳ ಬೆಂಬಲದ ಬದಲು [[lump_sum_settlement:ಒಂದೇ ಬಾರಿಗೆ ಒಟ್ಟು ಹಣ]] ಕೇಳಬಹುದೇ?"],
    ro=["Tingala [[maintenance:jeevanamsha]] badalu nanage [[lump_sum_settlement:ottu hana]] beku.",
        "Tingala bembalada badalu [[lump_sum_settlement:onde barige ottu hana]] kelabahude?"],
    issues={"maintenance": "requested"},
    facts={"money_fact": "supported", "lump_sum_settlement": "supported",
           "in_scope": "supported"},
    enums=dict(SPOUSE)))
_reg(B("maint_interim_pending", "core",
    en=["My divorce case is pending in court. I need [[interim_asked:interim maintenance]] until the case ends.",
        "While our divorce case is going on, I want [[interim_asked:maintenance for now]], till the final order."],
    kn=["ನಮ್ಮ ವಿಚ್ಛೇದನ ಕೇಸ್ ಕೋರ್ಟ್‌ನಲ್ಲಿ ನಡೆಯುತ್ತಿದೆ. ಕೇಸ್ ಮುಗಿಯುವವರೆಗೆ ನನಗೆ [[interim_asked:ಮಧ್ಯಂತರ ಜೀವನಾಂಶ]] ಬೇಕು.",
        "ವಿಚ್ಛೇದನ ಕೇಸ್ ನಡೆಯುವಾಗ ನನಗೆ [[interim_asked:ಈಗ ಜೀವನಾಂಶ]] ಬೇಕು."],
    ro=["Namma divorce case court nalli nadeyuttide. Case mugiyuvarage nanage [[interim_asked:madhyantara jeevanamsha]] beku.",
        "Divorce case nadeyuvaga nanage [[interim_asked:ega jeevanamsha]] beku."],
    issues={"maintenance": "requested", "divorce": "incidental"},
    facts={"money_fact": "supported", "interim_asked": "supported",
           "proceeding_pending_hma": "supported", "in_scope": "supported"},
    enums=dict(SPOUSE)))
_reg(B("maint_post_decree", "core",
    en=["Our divorce is already decided by the court. I still need monthly [[maintenance:maintenance]] from my ex-husband.",
        "The court gave the divorce decree last year. I want [[maintenance:maintenance]] after the decree."],
    kn=["ನಮ್ಮ ವಿಚ್ಛೇದನವನ್ನು ಕೋರ್ಟ್ ಈಗಾಗಲೇ ತೀರ್ಮಾನಿಸಿದೆ. ನನ್ನ ಮಾಜಿ ಗಂಡನಿಂದ ಇನ್ನೂ ತಿಂಗಳ [[maintenance:ಜೀವನಾಂಶ]] ಬೇಕು.",
        "ಕೋರ್ಟ್ ಕಳೆದ ವರ್ಷ ವಿಚ್ಛೇದನ ತೀರ್ಪು ನೀಡಿತು. ತೀರ್ಪಿನ ನಂತರ [[maintenance:ಜೀವನಾಂಶ]] ಬೇಕು."],
    ro=["Namma divorce court egagale teermaniside. Nanna maji gandana inda innu tingala [[maintenance:jeevanamsha]] beku.",
        "Court kaleda varsha divorce teerpu needitu. Teerpina nantara [[maintenance:jeevanamsha]] beku."],
    issues={"maintenance": "requested", "divorce": "incidental"},
    facts={"money_fact": "supported", "decree": "supported",
           "in_scope": "supported"},
    enums=dict(SPOUSE)))
_reg(B("maint_arrears", "hn_e",
    en=["The court already ordered my husband to pay [[maintenance:maintenance]], but he has not paid for {duration}. I want the unpaid amount.",
        "My husband was ordered to pay monthly support, and he has missed payments for {duration}. How do I recover the arrears?",
        "The court ordered him to pay, and he paid for three months, then he stopped. What do I do now to get the unpaid money?"],
    kn=["ಕೋರ್ಟ್ ಈಗಾಗಲೇ ನನ್ನ ಗಂಡ ಜೀವನಾಂಶ ಕೊಡಬೇಕು ಎಂದು ಆದೇಶಿಸಿದೆ, ಆದರೆ ಅವನು {duration} ಕೊಟ್ಟಿಲ್ಲ. ಬಾಕಿ ಹಣ ಬೇಕು.",
        "ನನ್ನ ಗಂಡ ತಿಂಗಳ ಬೆಂಬಲ ಕೊಡಬೇಕು ಎಂದು ಆದೇಶವಿದೆ, {duration} ಕೊಟ್ಟಿಲ್ಲ. ಬಾಕಿ ಹಣವನ್ನು ಹೇಗೆ ಪಡೆಯುವುದು?",
        "ಕೋರ್ಟ್ ಅವನು ಕೊಡಬೇಕು ಎಂದು ಆದೇಶಿಸಿತು, ಅವನು ಮೂರು ತಿಂಗಳು ಕೊಟ್ಟನು, ನಂತರ ನಿಲ್ಲಿಸಿದನು. ಬಾಕಿ ಹಣ ಪಡೆಯಲು ಈಗ ನಾನು ಏನು ಮಾಡಬೇಕು?"],
    ro=["Court egagale nanna ganda jeevanamsha kodabeku anta adeshiside, adare avanu {duration} kottilla. Baki hana beku.",
        "Nanna ganda tingala bembala kodabeku anta adeshavide, {duration} kottilla. Baki hanavannu hege padeyuvudu?",
        "Court avanu kodabeku anta adeshisitu, avanu mooru tingalu kottanu, nantara nillisidanu. Baki hana padeyalu ega nanu enu madabeku?"],
    issues={"maintenance": "requested"},
    facts={"money_fact": "supported", "existing_order_enforcement": "supported",
           "in_scope": "supported"},
    enums=dict(SPOUSE)))
_reg(B("maint_vary", "hn_e",
    en=["My husband's salary has gone up since the maintenance order. I want the [[maintenance:maintenance]] amount increased.",
        "The maintenance was fixed two years ago, but my husband now earns much more. Can the amount be revised upwards?"],
    kn=["ಜೀವನಾಂಶ ಆದೇಶವಾದ ನಂತರ ನನ್ನ ಗಂಡನ ಸಂಬಳ ಹೆಚ್ಚಾಗಿದೆ. [[maintenance:ಜೀವನಾಂಶ]] ಮೊತ್ತ ಹೆಚ್ಚಿಸಬೇಕು.",
        "ಜೀವನಾಂಶವನ್ನು ಎರಡು ವರ್ಷಗಳ ಹಿಂದೆ ನಿಗದಿಪಡಿಸಲಾಗಿತ್ತು, ಆದರೆ ನನ್ನ ಗಂಡ ಈಗ ಹೆಚ್ಚು ಸಂಪಾದಿಸುತ್ತಾನೆ. ಮೊತ್ತ ಹೆಚ್ಚಿಸಬಹುದೇ?"],
    ro=["Jeevanamsha adeshavada nantara nanna gandana sambala hechagide. [[maintenance:jeevanamsha]] motta hechisabeku.",
        "Jeevanamsha vannu eradu varshagala hinde nigadipadisalagittu, adare nanna ganda ega hechu sampadistane. Motta hechisabahude?"],
    issues={"maintenance": "requested"},
    facts={"money_fact": "supported", "existing_order_enforcement": "supported",
           "in_scope": "supported"},
    enums=dict(SPOUSE)))
_reg(B("maint_elder_parent", "hn_e",
    en=["I am a 70-year-old mother. My son earns well but [[money_fact:gives me nothing]] for food and medicines. I need [[maintenance:maintenance]] from him.",
        "I am 68 years old and my son does not support me at all. Can a parent ask for [[maintenance:maintenance]] from a son?"],
    kn=["ನನಗೆ 70 ವರ್ಷ. ನನ್ನ ಮಗ ಚೆನ್ನಾಗಿ ಸಂಪಾದಿಸುತ್ತಾನೆ, ಆದರೆ [[money_fact:ಊಟ ಮತ್ತು ಔಷಧಿಗೆ ಏನೂ ಕೊಡುವುದಿಲ್ಲ]]. ಅವನಿಂದ [[maintenance:ಜೀವನಾಂಶ]] ಬೇಕು.",
        "ನನಗೆ 68 ವರ್ಷ, ನನ್ನ ಮಗ ನನ್ನನ್ನು ನೋಡಿಕೊಳ್ಳುವುದೇ ಇಲ್ಲ. ತಂದೆ-ತಾಯಿ ಮಗನಿಂದ [[maintenance:ಜೀವನಾಂಶ]] ಕೇಳಬಹುದೇ?"],
    ro=["Nanage 70 varsha. Nanna maga chennagi sampadistane, adare [[money_fact:uta mattu aushadhige enu koduvudilla]]. Avaninda [[maintenance:jeevanamsha]] beku.",
        "Nanage 68 varsha, nanna maga nannannu nodikolluvude illa. Tande-tayi maganinda [[maintenance:jeevanamsha]] kelabahude?"],
    issues={"maintenance": "requested"},
    facts={"money_fact": "supported", "in_scope": "supported"},
    enums={"claimant_sex": F, "claimant_role": "parent"}))
_reg(B("maint_male_self", "hn_e",
    en=["I am the husband. My wife earns {amount} a month and [[money_fact:gives me nothing]] for my living costs. I need [[maintenance:maintenance]] for myself.",
        "I am a husband with no income, and my wife refuses to support me. Can I ask for [[maintenance:maintenance]]?"],
    kn=["ನಾನು ಗಂಡ. ನನ್ನ ಹೆಂಡತಿ ತಿಂಗಳಿಗೆ {amount} ಸಂಪಾದಿಸುತ್ತಾಳೆ, ಆದರೆ [[money_fact:ನನ್ನ ಜೀವನ ವೆಚ್ಚಕ್ಕೆ ಏನೂ ಕೊಡುವುದಿಲ್ಲ]]. ನನಗೆ [[maintenance:ಜೀವನಾಂಶ]] ಬೇಕು.",
        "ನನಗೆ ಆದಾಯವಿಲ್ಲದ ಗಂಡ, ನನ್ನ ಹೆಂಡತಿ ನನ್ನನ್ನು ನೋಡಿಕೊಳ್ಳಲು ನಿರಾಕರಿಸುತ್ತಾಳೆ. ನಾನು [[maintenance:ಜೀವನಾಂಶ]] ಕೇಳಬಹುದೇ?"],
    ro=["Nanu ganda. Nanna hendati tingalige {amount} sampadistale, adare [[money_fact:nanna jeevana vechchakke enu koduvudilla]]. Nanage [[maintenance:jeevanamsha]] beku.",
        "Nanage adayavilla ganda, nanna hendati nannannu nodikollalu nirakaristale. Nanu [[maintenance:jeevanamsha]] kelabahude?"],
    issues={"maintenance": "requested"},
    facts={"money_fact": "supported", "in_scope": "supported"},
    enums=dict(SPOUSE_M)))
_reg(B("maint_father_child_only", "hn_e",
    en=["I am the father. I want money only for my {child_age}-year-old {child_word}'s [[school_fees_fact:school fees]] and books, nothing for myself.",
        "I am a father asking only for my {child_word}'s expenses. My wife gives nothing for the {child_word}'s schooling."],
    kn=["ನಾನು ತಂದೆ. ನನಗೆ {child_age} ವರ್ಷದ {child_word}ನ [[school_fees_fact:ಶಾಲಾ ಶುಲ್ಕ]] ಮತ್ತು ಪುಸ್ತಕಗಳಿಗಾಗಿ ಮಾತ್ರ ಹಣ ಬೇಕು, ನನಗಾಗಿ ಏನೂ ಬೇಡ.",
        "ನಾನು ತಂದೆ, ನನ್ನ {child_word}ನ ಖರ್ಚಿಗಾಗಿ ಮಾತ್ರ ಕೇಳುತ್ತಿದ್ದೇನೆ. ನನ್ನ ಹೆಂಡತಿ {child_word}ನ ಶಾಲೆಗೆ ಏನೂ ಕೊಡುವುದಿಲ್ಲ."],
    ro=["Nanu tande. Nanage {child_age} varshada {child_word}na [[school_fees_fact:shala shulka]] mattu pustakagaligagi matra hana beku, nanagagi enu beda.",
        "Nanu tande, nanna {child_word}na kharchigagi matra keluttiddene. Nanna hendati {child_word}na shalege enu koduvudilla."],
    issues={"maintenance": "requested"},
    facts={"money_fact": "supported", "child_maintenance_only": "supported",
           "child_fact": "supported", "minor_child": "supported",
           "school_fees_fact": "supported", "in_scope": "supported"},
    enums=dict(SPOUSE_M)))
_reg(B("maint_child_self", "core",
    en=["I am {child_age} years old. My father [[money_fact:does not pay for my school]] or my food. Can I ask for support for myself?",
        "I am a {child_age}-year-old {child_word}, and my father gives nothing for my studies. I need [[maintenance:maintenance]] for my education."],
    kn=["ನನಗೆ {child_age} ವರ್ಷ. ನನ್ನ ತಂದೆ [[money_fact:ನನ್ನ ಶಾಲೆಗೆ ಅಥವಾ ಊಟಕ್ಕೆ ಹಣ ಕೊಡುವುದಿಲ್ಲ]]. ನನಗಾಗಿ ಬೆಂಬಲ ಕೇಳಬಹುದೇ?",
        "ನಾನು {child_age} ವರ್ಷದ {child_word}, ನನ್ನ ತಂದೆ ನನ್ನ ಓದಿಗೆ ಏನೂ ಕೊಡುವುದಿಲ್ಲ. ನನ್ನ ಶಿಕ್ಷಣಕ್ಕಾಗಿ [[maintenance:ಜೀವನಾಂಶ]] ಬೇಕು."],
    ro=["Nanage {child_age} varsha. Nanna tande [[money_fact:nanna shalege athava utakke hana koduvudilla]]. Nanagagi bembala kelabahude?",
        "Nanu {child_age} varshada {child_word}, nanna tande nanna odige enu koduvudilla. Nanna shikshanakagi [[maintenance:jeevanamsha]] beku."],
    issues={"maintenance": "requested"},
    facts={"money_fact": "supported", "child_maintenance_only": "supported",
           "child_fact": "supported", "minor_child": "supported",
           "school_fees_fact": "supported", "in_scope": "supported"},
    enums={"claimant_sex": "U", "claimant_role": "child"}))

# --- core: custody ------------------------------------------------------
_reg(B("custody_mother", "core",
    en=["I want [[custody:custody]] of my {child_age}-year-old {child_word}. My {child_word} should live with me.",
        "Who will get my {child_age}-year-old {child_word}? I am asking that my {child_word} remain in my care.",
        "Is there any legal way for me to get custody of my baby? My husband took our baby away from me."],
    kn=["ನನ್ನ {child_age} ವರ್ಷದ {child_word}ನ [[custody:ಪಾಲನೆ]] ನನಗೆ ಬೇಕು. ನನ್ನ {child_word} ನನ್ನ ಜೊತೆ ಇರಬೇಕು.",
        "ನನ್ನ {child_age} ವರ್ಷದ {child_word} ಯಾರಿಗೆ ಸಿಗುತ್ತಾರೆ? ನನ್ನ {child_word} ನನ್ನ ಆರೈಕೆಯಲ್ಲಿ ಇರಬೇಕು ಎಂದು ಕೇಳುತ್ತಿದ್ದೇನೆ.",
        "ನನ್ನ ಮಗುವಿನ ಪಾಲನೆ ಪಡೆಯಲು ಯಾವುದಾದರೂ ಕಾನೂನುಬದ್ಧ ಮಾರ್ಗವಿದೆಯೇ? ನನ್ನ ಗಂಡ ನಮ್ಮ ಮಗುವನ್ನು ನನ್ನಿಂದ ಕರೆದುಕೊಂಡು ಹೋಗಿದ್ದಾನೆ."],
    ro=["Nanna {child_age} varshada {child_word}na [[custody:paalane]] nanage beku. Nanna {child_word} nanna jothe irabeku.",
        "Nanna {child_age} varshada {child_word} yarige siguttare? Nanna {child_word} nanna aaraikeyalli irabekendu keluttiddene.",
        "Nanna maguvina paalane padeyalu yavudadaru kanunubaddha margavideye? Nanna ganda namma maguvannu nanninda karedukondu hogiddane."],
    issues={"custody": "requested"},
    facts={"custody_claim": "supported", "child_fact": "supported",
           "minor_child": "supported", "in_scope": "supported"},
    enums=dict(SPOUSE)))
_reg(B("custody_father", "core",
    en=["I am the father, and I want [[custody:custody]] of my {child_age}-year-old {child_word}.",
        "My wife left with our {child_word}. I want my {child_word} back with me, and I am asking for [[custody:custody]]."],
    kn=["ನಾನು ತಂದೆ, ನನ್ನ {child_age} ವರ್ಷದ {child_word}ನ [[custody:ಪಾಲನೆ]] ನನಗೆ ಬೇಕು.",
        "ನನ್ನ ಹೆಂಡತಿ ನಮ್ಮ {child_word}ನೊಂದಿಗೆ ಹೋಗಿದ್ದಾಳೆ. ನನ್ನ {child_word} ನನ್ನ ಬಳಿ ಬೇಕು, [[custody:ಪಾಲನೆ]] ಕೇಳುತ್ತಿದ್ದೇನೆ."],
    ro=["Nanu tande, nanna {child_age} varshada {child_word}na [[custody:paalane]] nanage beku.",
        "Nanna hendati namma {child_word}nodige hogiddale. Nanna {child_word} nanna bali beku, [[custody:paalane]] keluttiddene."],
    issues={"custody": "requested"},
    facts={"custody_claim": "supported", "child_fact": "supported",
           "minor_child": "supported", "in_scope": "supported"},
    enums=dict(SPOUSE_M)))

# --- core: residence / violence -----------------------------------------
_reg(B("residence_thrown_out", "core",
    en=["My husband is [[residence_claim:throwing me out of the house]]. I have nowhere to go and I want to stay in my home.",
        "My in-laws are forcing me to leave the house. I want the right to keep living in our home."],
    kn=["ನನ್ನ ಗಂಡ [[residence_claim:ನನ್ನನ್ನು ಮನೆಯಿಂದ ಹೊರಹಾಕುತ್ತಿದ್ದಾನೆ]]. ನನಗೆ ಹೋಗಲು ಎಲ್ಲೂ ಇಲ್ಲ, ನನ್ನ ಮನೆಯಲ್ಲೇ ಇರಬೇಕು.",
        "ನನ್ನ ಅತ್ತೆ-ಮಾವ ನನ್ನನ್ನು ಮನೆ ಬಿಟ್ಟು ಹೋಗುವಂತೆ ಒತ್ತಾಯಿಸುತ್ತಿದ್ದಾರೆ. ನಮ್ಮ ಮನೆಯಲ್ಲೇ ಇರುವ ಹಕ್ಕು ಬೇಕು."],
    ro=["Nanna ganda [[residence_claim:nannannu maneyinda horahakuttiddane]]. Nanage hogalu ellu illa, nanna maneyalle irabeku.",
        "Nanna atte-mava nannannu mane bittu hoguvante ottayisuttiddare. Namma maneyalle iruva hakku beku."],
    issues={"residence": "requested"},
    facts={"residence_claim": "supported",
           "coercive_eviction_or_lockout": "supported",
           "in_scope": "supported"},
    enums=dict(SPOUSE)))
_reg(B("residence_live_in_house", "core",
    en=["I want to keep living in our shared house with my {child_word}. This is the home we have lived in for years.",
        "I only want to continue staying in the house where I have lived since my marriage."],
    kn=["ನನ್ನ {child_word}ನೊಂದಿಗೆ ನಮ್ಮ ಮನೆಯಲ್ಲೇ ಇರಲು ಬಯಸುತ್ತೇನೆ. ಇದು ನಾವು ವರ್ಷಗಳಿಂದ ವಾಸಿಸುತ್ತಿರುವ ಮನೆ.",
        "ಮದುವೆಯಾದಾಗಿನಿಂದ ವಾಸಿಸುತ್ತಿರುವ ಮನೆಯಲ್ಲೇ ಮುಂದುವರಿಯಲು ಬಯಸುತ್ತೇನೆ."],
    ro=["Nanna {child_word}nodige namma maneyalle iralu bayasuttene. Idu navu varshagalinda vaasisuttiruva mane.",
        "Maduveadaginda vaasisuttiruva maneyalle munduvariyalu bayasuttene."],
    issues={"residence": "requested"},
    facts={"residence_claim": "supported",
           "in_scope": "supported"},
    enums=dict(SPOUSE)))
_reg(B("residence_explicit_only", "hn_b",
    en=["I only want an order that I can live in our shared house. Nobody has hit me and nobody has locked me out.",
        "I am not asking for anything else. I just want a court order saying I may stay in the house I live in."],
    kn=["ನಮ್ಮ ಮನೆಯಲ್ಲಿ ನಾನು ಇರಬಹುದು ಎಂಬ ಆದೇಶ ಮಾತ್ರ ಬೇಕು. ಯಾರೂ ನನ್ನನ್ನು ಹೊಡೆದಿಲ್ಲ, ಯಾರೂ ನನ್ನನ್ನು ಹೊರಗೆ ಹಾಕಿಲ್ಲ.",
        "ನನಗೆ ಬೇರೆ ಏನೂ ಬೇಡ. ನಾನು ವಾಸಿಸುವ ಮನೆಯಲ್ಲಿ ಇರಬಹುದು ಎಂಬ ಕೋರ್ಟ್ ಆದೇಶ ಮಾತ್ರ ಬೇಕು."],
    ro=["Namma maneyalli nanu irabahudu emba adesha matra beku. Yaru nannannu hodedilla, yaru nannannu horage hakilla.",
        "Nanage bere enu beda. Nanu vaasisuva maneyalli irabahudu emba court adesha matra beku."],
    issues={"residence": "requested"},
    facts={"residence_claim": "supported",
           "explicit_residence_order_only": "supported",
           "coercive_eviction_or_lockout": "denied",
           "violence": "denied", "in_scope": "supported"},
    enums=dict(SPOUSE)))
_reg(B("lockout", "hn_b",
    en=["My husband [[coercive_eviction_or_lockout:locked me out of the house]] and threw my things outside. I cannot enter my own home.",
        "When I came back, the door was locked and my husband refused to let me in. I need to get back into the house."],
    kn=["ನನ್ನ ಗಂಡ [[coercive_eviction_or_lockout:ನನ್ನನ್ನು ಮನೆಯಿಂದ ಹೊರಗೆ ಬೀಗ ಹಾಕಿದನು]] ಮತ್ತು ನನ್ನ ವಸ್ತುಗಳನ್ನು ಹೊರಗೆ ಎಸೆದನು. ನಾನು ನನ್ನ ಮನೆಗೆ ಪ್ರವೇಶಿಸಲು ಸಾಧ್ಯವಿಲ್ಲ.",
        "ನಾನು ಹಿಂತಿರುಗಿದಾಗ ಬಾಗಿಲು ಬೀಗ ಹಾಕಿತ್ತು, ನನ್ನ ಗಂಡ ನನ್ನನ್ನು ಒಳಗೆ ಬಿಡಲಿಲ್ಲ. ಮನೆಗೆ ಮರಳಬೇಕು."],
    ro=["Nanna ganda [[coercive_eviction_or_lockout:nannannu maneyinda horage beega hakidanu]] mattu nanna vastugalannu horage esedanu. Nanu nanna manege praveshisalu sadhyavilla.",
        "Nanu hintirugidaga bagilu beega hakittu, nanna ganda nannannu olage bidalilla. Manege maralabeku."],
    issues={"residence": "requested"},
    facts={"residence_claim": "supported",
           "coercive_eviction_or_lockout": "supported",
           "in_scope": "supported"},
    enums=dict(SPOUSE)))
_reg(B("violence_beats", "core",
    en=["My husband [[violence:beats me]] at home. I am afraid for my safety and I need protection.",
        "My husband hits me whenever he drinks. I need help to stop the [[violence:violence]] at home.",
        "My husband is a habitual drinker and beats me regularly. Last week he hurt my hand badly, and I had to rush to hospital."],
    kn=["ನನ್ನ ಗಂಡ ಮನೆಯಲ್ಲಿ [[violence:ನನ್ನನ್ನು ಹೊಡೆಯುತ್ತಾನೆ]]. ನನ್ನ ಸುರಕ್ಷತೆಗಾಗಿ ನನಗೆ ರಕ್ಷಣೆ ಬೇಕು.",
        "ನನ್ನ ಗಂಡ ಕುಡಿದಾಗಲೆಲ್ಲ ನನ್ನನ್ನು ಹೊಡೆಯುತ್ತಾನೆ. ಮನೆಯಲ್ಲಿ [[violence:ಹಿಂಸೆ]] ನಿಲ್ಲಿಸಲು ಸಹಾಯ ಬೇಕು.",
        "ನನ್ನ ಗಂಡ ಅಭ್ಯಾಸದ ಕುಡುಕ, ನನ್ನನ್ನು ನಿಯಮಿತವಾಗಿ ಹೊಡೆಯುತ್ತಾನೆ. ಕಳೆದ ವಾರ ಅವನು ನನ್ನ ಕೈಗೆ ತೀವ್ರವಾಗಿ ಗಾಯ ಮಾಡಿದನು, ನಾನು ಆಸ್ಪತ್ರೆಗೆ ಓಡಬೇಕಾಯಿತು."],
    ro=["Nanna ganda maneyalli [[violence:nannannu hodeyuttane]]. Nanna surakshategagi nanage rakshane beku.",
        "Nanna ganda kudidagale nannannu hodeyuttane. Maneyalli [[violence:himse]] nillisalu sahaya beku.",
        "Nanna ganda abhyasada kuduka, nannannu niyamitavagi hodeyuttane. Kaleda vara avanu nanna kaige teevravagi gaya madidanu, nanu aspatrege odabekayitu."],
    issues={"violence": "requested"},
    facts={"violence": "supported", "in_scope": "supported"},
    enums=dict(SPOUSE)))
_reg(B("violence_threats", "core",
    en=["My husband [[violence:says he will kill me]] if I tell anyone about it. I live in fear every day.",
        "My in-laws abuse me with bad words and threaten to throw me out. I need protection from this harassment.",
        "My husband says I should not dare to ask for a single rupee, or he will beat me again. I live in fear of asking for anything."],
    kn=["ನಾನು ಯಾರಿಗಾದರೂ ಹೇಳಿದರೆ ನನ್ನ ಗಂಡ [[violence:ನನ್ನ ಪ್ರಾಣ ತೆಗೆಯುತ್ತೇನೆ ಎಂದು ಹೇಳುತ್ತಾನೆ]]. ಪ್ರತಿದಿನ ಭಯದಲ್ಲಿ ಬದುಕುತ್ತಿದ್ದೇನೆ.",
        "ನನ್ನ ಅತ್ತೆ-ಮಾವ ಕೆಟ್ಟ ಮಾತುಗಳಿಂದ ನನ್ನನ್ನು ನಿಂದಿಸುತ್ತಾರೆ ಮತ್ತು ಹೊರಹಾಕುವುದಾಗಿ ಬೆದರಿಸುತ್ತಾರೆ. ಈ ಕಿರುಕುಳದಿಂದ ರಕ್ಷಣೆ ಬೇಕು.",
        "ಒಂದು ರೂಪಾಯಿಯನ್ನೂ ಕೇಳಲು ಧೈರ್ಯ ಮಾಡಬಾರದು ಎಂದು ನನ್ನ ಗಂಡ ಹೇಳುತ್ತಾನೆ, ಇಲ್ಲದಿದ್ದರೆ ಮತ್ತೆ ಹೊಡೆಯುತ್ತೇನೆ ಎನ್ನುತ್ತಾನೆ. ಏನನ್ನೂ ಕೇಳಲು ನನಗೆ ಭಯವಾಗುತ್ತದೆ."],
    ro=["Nanu yarigadaroo helidare nanna ganda [[violence:nanna prana tegeyuttene anta heluttane]]. Pratidina bhayadalli badukuttiddene.",
        "Nanna atte-mava ketta matugalinda nannannu nindisuttare mattu horahakuvudagi bedarisuttare. Ee kirukula inda rakshane beku.",
        "Ondu rupayiyannu kelalu dhairya madabaradu anta nanna ganda heluttane, illadiddare matte hodeyuttene ennuttane. Enannu kelalu nanage bhayavaguttade."],
    issues={"violence": "requested"},
    facts={"violence": "supported", "in_scope": "supported"},
    enums=dict(SPOUSE)))
_reg(B("violence_dv_comp", "hn_b",
    en=["My husband beat me badly and I had to go to hospital. I want [[dv_compensation:compensation for my injuries]] and medical costs.",
        "I was injured by my husband's beating and spent money on treatment. I want the court to order payment for my injuries."],
    kn=["ನನ್ನ ಗಂಡ ನನ್ನನ್ನು ತೀವ್ರವಾಗಿ ಹೊಡೆದನು, ನಾನು ಆಸ್ಪತ್ರೆಗೆ ಹೋಗಬೇಕಾಯಿತು. ನನ್ನ ಗಾಯಗಳು ಮತ್ತು ಚಿಕಿತ್ಸೆಗಾಗಿ [[dv_compensation:ಪರಿಹಾರ]] ಬೇಕು.",
        "ನನ್ನ ಗಂಡನ ಹೊಡೆತದಿಂದ ಗಾಯಗೊಂಡೆ, ಚಿಕಿತ್ಸೆಗಾಗಿ ಹಣ ಖರ್ಚು ಮಾಡಿದೆ. ನನ್ನ ಗಾಯಗಳಿಗಾಗಿ ಹಣ ನೀಡುವಂತೆ ಕೋರ್ಟ್ ಆದೇಶಿಸಬೇಕು."],
    ro=["Nanna ganda nannannu teevravagi hodedanu, nanu aspatrege hogabekayitu. Nanna gayagalu mattu chikitsegagi [[dv_compensation:parihara]] beku.",
        "Nanna gandana hodetinda gayagondedu, chikitsegagi hana kharchu madide. Nanna gayagaligagi hana needuvante court adeshisabeku."],
    issues={"violence": "requested", "dv_compensation": "requested"},
    facts={"violence": "supported", "dv_injury_comp_asked": "supported",
           "in_scope": "supported"},
    enums=dict(SPOUSE)))
_reg(B("violence_child_risk", "core",
    en=["My husband drinks and beats our {child_word} too. I fear for my {child_word}'s safety at home.",
        "My husband is violent at home and my {child_age}-year-old {child_word} is not safe with him."],
    kn=["ನನ್ನ ಗಂಡ ಕುಡಿದು ನಮ್ಮ {child_word}ನನ್ನೂ ಹೊಡೆಯುತ್ತಾನೆ. ಮನೆಯಲ್ಲಿ ನನ್ನ {child_word}ನ ಸುರಕ್ಷತೆಯ ಬಗ್ಗೆ ಭಯವಿದೆ.",
        "ನನ್ನ ಗಂಡ ಮನೆಯಲ್ಲಿ ಹಿಂಸಾತ್ಮಕವಾಗಿ ವರ್ತಿಸುತ್ತಾನೆ, ನನ್ನ {child_age} ವರ್ಷದ {child_word} ಅವನ ಜೊತೆ ಸುರಕ್ಷಿತವಾಗಿಲ್ಲ."],
    ro=["Nanna ganda kudidu namma {child_word}nannu hodeyuttane. Maneyalli nanna {child_word}na surakshateya bagge bhayavide.",
        "Nanna ganda maneyalli himsatmakavagi vartistane, nanna {child_age} varshada {child_word} avana jothe surakshitavagilla."],
    issues={"violence": "requested"},
    facts={"violence": "supported", "child_safety_risk": "supported",
           "child_fact": "supported", "minor_child": "supported",
           "in_scope": "supported"},
    enums=dict(SPOUSE)))

# --- core: divorce / restitution / judicial separation -------------------
_reg(B("divorce_want", "core",
    en=["My marriage has broken down completely. I want a [[divorce:divorce]] from my husband.",
        "I no longer want to stay married. I want to end my marriage legally through [[divorce:divorce]]."],
    kn=["ನನ್ನ ಮದುವೆ ಸಂಪೂರ್ಣವಾಗಿ ಮುರಿದುಬಿದ್ದಿದೆ. ನನ್ನ ಗಂಡನಿಂದ [[divorce:ವಿಚ್ಛೇದನ]] ಬೇಕು.",
        "ನಾನು ಇನ್ನು ಮದುವೆಯಲ್ಲಿರಲು ಬಯಸುವುದಿಲ್ಲ. [[divorce:ವಿಚ್ಛೇದನ]] ಮೂಲಕ ನನ್ನ ಮದುವೆಯನ್ನು ಕಾನೂನುಬದ್ಧವಾಗಿ ಕೊನೆಗೊಳಿಸಲು ಬಯಸುತ್ತೇನೆ."],
    ro=["Nanna maduve sampurnavagi muridubiddide. Nanna gandana inda [[divorce:vichchhedana]] beku.",
        "Nanu innu maduveyalliralu bayasuvudilla. [[divorce:vichchhedana]] moolaka nanna maduveyannu kanunubaddhavagi konegolisalu bayasuttene."],
    issues={"divorce": "requested"},
    facts={"divorce_asked": "supported", "in_scope": "supported"},
    enums=dict(SPOUSE)))
_reg(B("divorce_mutual", "core",
    en=["My husband and I both agree to end the marriage. We want a [[divorce:divorce]] by [[mutual_consent:mutual consent]].",
        "We have decided together to separate. We want a [[mutual_consent:mutual consent divorce]]."],
    kn=["ನನ್ನ ಗಂಡ ಮತ್ತು ನಾನು ಮದುವೆ ಕೊನೆಗೊಳಿಸಲು ಒಪ್ಪಿದ್ದೇವೆ. [[mutual_consent:ಪರಸ್ಪರ ಒಪ್ಪಿಗೆ]]ಯಿಂದ [[divorce:ವಿಚ್ಛೇದನ]] ಬೇಕು.",
        "ನಾವು ಒಟ್ಟಿಗೆ ಬೇರೆಯಾಗಲು ನಿರ್ಧರಿಸಿದ್ದೇವೆ. [[mutual_consent:ಪರಸ್ಪರ ಒಪ್ಪಿಗೆಯ ವಿಚ್ಛೇದನ]] ಬೇಕು."],
    ro=["Nanna ganda mattu nanu maduve konegolisalu oppideve. [[mutual_consent:paraspara oppige]]yinda [[divorce:vichchhedana]] beku.",
        "Navu ottige bereyagalu nirdharisiddeve. [[mutual_consent:paraspara oppigeya vichchhedana]] beku."],
    issues={"divorce": "requested"},
    facts={"divorce_asked": "supported", "mutual_consent": "supported",
           "in_scope": "supported"},
    enums=dict(SPOUSE)))
_reg(B("divorce_pending", "hn_c",
    en=["My divorce case is already pending in the Family Court. I need money to live on while the case goes on.",
        "Our divorce petition is pending before the court. I want to know what support I can get during the case."],
    kn=["ನನ್ನ ವಿಚ್ಛೇದನ ಕೇಸ್ ಈಗಾಗಲೇ ಕೌಟುಂಬಿಕ ನ್ಯಾಯಾಲಯದಲ್ಲಿ ನಡೆಯುತ್ತಿದೆ. ಕೇಸ್ ನಡೆಯುವಾಗ ಬದುಕಲು ಹಣ ಬೇಕು.",
        "ನಮ್ಮ ವಿಚ್ಛೇದನ ಅರ್ಜಿ ಕೋರ್ಟ್‌ನಲ್ಲಿ ನಡೆಯುತ್ತಿದೆ. ಕೇಸ್ ನಡೆಯುವಾಗ ಏನು ಬೆಂಬಲ ಸಿಗುತ್ತದೆ ಎಂದು ತಿಳಿಯಬೇಕು."],
    ro=["Nanna divorce case egagale koutumbika nyayalayadalli nadeyuttide. Case nadeyuvaga badukalu hana beku.",
        "Namma divorce arji court nalli nadeyuttide. Case nadeyuvaga enu bembala siguttade anta tiliyabeku."],
    issues={"divorce": "incidental", "maintenance": "requested"},
    facts={"proceeding_pending_hma": "supported", "divorce_asked": "unknown",
           "money_fact": "supported", "in_scope": "supported"},
    enums=dict(SPOUSE)))
_reg(B("divorce_being_filed", "hn_c",
    en=["I am [[being_filed:filing for divorce]] next week. I have already spoken to a lawyer about the petition.",
        "I will file a divorce petition next month. I want to know what I should do first."],
    kn=["ನಾನು ಮುಂದಿನ ವಾರ [[being_filed:ವಿಚ್ಛೇದನಕ್ಕಾಗಿ ಅರ್ಜಿ ಹಾಕುತ್ತಿದ್ದೇನೆ]]. ಅರ್ಜಿಯ ಬಗ್ಗೆ ವಕೀಲರೊಂದಿಗೆ ಈಗಾಗಲೇ ಮಾತನಾಡಿದ್ದೇನೆ.",
        "ನಾನು ಮುಂದಿನ ತಿಂಗಳು ವಿಚ್ಛೇದನ ಅರ್ಜಿ ಹಾಕುತ್ತೇನೆ. ಮೊದಲು ಏನು ಮಾಡಬೇಕು ಎಂದು ತಿಳಿಯಬೇಕು."],
    ro=["Nanu mundina vara [[being_filed:vichchhedanakagi arji hakuttiddene]]. Arjiya bagge vakilarondige egagale matanadiddene.",
        "Nanu mundina tingalu divorce arji hakuttene. Modalu enu madabeku anta tiliyabeku."],
    issues={"divorce": "requested"},
    facts={"being_filed": "supported", "divorce_asked": "supported",
           "in_scope": "supported"},
    enums={"claimant_sex": F, "claimant_role": "spouse",
           "modality_time": "future"}))
_reg(B("divorce_js_only", "hn_c",
    en=["I want [[judicial_separation_only:judicial separation]] only. I do not want a [[divorce:divorce]].",
        "I want to live separately from my husband with a court order, but I do not want to end the marriage."],
    kn=["ನನಗೆ [[judicial_separation_only:ನ್ಯಾಯಾಂಗ ಬೇರ್ಪಡಿಕೆ]] ಮಾತ್ರ ಬೇಕು. ನನಗೆ [[divorce:ವಿಚ್ಛೇದನ]] ಬೇಡ.",
        "ಕೋರ್ಟ್ ಆದೇಶದೊಂದಿಗೆ ನನ್ನ ಗಂಡನಿಂದ ಬೇರೆಯಾಗಿ ವಾಸಿಸಲು ಬಯಸುತ್ತೇನೆ, ಆದರೆ ಮದುವೆ ಕೊನೆಗೊಳಿಸಲು ಬಯಸುವುದಿಲ್ಲ."],
    ro=["Nanage [[judicial_separation_only:nyayanga berpadike]] matra beku. Nanage [[divorce:vichchhedana]] beda.",
        "Court adeshadondige nanna gandana inda bereyagi vaasisalu bayasuttene, adare maduve konegolisalu bayasuvudilla."],
    issues={"divorce": "denied"},
    facts={"judicial_separation_only": "supported",
           "divorce_asked": "denied", "in_scope": "supported"},
    enums=dict(SPOUSE)))
_reg(B("divorce_restitution", "hn_c",
    en=["I do not want a divorce. I want my husband to [[restitution:come back and live with me]] as husband and wife.",
        "My husband left the house. I want the court to ask him to return home and live with me again."],
    kn=["ನನಗೆ ವಿಚ್ಛೇದನ ಬೇಡ. ನನ್ನ ಗಂಡ [[restitution:ಮರಳಿ ಬಂದು ನನ್ನ ಜೊತೆ ಗಂಡ-ಹೆಂಡತಿಯಾಗಿ ಬದುಕಬೇಕು]] ಎಂದು ಬಯಸುತ್ತೇನೆ.",
        "ನನ್ನ ಗಂಡ ಮನೆ ಬಿಟ್ಟು ಹೋಗಿದ್ದಾನೆ. ಅವನು ಮನೆಗೆ ಮರಳಿ ನನ್ನ ಜೊತೆ ವಾಸಿಸಬೇಕು ಎಂದು ಕೋರ್ಟ್ ಕೇಳಬೇಕು."],
    ro=["Nanage divorce beda. Nanna ganda [[restitution:marali bandu nanna jothe ganda-hendatiyagi badukabeku]] anta bayasuttene.",
        "Nanna ganda mane bittu hogiddane. Avanu manege marali nanna jothe vaasisabeku anta court kelabeku."],
    issues={"restitution": "requested", "divorce": "denied"},
    facts={"restitution_asked": "supported", "divorce_asked": "denied",
           "in_scope": "supported"},
    enums=dict(SPOUSE)))
_reg(B("divorce_decree_done", "hn_c",
    en=["The court already passed our divorce decree last year. I only want to know about maintenance after the decree.",
        "Our divorce was decided by the court six months ago. What support can I get now?"],
    kn=["ಕೋರ್ಟ್ ಕಳೆದ ವರ್ಷ ನಮ್ಮ ವಿಚ್ಛೇದನ ತೀರ್ಪು ನೀಡಿತು. ತೀರ್ಪಿನ ನಂತರದ ಜೀವನಾಂಶದ ಬಗ್ಗೆ ಮಾತ್ರ ತಿಳಿಯಬೇಕು.",
        "ನಮ್ಮ ವಿಚ್ಛೇದನವನ್ನು ಕೋರ್ಟ್ ಆರು ತಿಂಗಳ ಹಿಂದೆ ತೀರ್ಮಾನಿಸಿತು. ಈಗ ನನಗೆ ಏನು ಬೆಂಬಲ ಸಿಗುತ್ತದೆ?"],
    ro=["Court kaleda varsha namma divorce teerpu needitu. Teerpina nantarada jeevanamshada bagge matra tiliyabeku.",
        "Namma divorce vannu court aaru tingala hinde teermanisitu. Eega nanage enu bembala siguttade?"],
    issues={"divorce": "incidental", "maintenance": "requested"},
    facts={"decree": "supported", "divorce_asked": "unknown",
           "money_fact": "supported", "in_scope": "supported"},
    enums=dict(SPOUSE)))

# --- core: stridhan / joint property / birth certificate -----------------
_reg(B("stridhan_held", "core",
    en=["My [[stridhan_claim:gold worth {gold_value}]] given by my parents is held by my husband's family. I have asked for it back several times and they [[demand_made:refuse to give it back]].",
        "My wedding jewellery is kept by my in-laws. I asked for it back and they refused to give it.",
        "I have kept a list of all my jewellery, with photos, and everything is in my husband's house. I have asked for it back many times."],
    kn=["ನನ್ನ ಪೋಷಕರು ಕೊಟ್ಟ [[stridhan_claim:{gold_value} ಮೌಲ್ಯದ ಚಿನ್ನ]]ವನ್ನು ನನ್ನ ಗಂಡನ ಮನೆಯವರು ಇಟ್ಟುಕೊಂಡಿದ್ದಾರೆ. ಹಲವು ಬಾರಿ ಕೇಳಿದರೂ ಅದನ್ನು [[demand_made:ಹಿಂದಿರುಗಿಸಲು ನಿರಾಕರಿಸುತ್ತಿದ್ದಾರೆ]].",
        "ನನ್ನ ಮದುವೆಯ ಆಭರಣಗಳನ್ನು ನನ್ನ ಅತ್ತೆ-ಮಾವ ಇಟ್ಟುಕೊಂಡಿದ್ದಾರೆ. ವಾಪಸ್ ಕೇಳಿದೆ, ಅವರು ಕೊಡಲು ನಿರಾಕರಿಸಿದರು.",
        "ನನ್ನ ಎಲ್ಲಾ ಆಭರಣಗಳ ಪಟ್ಟಿಯನ್ನು ಫೋಟೋಗಳೊಂದಿಗೆ ಇಟ್ಟುಕೊಂಡಿದ್ದೇನೆ, ಎಲ್ಲವೂ ನನ್ನ ಗಂಡನ ಮನೆಯಲ್ಲಿದೆ. ಹಲವು ಬಾರಿ ವಾಪಸ್ ಕೇಳಿದ್ದೇನೆ."],
    ro=["Nanna poshakaru kotta [[stridhan_claim:{gold_value} maulyada chinnavannu]] nanna gandana maneyavaru ittukondiddare. Halavu bari kelidaru adannu [[demand_made:hindirugisalu nirakarisuttiddare]].",
        "Nanna maduveya abharanagalannu nanna atte-mava ittukondiddare. Vapas kelide, avaru kodalu nirakarisidaru.",
        "Nanna ella abharanagala pattiyannu photogalondige ittukondiddene, ellavu nanna gandana maneyallide. Halavu bari vapas keliddene."],
    issues={"stridhan": "requested"},
    facts={"stridhan_claim": "supported", "demand_made": "supported",
           "in_scope": "supported"},
    enums=dict(SPOUSE)))
_reg(B("stridhan_sold", "hn_d",
    en=["My husband [[stridhan_sold_or_mortgaged:sold my gold jewellery]] without asking me. I want my [[stridhan_claim:gold]] back or its value.",
        "My in-laws pawned my wedding gold. I want to recover the money for my [[stridhan_claim:stridhan]]."],
    kn=["ನನ್ನ ಗಂಡ ನನ್ನನ್ನು ಕೇಳದೆ [[stridhan_sold_or_mortgaged:ನನ್ನ ಚಿನ್ನಾಭರಣವನ್ನು ಮಾರಿಬಿಟ್ಟನು]]. ನನ್ನ [[stridhan_claim:ಚಿನ್ನ]] ಅಥವಾ ಅದರ ಮೌಲ್ಯ ವಾಪಸ್ ಬೇಕು.",
        "ನನ್ನ ಅತ್ತೆ-ಮಾವ ನನ್ನ ಮದುವೆಯ ಚಿನ್ನವನ್ನು ಅಡವಿಟ್ಟರು. ನನ್ನ [[stridhan_claim:ಚಿನ್ನ]]ಕ್ಕಾಗಿ ಹಣ ವಾಪಸ್ ಪಡೆಯಬೇಕು."],
    ro=["Nanna ganda nannannu kelade [[stridhan_sold_or_mortgaged:nanna chinnabharanavannu maribittanu]]. Nanna [[stridhan_claim:chinna]] athava adara maulya vapas beku.",
        "Nanna atte-mava nanna maduveya chinnavannu adavittaru. Nanna [[stridhan_claim:chinna]]kkagi hana vapas padeyabeku."],
    issues={"stridhan": "requested"},
    facts={"stridhan_claim": "supported",
           "stridhan_sold_or_mortgaged": "supported",
           "demand_made": "supported", "in_scope": "supported"},
    enums=dict(SPOUSE)))
_reg(B("stridhan_safe", "hn_d",
    en=["My gold is [[stridhan_claim:safe in my own locker]] and nobody has taken it. I only want to know about maintenance.",
        "My jewellery is with me and there is no dispute about it. My question is only about monthly support."],
    kn=["ನನ್ನ ಚಿನ್ನ [[stridhan_claim:ನನ್ನ ಸ್ವಂತ ಲಾಕರ್‌ನಲ್ಲಿ ಸುರಕ್ಷಿತವಾಗಿದೆ]], ಯಾರೂ ತೆಗೆದುಕೊಂಡಿಲ್ಲ. ನನಗೆ ಜೀವನಾಂಶದ ಬಗ್ಗೆ ಮಾತ್ರ ತಿಳಿಯಬೇಕು.",
        "ನನ್ನ ಆಭರಣಗಳು ನನ್ನ ಬಳಿಯೇ ಇವೆ, ಅವುಗಳ ಬಗ್ಗೆ ಯಾವುದೇ ವಿವಾದವಿಲ್ಲ. ನನ್ನ ಪ್ರಶ್ನೆ ತಿಂಗಳ ಬೆಂಬಲದ ಬಗ್ಗೆ ಮಾತ್ರ."],
    ro=["Nanna chinna [[stridhan_claim:nanna swanta locker nalli surakshitavagide]], yaru tegedukondilla. Nanage jeevanamshada bagge matra tiliyabeku.",
        "Nanna abharanagalu nanna baliye ive, avugala bagge yavude vivadavilla. Nanna prashne tingala bembalada bagge matra."],
    issues={"stridhan": "denied", "maintenance": "requested"},
    facts={"stridhan_claim": "denied", "money_fact": "supported",
           "in_scope": "supported"},
    enums=dict(SPOUSE)))
_reg(B("stridhan_never_asked", "hn_d",
    en=["I have [[demand_made:never asked]] my in-laws for my gold back. Can I ask for my [[stridhan_claim:stridhan]] now?",
        "My wedding gold is still with my husband's family, but I have not demanded it yet. How do I ask for it?"],
    kn=["ನಾನು ನನ್ನ ಅತ್ತೆ-ಮಾವನನ್ನು ಚಿನ್ನ ವಾಪಸ್ ಕೇಳಿಯೇ ಇಲ್ಲ. ಈಗ ನನ್ನ [[stridhan_claim:ಚಿನ್ನ]] ಕೇಳಬಹುದೇ?",
        "ನನ್ನ ಮದುವೆಯ ಚಿನ್ನ ಇನ್ನೂ ನನ್ನ ಗಂಡನ ಮನೆಯಲ್ಲಿದೆ, ಆದರೆ ನಾನು ಇನ್ನೂ ಕೇಳಿಲ್ಲ. ಅದನ್ನು ಹೇಗೆ ಕೇಳುವುದು?"],
    ro=["Nanu nanna atte-mavanannu chinna vapas keliye illa. Eega nanna [[stridhan_claim:chinna]] kelabahude?",
        "Nanna maduveya chinna innu nanna gandana maneyallide, adare nanu innu kelilla. Adannu hege keluvudu?"],
    issues={"stridhan": "requested"},
    facts={"stridhan_claim": "supported", "demand_made": "denied",
           "in_scope": "supported"},
    enums=dict(SPOUSE)))
_reg(B("joint_property", "core",
    en=["My husband and I bought a flat together in both our names. I want my share of this [[joint_property_claim:joint property]].",
        "We own a house jointly, and I want the court to divide our [[joint_property_claim:joint property]] fairly."],
    kn=["ನನ್ನ ಗಂಡ ಮತ್ತು ನಾನು ಇಬ್ಬರ ಹೆಸರಿನಲ್ಲಿ ಒಂದು ಫ್ಲ್ಯಾಟ್ ಖರೀದಿಸಿದೆವು. ಈ [[joint_property_claim:ಜಂಟಿ ಆಸ್ತಿ]]ಯಲ್ಲಿ ನನ್ನ ಪಾಲು ಬೇಕು.",
        "ನಾವು ಜಂಟಿಯಾಗಿ ಮನೆ ಹೊಂದಿದ್ದೇವೆ, ನಮ್ಮ [[joint_property_claim:ಜಂಟಿ ಆಸ್ತಿ]]ಯನ್ನು ನ್ಯಾಯಯುತವಾಗಿ ವಿಭಜಿಸಲು ಕೋರ್ಟ್‌ಗೆ ಕೇಳಬೇಕು."],
    ro=["Nanna ganda mattu nanu ibbara hesarinalli ondu flat khareedisidevu. Ee [[joint_property_claim:janti asti]]yalli nanna palu beku.",
        "Navu jantiyagi mane hondiddeve, namma [[joint_property_claim:janti asti]]yannu nyayayutavagi vibhajisalu court ge kelabeku."],
    issues={"joint_property": "requested"},
    facts={"joint_property_claim": "supported", "in_scope": "supported"},
    enums=dict(SPOUSE)))
_reg(B("joint_property_hma_pending", "hn_d",
    en=["My divorce case is pending, and we also have a house in both our names. I want my share of the [[joint_property_claim:joint property]] along with the divorce case.",
        "While our divorce case goes on, I want the court to decide about our jointly owned flat as well."],
    kn=["ನನ್ನ ವಿಚ್ಛೇದನ ಕೇಸ್ ನಡೆಯುತ್ತಿದೆ, ನಮ್ಮಿಬ್ಬರ ಹೆಸರಿನಲ್ಲಿ ಮನೆಯೂ ಇದೆ. ವಿಚ್ಛೇದನ ಕೇಸ್ ಜೊತೆಗೆ [[joint_property_claim:ಜಂಟಿ ಆಸ್ತಿ]]ಯಲ್ಲಿ ನನ್ನ ಪಾಲು ಬೇಕು.",
        "ನಮ್ಮ ವಿಚ್ಛೇದನ ಕೇಸ್ ನಡೆಯುವಾಗ, ನಮ್ಮ ಜಂಟಿ ಫ್ಲ್ಯಾಟ್ ಬಗ್ಗೆಯೂ ಕೋರ್ಟ್ ತೀರ್ಮಾನಿಸಬೇಕು."],
    ro=["Nanna divorce case nadeyuttide, nammibbara hesarinalli maneyu ide. Divorce case jotege [[joint_property_claim:janti asti]]yalli nanna palu beku.",
        "Namma divorce case nadeyuvaga, namma janti flat baggeyu court teermanisabeku."],
    issues={"joint_property": "requested", "divorce": "incidental"},
    facts={"joint_property_claim": "supported",
           "proceeding_pending_hma": "supported",
           "divorce_asked": "unknown", "in_scope": "supported"},
    enums=dict(SPOUSE)))
_reg(B("joint_property_no_hma", "hn_d",
    en=["There is no divorce case between us. I only want my share of the house we bought together in both names.",
        "We are still married and there is no case in court, but I want to know about my share in our joint house."],
    kn=["ನಮ್ಮ ನಡುವೆ ಯಾವುದೇ ವಿಚ್ಛೇದನ ಕೇಸ್ ಇಲ್ಲ. ನಾವು ಇಬ್ಬರ ಹೆಸರಿನಲ್ಲಿ ಖರೀದಿಸಿದ ಮನೆಯಲ್ಲಿ ನನ್ನ ಪಾಲು ಮಾತ್ರ ಬೇಕು.",
        "ನಾವು ಇನ್ನೂ ಮದುವೆಯಲ್ಲಿದ್ದೇವೆ, ಕೋರ್ಟ್‌ನಲ್ಲಿ ಯಾವುದೇ ಕೇಸ್ ಇಲ್ಲ, ಆದರೆ ನಮ್ಮ ಜಂಟಿ ಮನೆಯಲ್ಲಿ ನನ್ನ ಪಾಲಿನ ಬಗ್ಗೆ ತಿಳಿಯಬೇಕು."],
    ro=["Namma naduve yavude divorce case illa. Navu ibbara hesarinalli khareedisa maneyalli nanna palu matra beku.",
        "Navu innu maduveyalliddeve, court nalli yavude case illa, adare namma janti maneyalli nanna palina bagge tiliyabeku."],
    issues={"joint_property": "requested"},
    facts={"joint_property_claim": "supported",
           "proceeding_pending_hma": "denied", "being_filed": "denied",
           "in_scope": "supported"},
    enums=dict(SPOUSE)))
_reg(B("birth_cert", "core",
    en=["I need a [[birth_certificate:birth certificate]] for my {child_age}-year-old {child_word} for school admission. How do I get one?",
        "My {child_word} was born at home and has no [[birth_certificate:birth certificate]]. Where do I apply for it?"],
    kn=["ಶಾಲಾ ಪ್ರವೇಶಕ್ಕಾಗಿ ನನ್ನ {child_age} ವರ್ಷದ {child_word}ನ [[birth_certificate:ಜನನ ಪ್ರಮಾಣಪತ್ರ]] ಬೇಕು. ಅದನ್ನು ಹೇಗೆ ಪಡೆಯುವುದು?",
        "ನನ್ನ {child_word} ಮನೆಯಲ್ಲಿ ಹುಟ್ಟಿದನು, [[birth_certificate:ಜನನ ಪ್ರಮಾಣಪತ್ರ]] ಇಲ್ಲ. ಎಲ್ಲಿ ಅರ್ಜಿ ಹಾಕಬೇಕು?"],
    ro=["Shala praveshakagi nanna {child_age} varshada {child_word}na [[birth_certificate:janana pramanapatra]] beku. Adannu hege padeyuvudu?",
        "Nanna {child_word} maneyalli huttidanu, [[birth_certificate:janana pramanapatra]] illa. Elli arji hakabeku?"],
    issues={"birth_certificate": "requested"},
    facts={"birth_cert_asked": "supported", "child_fact": "supported",
           "minor_child": "supported", "in_scope": "supported"},
    enums=dict(SPOUSE)))

# --- core: procedure ------------------------------------------------------
_reg(B("procedure_court", "core",
    en=["Which court should I go to for [[procedure:maintenance]] and my child's custody?",
        "I do not know which court handles family cases. Where should I file my case?"],
    kn=["[[procedure:ಜೀವನಾಂಶ]] ಮತ್ತು ನನ್ನ ಮಗುವಿನ ಪಾಲನೆಗಾಗಿ ನಾನು ಯಾವ ಕೋರ್ಟ್‌ಗೆ ಹೋಗಬೇಕು?",
        "ಕೌಟುಂಬಿಕ ಪ್ರಕರಣಗಳನ್ನು ಯಾವ ಕೋರ್ಟ್ ನೋಡುತ್ತದೆ ಎಂದು ನನಗೆ ಗೊತ್ತಿಲ್ಲ. ನಾನು ಎಲ್ಲಿ ಕೇಸ್ ಹಾಕಬೇಕು?"],
    ro=["[[procedure:Jeevanamsha]] mattu nanna maguvina paalanegagi nanu yava court ge hogabeku?",
        "Koutumbika prakaranagalannu yava court noduttade anta nanage gottilla. Nanu elli case hakabeku?"],
    issues={"procedure": "requested"},
    facts={"in_scope": "supported"},
    enums=dict(SPOUSE)))
_reg(B("procedure_how_file", "core",
    en=["How do I file a case for [[procedure:maintenance]]? What papers do I need to start?",
        "What is the first step to ask the court for help with my husband not paying me?"],
    kn=["[[procedure:ಜೀವನಾಂಶ]]ಕ್ಕಾಗಿ ಕೇಸ್ ಹೇಗೆ ಹಾಕುವುದು? ಪ್ರಾರಂಭಿಸಲು ಯಾವ ಕಾಗದಗಳು ಬೇಕು?",
        "ನನ್ನ ಗಂಡ ಹಣ ಕೊಡದಿದ್ದಾಗ ಕೋರ್ಟ್ ಸಹಾಯ ಕೇಳಲು ಮೊದಲ ಹೆಜ್ಜೆ ಏನು?"],
    ro=["[[procedure:Jeevanamsha]]kkagi case hege hakuvudu? Prarambhisalu yava kagadagalu beku?",
        "Nanna ganda hana kodadiddaga court sahaya kelalu modala hejje enu?"],
    issues={"procedure": "requested"},
    facts={"in_scope": "supported"},
    enums=dict(SPOUSE)))

# --- recall-swarm expansion (Lane 02, 8,000; thin clusters + hn_g/hn_h) ---
# Added 2026-11-27 for the unseen-question recall target (>= 70% exact).
# Every sentence below was written fresh from the statutory concepts
# (BNSS s.144 / s.144(3) / s.146, HMA ss.9/13/13B/24/25/26/27, PWDVA
# ss.17/18/19/20/22, GWA 1890, HMGA s.6, BNS s.316, Births & Deaths Act
# 1969). NEVER from test banks, never from Kaanoon Q&A text: Kaanoon
# (kaanoon.com, read 2026-11-27: 2 searches + 1 public page fetch)
# informed only the PHRASING PATTERNS used here — dated narrative openers,
# numbered multi-question asks ("My questions are: first... second..."),
# arrears/execution framing ("he paid for three months, then stopped"),
# "can I fight my own case / how do I file this myself" procedure asks,
# post-decree stridhan recovery, and husband-side questions. No Kaanoon
# question or answer text was copied. Lane 11's study-sample patterns file
# (docs/kaanoon_phrasing_patterns.md) had NOT landed when these blocks
# were written; see the lane status file for the reconciliation note.
# Thin clusters targeted: conflict 50, birth_certificate 135,
# procedure 135, dv_compensation 134, restitution 118 (manifest counts),
# plus child_safety_risk 50, being_filed 66, judicial_separation_only 73.
# New clusters: hn_g = incidental-mention traps (issue mentioned as
# background, must NOT become requested); hn_h = modality traps
# (hypothetical / quoted / past-tense, incl. past violence that stopped).
_reg(B("birth_cert_late", "core",
    en=["My {child_age}-year-old {child_word} was born at home and never got a [[birth_certificate:birth certificate]]. I need one now for school admission.",
        "My {child_word} has no [[birth_certificate:birth certificate]] because the birth was never registered. How do I register it now, after so many years?"],
    kn=["ನನ್ನ {child_age} ವರ್ಷದ {child_word} ಮನೆಯಲ್ಲಿ ಹುಟ್ಟಿದನು, [[birth_certificate:ಜನನ ಪ್ರಮಾಣಪತ್ರ]] ಸಿಕ್ಕಿಲ್ಲ. ಶಾಲಾ ಪ್ರವೇಶಕ್ಕೆ ಈಗ ಅದು ಬೇಕು.",
        "ನನ್ನ {child_word}ನ ಜನನವನ್ನು ನೋಂದಾಯಿಸಿಲ್ಲ, ಅದಕ್ಕಾಗಿ [[birth_certificate:ಜನನ ಪ್ರಮಾಣಪತ್ರ]] ಇಲ್ಲ. ಇಷ್ಟು ವರ್ಷಗಳ ನಂತರ ಅದನ್ನು ಹೇಗೆ ನೋಂದಾಯಿಸುವುದು?"],
    ro=["Nanna {child_age} varshada {child_word} maneyalli huttidanu, [[birth_certificate:janana pramanapatra]] sikkilla. Shala praveshakke ega adu beku.",
        "Nanna {child_word}na janana vannu nondaisilla, adakkagi [[birth_certificate:janana pramanapatra]] illa. Ishtu varshagala nantara adannu hege nondaisuvudu?"],
    issues={"birth_certificate": "requested"},
    facts={"birth_cert_asked": "supported", "child_fact": "supported",
           "minor_child": "supported", "in_scope": "supported"},
    enums=dict(SPOUSE)))
_reg(B("birth_cert_correction", "core",
    en=["The name on my {child_word}'s [[birth_certificate:birth certificate]] is spelled wrong. I want to correct the spelling on the certificate.",
        "My {child_word}'s [[birth_certificate:birth certificate]] shows the wrong date of birth. How do I get the date corrected?"],
    kn=["ನನ್ನ {child_word}ನ [[birth_certificate:ಜನನ ಪ್ರಮಾಣಪತ್ರ]]ದಲ್ಲಿ ಹೆಸರು ತಪ್ಪಾಗಿ ಬರೆದಿದೆ. ಪ್ರಮಾಣಪತ್ರದಲ್ಲಿ ಹೆಸರನ್ನು ಸರಿಪಡಿಸಬೇಕು.",
        "ನನ್ನ {child_word}ನ [[birth_certificate:ಜನನ ಪ್ರಮಾಣಪತ್ರ]]ದಲ್ಲಿ ಹುಟ್ಟಿದ ದಿನಾಂಕ ತಪ್ಪಾಗಿದೆ. ದಿನಾಂಕವನ್ನು ಹೇಗೆ ಸರಿಪಡಿಸುವುದು?"],
    ro=["Nanna {child_word}na [[birth_certificate:janana pramanapatra]]dalli hesaru tappagi baredide. Pramanapatradalli hesarannu saripadisabeku.",
        "Nanna {child_word}na [[birth_certificate:janana pramanapatra]]dalli huttida dinanka tappagide. Dinankavannu hege saripadisuvudu?"],
    issues={"birth_certificate": "requested"},
    facts={"birth_cert_asked": "supported", "child_fact": "supported",
           "minor_child": "supported", "in_scope": "supported"},
    enums=dict(SPOUSE)))
_reg(B("birth_cert_lost", "core",
    en=["I have lost my {child_word}'s [[birth_certificate:birth certificate]]. I need a duplicate copy for school admission.",
        "My {child_word}'s [[birth_certificate:birth certificate]] was lost when we shifted house. Where do I apply for a new copy?"],
    kn=["ನನ್ನ {child_word}ನ [[birth_certificate:ಜನನ ಪ್ರಮಾಣಪತ್ರ]] ಕಳೆದುಹೋಗಿದೆ. ಶಾಲಾ ಪ್ರವೇಶಕ್ಕಾಗಿ ನಕಲು ಪ್ರತಿ ಬೇಕು.",
        "ನಾವು ಮನೆ ಬದಲಾಯಿಸಿದಾಗ ನನ್ನ {child_word}ನ [[birth_certificate:ಜನನ ಪ್ರಮಾಣಪತ್ರ]] ಕಳೆದುಹೋಯಿತು. ಹೊಸ ಪ್ರತಿಗಾಗಿ ಎಲ್ಲಿ ಅರ್ಜಿ ಹಾಕಬೇಕು?"],
    ro=["Nanna {child_word}na [[birth_certificate:janana pramanapatra]] kaledu hogide. Shala praveshakagi nakalu prati beku.",
        "Navu mane badalayisidaga nanna {child_word}na [[birth_certificate:janana pramanapatra]] kaledu hoyitu. Hosa pratigagi elli arji hakabeku?"],
    issues={"birth_certificate": "requested"},
    facts={"birth_cert_asked": "supported", "child_fact": "supported",
           "minor_child": "supported", "in_scope": "supported"},
    enums=dict(SPOUSE)))
_reg(B("procedure_documents", "core",
    en=["What papers do I need to file a case for [[procedure:maintenance]]? I want to know which documents to carry to court.",
        "I want to start a case for my child's custody. Which documents will the court ask for first?"],
    kn=["[[procedure:ಜೀವನಾಂಶ]]ಕ್ಕಾಗಿ ಕೇಸ್ ಹಾಕಲು ಯಾವ ಕಾಗದಗಳು ಬೇಕು? ಕೋರ್ಟ್‌ಗೆ ಯಾವ ದಾಖಲೆಗಳನ್ನು ತೆಗೆದುಕೊಂಡು ಹೋಗಬೇಕು ಎಂದು ತಿಳಿಯಬೇಕು.",
        "ನನ್ನ ಮಗುವಿನ ಪಾಲನೆಗಾಗಿ ಕೇಸ್ ಪ್ರಾರಂಭಿಸಲು ಬಯಸುತ್ತೇನೆ. ಕೋರ್ಟ್ ಮೊದಲು ಯಾವ ದಾಖಲೆಗಳನ್ನು ಕೇಳುತ್ತದೆ?"],
    ro=["[[procedure:Jeevanamsha]]kkagi case hakalu yava kagadagalu beku? Court ge yava dakhalegalannu tegedukondu hogabeku anta tiliyabeku.",
        "Nanna maguvina palanegagi case prarambhisalu bayasuttene. Court modalu yava dakhalegalannu keluttade?"],
    issues={"procedure": "requested"},
    facts={"in_scope": "supported"},
    enums=dict(SPOUSE)))
_reg(B("procedure_fees", "core",
    en=["How much does it cost to file a case in court? Do I have to pay any court fees for a maintenance case?",
        "I have no money to hire a lawyer. Can I get free legal help to file my family case?"],
    kn=["ಕೋರ್ಟ್‌ನಲ್ಲಿ ಕೇಸ್ ಹಾಕಲು ಎಷ್ಟು ಖರ್ಚಾಗುತ್ತದೆ? ಜೀವನಾಂಶ ಕೇಸ್‌ಗೆ ಕೋರ್ಟ್ ಶುಲ್ಕ ಕೊಡಬೇಕೇ?",
        "ವಕೀಲರನ್ನು ನೇಮಿಸಲು ನನ್ನ ಬಳಿ ಹಣವಿಲ್ಲ. ನನ್ನ ಕೌಟುಂಬಿಕ ಕೇಸ್‌ಗೆ ಉಚಿತ ಕಾನೂನು ಸಹಾಯ ಸಿಗಬಹುದೇ?"],
    ro=["Court nalli case hakalu eshtu kharchaguttade? Jeevanamsha case ge court shulka kodabeke?",
        "Vakilarannu nemisalu nanna bali hanavilla. Nanna koutumbika case ge uchita kanoonu sahaya sigabahude?"],
    issues={"procedure": "requested"},
    facts={"in_scope": "supported"},
    enums=dict(SPOUSE)))
_reg(B("procedure_timeline", "core",
    en=["How long will my maintenance case take in court? When will the first hearing happen?",
        "I filed my case two months ago and nothing has happened yet. How long do family cases usually take?",
        "Is there any time limit for filing my maintenance case? I want to know how much time I have."],
    kn=["ನನ್ನ ಜೀವನಾಂಶ ಕೇಸ್ ಕೋರ್ಟ್‌ನಲ್ಲಿ ಎಷ್ಟು ಸಮಯ ತೆಗೆದುಕೊಳ್ಳುತ್ತದೆ? ಮೊದಲ ವಿಚಾರಣೆ ಯಾವಾಗ ನಡೆಯುತ್ತದೆ?",
        "ನಾನು ಎರಡು ತಿಂಗಳ ಹಿಂದೆ ಕೇಸ್ ಹಾಕಿದೆ, ಇನ್ನೂ ಏನೂ ಆಗಿಲ್ಲ. ಕೌಟುಂಬಿಕ ಕೇಸ್‌ಗಳು ಸಾಮಾನ್ಯವಾಗಿ ಎಷ್ಟು ಸಮಯ ತೆಗೆದುಕೊಳ್ಳುತ್ತವೆ?",
        "ನನ್ನ ಜೀವನಾಂಶ ಕೇಸ್ ಹಾಕಲು ಯಾವುದಾದರೂ ಸಮಯ ಮಿತಿ ಇದೆಯೇ? ನನಗೆ ಎಷ್ಟು ಸಮಯವಿದೆ ಎಂದು ತಿಳಿಯಬೇಕು."],
    ro=["Nanna jeevanamsha case court nalli eshtu samaya tegedukolluttade? Modala vicharane yavaga nadeyuttade?",
        "Nanu eradu tingala hinde case hakide, innu enu agilla. Koutumbika case galu samanyavagi eshtu samaya tegedukolluttave?",
        "Nanna jeevanamsha case hakalu yavudadaru samaya miti ideye? Nanage eshtu samayavide anta tiliyabeku?"],
    issues={"procedure": "requested"},
    facts={"in_scope": "supported"},
    enums=dict(SPOUSE)))
_reg(B("child_risk_alcoholic", "core",
    en=["My husband drinks every day and shouts at our {child_age}-year-old {child_word}. I fear he will hurt my {child_word}, so I want [[custody:custody]] of my {child_word}.",
        "My husband comes home drunk and frightens our {child_word}. My {child_word} is not safe with him, and I want my {child_word} to remain under my care."],
    kn=["ನನ್ನ ಗಂಡ ಪ್ರತಿದಿನ ಕುಡಿದು ನಮ್ಮ {child_age} ವರ್ಷದ {child_word}ನನ್ನು ಗದರಿಸುತ್ತಾನೆ. ಅವನು ನನ್ನ {child_word}ನಿಗೆ ತೊಂದರೆ ಕೊಡುತ್ತಾನೆ ಎಂದು ಭಯವಿದೆ, ಅದಕ್ಕಾಗಿ ನನ್ನ {child_word}ನ [[custody:ಪಾಲನೆ]] ಬೇಕು.",
        "ನನ್ನ ಗಂಡ ಕುಡಿದು ಮನೆಗೆ ಬಂದು ನಮ್ಮ {child_word}ನನ್ನು ಹೆದರಿಸುತ್ತಾನೆ. ನನ್ನ {child_word} ಅವನ ಜೊತೆ ಸುರಕ್ಷಿತವಾಗಿಲ್ಲ, ನನ್ನ {child_word} ನನ್ನ ಆರೈಕೆಯಲ್ಲಿ ಇರಬೇಕು."],
    ro=["Nanna ganda pratidina kudidu namma {child_age} varshada {child_word}nannu gadarisuttane. Avanu nanna {child_word}nige tondare koduttane anta bhayavide, adakkagi nanna {child_word}na [[custody:paalane]] beku.",
        "Nanna ganda kudidu manege bandu namma {child_word}nannu hedisuttane. Nanna {child_word} avana jothe surakshitavagilla, nanna {child_word} nanna aaraikeyalli irabeku."],
    issues={"custody": "requested"},
    facts={"custody_claim": "supported", "child_safety_risk": "supported",
           "child_fact": "supported", "minor_child": "supported",
           "in_scope": "supported"},
    enums=dict(SPOUSE)))
_reg(B("child_risk_abduction", "core",
    en=["My husband says he will take our {child_age}-year-old {child_word} away to his village and never bring the {child_word} back. I want [[custody:custody]] so he cannot take my {child_word}.",
        "My husband has threatened to hide our {child_word} from me. I am afraid he will take my {child_word} away."],
    kn=["ನನ್ನ ಗಂಡ ನಮ್ಮ {child_age} ವರ್ಷದ {child_word}ನನ್ನು ತನ್ನ ಊರಿಗೆ ಕರೆದುಕೊಂಡು ಹೋಗಿ ಮರಳಿ ತರುವುದಿಲ್ಲ ಎಂದು ಹೇಳುತ್ತಾನೆ. ಅವನು ನನ್ನ {child_word}ನನ್ನು ತೆಗೆದುಕೊಂಡು ಹೋಗದಂತೆ ನನ್ನ {child_word}ನ [[custody:ಪಾಲನೆ]] ಬೇಕು.",
        "ನನ್ನ ಗಂಡ ನಮ್ಮ {child_word}ನನ್ನು ನನ್ನಿಂದ ಮರೆಮಾಡುವುದಾಗಿ ಬೆದರಿಸಿದ್ದಾನೆ. ಅವನು ನನ್ನ {child_word}ನನ್ನು ಕರೆದುಕೊಂಡು ಹೋಗುತ್ತಾನೆ ಎಂದು ಭಯವಿದೆ."],
    ro=["Nanna ganda namma {child_age} varshada {child_word}nannu tanna oorige karedukondu hogi marali taruvudilla anta heluttane. Avanu nanna {child_word}nannu tegedukondu hogadante nanna {child_word}na [[custody:paalane]] beku.",
        "Nanna ganda namma {child_word}nannu nanninda maremaduvudagi bedarisiddane. Avanu nanna {child_word}nannu karedukondu hoguttane anta bhayavide."],
    issues={"custody": "requested"},
    facts={"custody_claim": "supported", "child_safety_risk": "supported",
           "child_fact": "supported", "minor_child": "supported",
           "in_scope": "supported"},
    enums=dict(SPOUSE)))
_reg(B("child_risk_neglect", "core",
    en=["My husband leaves our {child_age}-year-old {child_word} alone at home all day and does not give the {child_word} food on time. I want [[custody:custody]] of my {child_word}.",
        "My {child_word} is left alone at home while my husband goes out. My {child_word} is not looked after properly, and I want my {child_word} with me."],
    kn=["ನನ್ನ ಗಂಡ ನಮ್ಮ {child_age} ವರ್ಷದ {child_word}ನನ್ನು ದಿನವಿಡೀ ಮನೆಯಲ್ಲಿ ಒಬ್ಬಂಟಿಯಾಗಿ ಬಿಟ್ಟು ಸಮಯಕ್ಕೆ ಊಟ ಕೊಡುವುದಿಲ್ಲ. ನನ್ನ {child_word}ನ [[custody:ಪಾಲನೆ]] ಬೇಕು.",
        "ನನ್ನ ಗಂಡ ಹೊರಗೆ ಹೋಗುವಾಗ ನನ್ನ {child_word} ಮನೆಯಲ್ಲಿ ಒಬ್ಬಂಟಿಯಾಗಿ ಇರುತ್ತಾನೆ. ನನ್ನ {child_word}ನನ್ನು ಸರಿಯಾಗಿ ನೋಡಿಕೊಳ್ಳುವುದಿಲ್ಲ, ನನ್ನ {child_word} ನನ್ನ ಜೊತೆ ಇರಬೇಕು."],
    ro=["Nanna ganda namma {child_age} varshada {child_word}nannu dinavidi maneyalli obbantiyagi bittu samayakke uta koduvudilla. Nanna {child_word}na [[custody:paalane]] beku.",
        "Nanna ganda horage hoguvaga nanna {child_word} maneyalli obbantiyagi iruttane. Nanna {child_word}nannu sariyagi nodikolluvudilla, nanna {child_word} nanna jothe irabeku."],
    issues={"custody": "requested"},
    facts={"custody_claim": "supported", "child_safety_risk": "supported",
           "child_fact": "supported", "minor_child": "supported",
           "in_scope": "supported"},
    enums=dict(SPOUSE)))
_reg(B("mutual_agreed_terms", "core",
    en=["My husband and I both agree to end the marriage, and we have agreed on maintenance and our {child_word}'s custody. We want a [[mutual_consent:mutual consent divorce]].",
        "We have settled everything between us — money, the house, and our {child_word}. Now we both want a divorce by [[mutual_consent:mutual consent]]."],
    kn=["ನನ್ನ ಗಂಡ ಮತ್ತು ನಾನು ಮದುವೆ ಕೊನೆಗೊಳಿಸಲು ಒಪ್ಪಿದ್ದೇವೆ, ಜೀವನಾಂಶ ಮತ್ತು ನಮ್ಮ {child_word}ನ ಪಾಲನೆಯ ಬಗ್ಗೆಯೂ ಒಪ್ಪಿದ್ದೇವೆ. ನಮಗೆ [[mutual_consent:ಪರಸ್ಪರ ಒಪ್ಪಿಗೆಯ ವಿಚ್ಛೇದನ]] ಬೇಕು.",
        "ನಾವು ಎಲ್ಲವನ್ನೂ ನಮ್ಮ ನಡುವೆ ಬಗೆಹರಿಸಿಕೊಂಡಿದ್ದೇವೆ — ಹಣ, ಮನೆ, ಮತ್ತು ನಮ್ಮ {child_word}. ಈಗ ನಾವಿಬ್ಬರೂ [[mutual_consent:ಪರಸ್ಪರ ಒಪ್ಪಿಗೆ]]ಯಿಂದ ವಿಚ್ಛೇದನ ಬಯಸುತ್ತೇವೆ."],
    ro=["Nanna ganda mattu nanu maduve konegolisalu oppideve, jeevanamsha mattu namma {child_word}na palaneya baggeyu oppideve. Namage [[mutual_consent:paraspara oppigeya vichchhedana]] beku.",
        "Navu ellavannu namma naduve bageharisikondiddeve — hana, mane, mattu namma {child_word}. Eega navibbaru [[mutual_consent:paraspara oppige]]yinda vichchhedana bayasutteve."],
    issues={"divorce": "requested"},
    facts={"divorce_asked": "supported", "mutual_consent": "supported",
           "in_scope": "supported"},
    enums=dict(SPOUSE)))
_reg(B("multi_ask_maint_stridhan", "core",
    en=["My questions are: first, can I get [[maintenance:maintenance]] from my husband who gives me nothing, and second, can I get my [[stridhan_claim:gold]] back from my in-laws?",
        "I have two questions. Can I ask for monthly support from my husband, and can I ask for my wedding jewellery to be returned?"],
    kn=["ನನ್ನ ಪ್ರಶ್ನೆಗಳು: ಮೊದಲು, ಏನೂ ಕೊಡದ ನನ್ನ ಗಂಡನಿಂದ [[maintenance:ಜೀವನಾಂಶ]] ಪಡೆಯಬಹುದೇ, ಎರಡನೆಯದಾಗಿ, ನನ್ನ [[stridhan_claim:ಚಿನ್ನ]]ವನ್ನು ಅತ್ತೆ-ಮಾವನಿಂದ ವಾಪಸ್ ಪಡೆಯಬಹುದೇ?",
        "ನನಗೆ ಎರಡು ಪ್ರಶ್ನೆಗಳಿವೆ. ನನ್ನ ಗಂಡನಿಂದ ತಿಂಗಳ ಬೆಂಬಲ ಕೇಳಬಹುದೇ, ಮತ್ತು ನನ್ನ ಮದುವೆಯ ಆಭರಣಗಳನ್ನು ವಾಪಸ್ ಕೇಳಬಹುದೇ?"],
    ro=["Nanna prashnegalu: modalu, enu kodada nanna gandana inda [[maintenance:jeevanamsha]] padeyabahude, eradaneyadagi, nanna [[stridhan_claim:chinna]]vannu atte-mavaninda vapas padeyabahude?",
        "Nanage eradu prashnegalive. Nanna gandana inda tingala bembala kelabahude, mattu nanna maduveya abharanagalannu vapas kelabahude?"],
    issues={"maintenance": "requested", "stridhan": "requested"},
    facts={"money_fact": "supported", "stridhan_claim": "supported",
           "in_scope": "supported"},
    enums=dict(SPOUSE)))
_reg(B("multi_ask_custody_maint", "core",
    en=["My questions are: first, can I get [[custody:custody]] of my {child_age}-year-old {child_word}, and second, can I get [[maintenance:maintenance]] for my {child_word}?",
        "I have two questions. Who will get my {child_word}, and will my husband have to pay for my {child_word}'s school fees?"],
    kn=["ನನ್ನ ಪ್ರಶ್ನೆಗಳು: ಮೊದಲು, ನನ್ನ {child_age} ವರ್ಷದ {child_word}ನ [[custody:ಪಾಲನೆ]] ಪಡೆಯಬಹುದೇ, ಎರಡನೆಯದಾಗಿ, ನನ್ನ {child_word}ಗಾಗಿ [[maintenance:ಜೀವನಾಂಶ]] ಪಡೆಯಬಹುದೇ?",
        "ನನಗೆ ಎರಡು ಪ್ರಶ್ನೆಗಳಿವೆ. ನನ್ನ {child_word} ಯಾರಿಗೆ ಸಿಗುತ್ತಾರೆ, ಮತ್ತು ನನ್ನ ಗಂಡ ನನ್ನ {child_word}ನ ಶಾಲಾ ಶುಲ್ಕ ಕೊಡಬೇಕೇ?"],
    ro=["Nanna prashnegalu: modalu, nanna {child_age} varshada {child_word}na [[custody:paalane]] padeyabahude, eradaneyadagi, nanna {child_word}gagi [[maintenance:jeevanamsha]] padeyabahude?",
        "Nanage eradu prashnegalive. Nanna {child_word} yarige siguttare, mattu nanna ganda nanna {child_word}na shala shulka kodabeke?"],
    issues={"custody": "requested", "maintenance": "requested"},
    facts={"custody_claim": "supported", "money_fact": "supported",
           "child_fact": "supported", "minor_child": "supported",
           "school_fees_fact": "supported", "in_scope": "supported"},
    enums=dict(SPOUSE)))
_reg(B("dv_comp_medical", "hn_b",
    en=["My husband beat me so badly that I had to stay in hospital for a week. I want [[dv_compensation:compensation]] for my hospital bills and treatment.",
        "I spent a lot of money on medicines after my husband beat me. I want the court to order him to pay for my treatment."],
    kn=["ನನ್ನ ಗಂಡ ನನ್ನನ್ನು ತುಂಬಾ ಹೊಡೆದನು, ನಾನು ಒಂದು ವಾರ ಆಸ್ಪತ್ರೆಯಲ್ಲಿ ಇರಬೇಕಾಯಿತು. ನನ್ನ ಆಸ್ಪತ್ರೆ ಬಿಲ್ ಮತ್ತು ಚಿಕಿತ್ಸೆಗಾಗಿ [[dv_compensation:ಪರಿಹಾರ]] ಬೇಕು.",
        "ನನ್ನ ಗಂಡ ಹೊಡೆದ ನಂತರ ಔಷಧಿಗಳಿಗೆ ಬಹಳ ಹಣ ಖರ್ಚು ಮಾಡಿದೆ. ಚಿಕಿತ್ಸೆಗಾಗಿ ಹಣ ಕೊಡುವಂತೆ ಕೋರ್ಟ್ ಅವನಿಗೆ ಆದೇಶಿಸಬೇಕು."],
    ro=["Nanna ganda nannannu tumba hodedanu, nanu ondu vara aspatreyalli irabekayitu. Nanna aspatre bill mattu chikitsegagi [[dv_compensation:parihara]] beku.",
        "Nanna ganda hodedanantara aushadhigalige bahala hana kharchu madide. Chikitsegagi hana koduvante court avanige adeshisabeku."],
    issues={"violence": "requested", "dv_compensation": "requested"},
    facts={"violence": "supported", "dv_injury_comp_asked": "supported",
           "in_scope": "supported"},
    enums=dict(SPOUSE)))
_reg(B("dv_comp_mental", "hn_b",
    en=["My husband and in-laws torture me with bad words every day. I want [[dv_compensation:compensation]] for this mental harassment.",
        "I have suffered mental torture at home for years. Can I ask for money as compensation for the suffering?"],
    kn=["ನನ್ನ ಗಂಡ ಮತ್ತು ಅತ್ತೆ-ಮಾವ ಪ್ರತಿದಿನ ಕೆಟ್ಟ ಮಾತುಗಳಿಂದ ನನ್ನನ್ನು ಹಿಂಸಿಸುತ್ತಾರೆ. ಈ ಮಾನಸಿಕ ಕಿರುಕುಳಕ್ಕಾಗಿ [[dv_compensation:ಪರಿಹಾರ]] ಬೇಕು.",
        "ಮನೆಯಲ್ಲಿ ವರ್ಷಗಳಿಂದ ಮಾನಸಿಕ ಹಿಂಸೆ ಅನುಭವಿಸಿದ್ದೇನೆ. ಆ ನೋವಿಗೆ ಪರಿಹಾರವಾಗಿ ಹಣ ಕೇಳಬಹುದೇ?"],
    ro=["Nanna ganda mattu atte-mava pratidina ketta matugalinda nannannu himsisuttare. Ee manasika kirukula kagi [[dv_compensation:parihara]] beku.",
        "Maneyalli varshagalinda manasika himse anubhavisiddene. Aa novige pariharavagi hana kelabahude?"],
    issues={"violence": "requested", "dv_compensation": "requested"},
    facts={"violence": "supported", "dv_injury_comp_asked": "supported",
           "in_scope": "supported"},
    enums=dict(SPOUSE)))
_reg(B("dv_comp_lost_wages", "hn_b",
    en=["After my husband beat me, I could not go to work for a month and lost my wages. I want [[dv_compensation:compensation]] for the wages I lost.",
        "My injuries stopped me from working, so I lost a month's pay. Can I ask my husband to pay for that loss?"],
    kn=["ನನ್ನ ಗಂಡ ಹೊಡೆದ ನಂತರ ನಾನು ಒಂದು ತಿಂಗಳು ಕೆಲಸಕ್ಕೆ ಹೋಗಲಾಗಲಿಲ್ಲ, ನನ್ನ ವೇತನ ಕಳೆದುಕೊಂಡೆ. ನಾನು ಕಳೆದುಕೊಂಡ ವೇತನಕ್ಕಾಗಿ [[dv_compensation:ಪರಿಹಾರ]] ಬೇಕು.",
        "ನನ್ನ ಗಾಯಗಳಿಂದ ಕೆಲಸ ಮಾಡಲಾಗಲಿಲ್ಲ, ಒಂದು ತಿಂಗಳ ಸಂಬಳ ಕಳೆದುಕೊಂಡೆ. ಆ ನಷ್ಟಕ್ಕೆ ನನ್ನ ಗಂಡ ಹಣ ಕೊಡಬೇಕೆಂದು ಕೇಳಬಹುದೇ?"],
    ro=["Nanna ganda hodedanantara nanu ondu tingalu kelasakke hogalagalilla, nanna vetana kaledukonde. Nanu kaledukonda vetanakkagi [[dv_compensation:parihara]] beku.",
        "Nanna gayagalinda kelasa madagalagilla, ondu tingala sambala kaledukonde. Aa nashtakke nanna ganda hana kodabekendu kelabahude?"],
    issues={"violence": "requested", "dv_compensation": "requested"},
    facts={"violence": "supported", "dv_injury_comp_asked": "supported",
           "in_scope": "supported"},
    enums=dict(SPOUSE)))
_reg(B("js_only_living_apart", "hn_c",
    en=["I want a court order to live separately from my husband, but I do not want to end the marriage. I only want [[judicial_separation_only:judicial separation]].",
        "We cannot live together anymore, but I am not ready for a divorce. I want to live apart with a court order."],
    kn=["ನನ್ನ ಗಂಡನಿಂದ ಬೇರೆಯಾಗಿ ವಾಸಿಸಲು ಕೋರ್ಟ್ ಆದೇಶ ಬೇಕು, ಆದರೆ ಮದುವೆ ಕೊನೆಗೊಳಿಸಲು ಬಯಸುವುದಿಲ್ಲ. ನನಗೆ [[judicial_separation_only:ನ್ಯಾಯಾಂಗ ಬೇರ್ಪಡಿಕೆ]] ಮಾತ್ರ ಬೇಕು.",
        "ನಾವು ಒಟ್ಟಿಗೆ ಬದುಕಲು ಸಾಧ್ಯವಿಲ್ಲ, ಆದರೆ ವಿಚ್ಛೇದನಕ್ಕೆ ನಾನು ಸಿದ್ಧವಿಲ್ಲ. ಕೋರ್ಟ್ ಆದೇಶದೊಂದಿಗೆ ಬೇರೆಯಾಗಿ ವಾಸಿಸಲು ಬಯಸುತ್ತೇನೆ."],
    ro=["Nanna gandana inda bereyagi vaasisalu court adesha beku, adare maduve konegolisalu bayasuvudilla. Nanage [[judicial_separation_only:nyayanga berpadike]] matra beku.",
        "Navu ottige badukalu sadhyavilla, adare divorce ge nanu siddhavilla. Court adeshadondige bereyagi vaasisalu bayasuttene."],
    issues={"divorce": "denied"},
    facts={"judicial_separation_only": "supported",
           "divorce_asked": "denied", "in_scope": "supported"},
    enums=dict(SPOUSE)))
_reg(B("being_filed_custody", "hn_c",
    en=["I am going to file a case for [[custody:custody]] of my {child_age}-year-old {child_word} next week. My husband has taken my {child_word} away from me.",
        "Next month I will file a custody petition for my {child_word}. What is the first thing I should arrange?"],
    kn=["ನಾನು ಮುಂದಿನ ವಾರ ನನ್ನ {child_age} ವರ್ಷದ {child_word}ನ [[custody:ಪಾಲನೆ]]ಗಾಗಿ ಕೇಸ್ ಹಾಕುತ್ತಿದ್ದೇನೆ. ನನ್ನ ಗಂಡ ನನ್ನ {child_word}ನನ್ನು ನನ್ನಿಂದ ಕರೆದುಕೊಂಡು ಹೋಗಿದ್ದಾನೆ.",
        "ಮುಂದಿನ ತಿಂಗಳು ನನ್ನ {child_word}ಗಾಗಿ ಪಾಲನೆ ಅರ್ಜಿ ಹಾಕುತ್ತೇನೆ. ಮೊದಲು ಏನು ಸಿದ್ಧಪಡಿಸಬೇಕು?"],
    ro=["Nanu mundina vara nanna {child_age} varshada {child_word}na [[custody:paalane]]gagi case hakuttiddene. Nanna ganda nanna {child_word}nannu nanninda karedukondu hogiddane.",
        "Mundina tingalu nanna {child_word}gagi paalane arji hakuttene. Modalu enu siddhapadisabeku?"],
    issues={"custody": "requested"},
    facts={"being_filed": "supported", "custody_claim": "supported",
           "child_fact": "supported", "minor_child": "supported",
           "in_scope": "supported"},
    enums={"claimant_sex": F, "claimant_role": "spouse",
           "modality_time": "future"}))
_reg(B("being_filed_maintenance", "hn_c",
    en=["I am going to file a case for [[maintenance:maintenance]] next week. My husband has given me nothing for {duration}.",
        "I will file a maintenance petition next month. I have already spoken to a lawyer about it."],
    kn=["ನಾನು ಮುಂದಿನ ವಾರ [[maintenance:ಜೀವನಾಂಶ]]ಕ್ಕಾಗಿ ಕೇಸ್ ಹಾಕುತ್ತಿದ್ದೇನೆ. ನನ್ನ ಗಂಡ {duration} ಏನೂ ಕೊಟ್ಟಿಲ್ಲ.",
        "ಮುಂದಿನ ತಿಂಗಳು ಜೀವನಾಂಶ ಅರ್ಜಿ ಹಾಕುತ್ತೇನೆ. ಅದರ ಬಗ್ಗೆ ವಕೀಲರೊಂದಿಗೆ ಈಗಾಗಲೇ ಮಾತನಾಡಿದ್ದೇನೆ."],
    ro=["Nanu mundina vara [[maintenance:jeevanamsha]]kkagi case hakuttiddene. Nanna ganda {duration} enu kottilla.",
        "Mundina tingalu jeevanamsha arji hakuttene. Adara bagge vakilarondige egagale matanadiddene."],
    issues={"maintenance": "requested"},
    facts={"being_filed": "supported", "money_fact": "supported",
           "in_scope": "supported"},
    enums={"claimant_sex": F, "claimant_role": "spouse",
           "modality_time": "future"}))
_reg(B("mutual_refused", "hn_c",
    en=["I asked my husband for a divorce by mutual consent, but he refuses to agree. I still want a [[divorce:divorce]], even if he does not agree.",
        "My husband will not agree to a mutual divorce. Can I still get a divorce without his consent?"],
    kn=["ನನ್ನ ಗಂಡನನ್ನು ಪರಸ್ಪರ ಒಪ್ಪಿಗೆಯ ವಿಚ್ಛೇದನಕ್ಕೆ ಕೇಳಿದೆ, ಆದರೆ ಅವನು ಒಪ್ಪಲು ನಿರಾಕರಿಸುತ್ತಾನೆ. ಅವನು ಒಪ್ಪದಿದ್ದರೂ ನನಗೆ [[divorce:ವಿಚ್ಛೇದನ]] ಬೇಕು.",
        "ನನ್ನ ಗಂಡ ಪರಸ್ಪರ ವಿಚ್ಛೇದನಕ್ಕೆ ಒಪ್ಪುವುದಿಲ್ಲ. ಅವನ ಒಪ್ಪಿಗೆ ಇಲ್ಲದೆ ವಿಚ್ಛೇದನ ಪಡೆಯಬಹುದೇ?"],
    ro=["Nanna gandannu paraspara oppigeya divorce ge kelide, adare avanu oppalu nirakarisuttane. Avanu oppadiddaru nanage [[divorce:vichchhedana]] beku.",
        "Nanna ganda paraspara divorce ge oppuvudilla. Avana oppige illade divorce padeyabahude?"],
    issues={"divorce": "requested"},
    facts={"divorce_asked": "supported", "mutual_consent": "denied",
           "in_scope": "supported"},
    enums=dict(SPOUSE)))
_reg(B("restitution_wife_left", "hn_c",
    en=["My wife left our home and went to her parents' house. I want her to [[restitution:come back and live with me]] as my wife.",
        "My wife has been living separately for a year. I do not want a divorce, I want my wife to return home.",
        "My wife left home one day without telling anyone, and she has been away for a year. I want her to return home and live with me."],
    kn=["ನನ್ನ ಹೆಂಡತಿ ನಮ್ಮ ಮನೆ ಬಿಟ್ಟು ತನ್ನ ಪೋಷಕರ ಮನೆಗೆ ಹೋದಳು. ಅವಳು [[restitution:ಮರಳಿ ಬಂದು ನನ್ನ ಜೊತೆ ಹೆಂಡತಿಯಾಗಿ ಬದುಕಬೇಕು]] ಎಂದು ಬಯಸುತ್ತೇನೆ.",
        "ನನ್ನ ಹೆಂಡತಿ ಒಂದು ವರ್ಷದಿಂದ ಬೇರೆಯಾಗಿ ವಾಸಿಸುತ್ತಿದ್ದಾಳೆ. ನನಗೆ ವಿಚ್ಛೇದನ ಬೇಡ, ನನ್ನ ಹೆಂಡತಿ ಮನೆಗೆ ಮರಳಬೇಕು.",
        "ನನ್ನ ಹೆಂಡತಿ ಒಂದು ದಿನ ಯಾರಿಗೂ ಹೇಳದೆ ಮನೆ ಬಿಟ್ಟು ಹೋದಳು, ಒಂದು ವರ್ಷದಿಂದ ದೂರವಿದ್ದಾಳೆ. ಅವಳು ಮನೆಗೆ ಮರಳಿ ನನ್ನ ಜೊತೆ ವಾಸಿಸಬೇಕು."],
    ro=["Nanna hendati namma mane bittu tanna poshakara manege hodalu. Avalu [[restitution:marali bandu nanna jothe hendatiyagi badukabeku]] anta bayasuttene.",
        "Nanna hendati ondu varshada inda bereyagi vaasisuttiddale. Nanage divorce beda, nanna hendati manege maralabeku.",
        "Nanna hendati ondu dina yarigu helade mane bittu hodalu, ondu varshada inda dooraviddale. Avalu manege marali nanna jothe vaasisabeku."],
    issues={"restitution": "requested", "divorce": "denied"},
    facts={"restitution_asked": "supported", "divorce_asked": "denied",
           "in_scope": "supported"},
    enums=dict(SPOUSE_M)))
_reg(B("restitution_desertion", "hn_c",
    en=["My husband left me two years ago and lives separately. I do not want a [[divorce:divorce]], I want him to return home and live with me.",
        "My husband deserted me and our {child_word}. I want the court to ask him to come back home."],
    kn=["ನನ್ನ ಗಂಡ ಎರಡು ವರ್ಷಗಳ ಹಿಂದೆ ನನ್ನನ್ನು ಬಿಟ್ಟು ಬೇರೆಯಾಗಿ ವಾಸಿಸುತ್ತಿದ್ದಾನೆ. ನನಗೆ [[divorce:ವಿಚ್ಛೇದನ]] ಬೇಡ, ಅವನು ಮನೆಗೆ ಮರಳಿ ನನ್ನ ಜೊತೆ ವಾಸಿಸಬೇಕು.",
        "ನನ್ನ ಗಂಡ ನನ್ನನ್ನು ಮತ್ತು ನಮ್ಮ {child_word}ನನ್ನು ಬಿಟ್ಟು ಹೋದನು. ಅವನು ಮನೆಗೆ ಮರಳಬೇಕು ಎಂದು ಕೋರ್ಟ್ ಕೇಳಬೇಕು."],
    ro=["Nanna ganda eradu varshagala hinde nannannu bittu bereyagi vaasisuttiddane. Nanage [[divorce:vichchhedana]] beda, avanu manege marali nanna jothe vaasisabeku.",
        "Nanna ganda nannannu mattu namma {child_word}nannu bittu hodanu. Avanu manege maralabeku anta court kelabeku."],
    issues={"restitution": "requested", "divorce": "denied"},
    facts={"restitution_asked": "supported", "divorce_asked": "denied",
           "in_scope": "supported"},
    enums=dict(SPOUSE)))
_reg(B("stridhan_after_decree", "hn_d",
    en=["I already took a divorce from my husband, but my [[stridhan_claim:gold]] is still in his house. How can I recover my stridhan even after the divorce?",
        "Our divorce is already decided, yet my wedding jewellery is still with my ex-husband's family. I want my [[stridhan_claim:stridhan]] back."],
    kn=["ನನ್ನ ಗಂಡನಿಂದ ನಾನು ಈಗಾಗಲೇ ವಿಚ್ಛೇದನ ಪಡೆದಿದ್ದೇನೆ, ಆದರೆ ನನ್ನ [[stridhan_claim:ಚಿನ್ನ]] ಇನ್ನೂ ಅವನ ಮನೆಯಲ್ಲಿದೆ. ವಿಚ್ಛೇದನದ ನಂತರವೂ ನನ್ನ ಚಿನ್ನವನ್ನು ಹೇಗೆ ವಾಪಸ್ ಪಡೆಯುವುದು?",
        "ನಮ್ಮ ವಿಚ್ಛೇದನ ಈಗಾಗಲೇ ತೀರ್ಮಾನವಾಗಿದೆ, ಆದರೂ ನನ್ನ ಮದುವೆಯ ಆಭರಣಗಳು ನನ್ನ ಮಾಜಿ ಗಂಡನ ಮನೆಯಲ್ಲೇ ಇವೆ. ನನ್ನ [[stridhan_claim:ಚಿನ್ನ]] ವಾಪಸ್ ಬೇಕು."],
    ro=["Nanna gandana inda nanu egagale divorce padediddene, adare nanna [[stridhan_claim:chinna]] innu avana maneyallide. Divorce danantaravu nanna chinnavannu hege vapas padeyuvudu?",
        "Namma divorce egagale teermanavagide, adaru nanna maduveya abharanagalu nanna maji gandana maneyalle ive. Nanna [[stridhan_claim:chinna]] vapas beku."],
    issues={"stridhan": "requested", "divorce": "incidental"},
    facts={"stridhan_claim": "supported", "decree": "supported",
           "divorce_asked": "unknown", "in_scope": "supported"},
    enums=dict(SPOUSE)))
_reg(B("conflict_custody", "conflict",
    en=["I want [[custody:custody]] of my {child_word}. Actually, no, let my husband keep our {child_word} with him. I cannot decide what is best.",
        "One moment I feel my {child_word} belongs with me, then I wonder whether my {child_word} should stay with the father. I am confused about custody."],
    kn=["ನನ್ನ {child_word}ನ [[custody:ಪಾಲನೆ]] ಬೇಕು. ಇಲ್ಲ, ನನ್ನ ಗಂಡನೇ ನಮ್ಮ {child_word}ನನ್ನು ತನ್ನ ಜೊತೆ ಇಟ್ಟುಕೊಳ್ಳಲಿ. ಯಾವುದು ಒಳ್ಳೆಯದು ಎಂದು ನಿರ್ಧರಿಸಲು ಸಾಧ್ಯವಿಲ್ಲ.",
        "ಒಂದು ಕ್ಷಣ ನನ್ನ {child_word} ನನ್ನ ಜೊತೆಯೇ ಇರಬೇಕು ಎಂದು ಅನಿಸುತ್ತದೆ, ಮರುಕ್ಷಣ ನನ್ನ {child_word} ತಂದೆಯ ಜೊತೆ ಇರುವುದು ಒಳ್ಳೆಯದೇ ಎಂದು ಗೊಂದಲವಾಗುತ್ತದೆ."],
    ro=["Nanna {child_word}na [[custody:paalane]] beku. Illa, nanna gandane namma {child_word}nannu tanna jothe ittukollali. Yavudu olleyadu anta nirdharisalu sadhyavilla.",
        "Ondu kshana nanna {child_word} nanna joteye irabeku anta anisuttade, marukshana nanna {child_word} tandeya jothe iruvudu olleyade anta gondalavaguttade."],
    issues={"custody": "uncertain"},
    facts={"custody_claim": "conflicting", "child_fact": "supported",
           "minor_child": "supported", "in_scope": "supported"},
    enums=dict(SPOUSE)))
_reg(B("conflict_maintenance", "conflict",
    en=["I want [[maintenance:maintenance]] from my husband. Actually, no, I do not need his money. I can manage on my own.",
        "One moment I want monthly support, the next moment I feel I should not take any money from him. I am confused about what to ask for."],
    kn=["ನನ್ನ ಗಂಡನಿಂದ [[maintenance:ಜೀವನಾಂಶ]] ಬೇಕು. ಇಲ್ಲ, ಅವನ ಹಣ ನನಗೆ ಬೇಡ. ನಾನೊಬ್ಬಳೇ ನಿಭಾಯಿಸಬಲ್ಲೆ.",
        "ಒಂದು ಕ್ಷಣ ತಿಂಗಳ ಬೆಂಬಲ ಬೇಕು ಎಂದು ಬಯಸುತ್ತೇನೆ, ಮರುಕ್ಷಣ ಅವನಿಂದ ಹಣ ತೆಗೆದುಕೊಳ್ಳಬಾರದು ಎಂದು ಅನಿಸುತ್ತದೆ. ಏನು ಕೇಳಬೇಕೆಂದು ಗೊಂದಲವಿದೆ."],
    ro=["Nanna gandana inda [[maintenance:jeevanamsha]] beku. Illa, avana hana nanage beda. Nanobbale nibhayisaballe.",
        "Ondu kshana tingala bembala beku anta bayasuttene, marukshana avaninda hana tegedukollabaradu anta anisuttade. Enu kelabekendu gondalavide."],
    issues={"maintenance": "uncertain"},
    facts={"money_fact": "conflicting", "in_scope": "supported"},
    enums=dict(SPOUSE)))
_reg(B("conflict_residence", "conflict",
    en=["I want to keep living in our house. Actually, no, I want to leave this house and live elsewhere. I cannot decide where to live.",
        "One moment I want to stay in my home, the next moment I want to move out. I am confused about the house."],
    kn=["ನಮ್ಮ ಮನೆಯಲ್ಲೇ ವಾಸ ಮುಂದುವರಿಸಲು ಬಯಸುತ್ತೇನೆ. ಇಲ್ಲ, ಈ ಮನೆ ಬಿಟ್ಟು ಬೇರೆಡೆ ವಾಸಿಸಲು ಬಯಸುತ್ತೇನೆ. ಎಲ್ಲಿ ವಾಸಿಸಬೇಕೆಂದು ನಿರ್ಧರಿಸಲು ಸಾಧ್ಯವಿಲ್ಲ.",
        "ಒಂದು ಕ್ಷಣ ನನ್ನ ಮನೆಯಲ್ಲೇ ಇರಬೇಕು ಎಂದು ಬಯಸುತ್ತೇನೆ, ಮರುಕ್ಷಣ ಮನೆ ಬಿಟ್ಟು ಹೋಗಬೇಕು ಎಂದು ಅನಿಸುತ್ತದೆ. ಮನೆಯ ಬಗ್ಗೆ ಗೊಂದಲವಿದೆ."],
    ro=["Namma maneyalle vaasa munduvarisalu bayasuttene. Illa, ee mane bittu berede vaasisalu bayasuttene. Elli vaasisabekendu nirdharisalu sadhyavilla.",
        "Ondu kshana nanna maneyalle irabeku anta bayasuttene, marukshana mane bittu hogabeku anta anisuttade. Maneya bagge gondalavide."],
    issues={"residence": "uncertain"},
    facts={"residence_claim": "conflicting", "in_scope": "supported"},
    enums=dict(SPOUSE)))
_reg(B("conflict_stridhan", "conflict",
    en=["I want my [[stridhan_claim:gold]] back from my in-laws. Actually, no, let them keep it. I cannot decide whether to ask for it.",
        "One moment I want my wedding jewellery back, the next moment I feel I should leave it with them. I am confused about my gold."],
    kn=["ನನ್ನ [[stridhan_claim:ಚಿನ್ನ]]ವನ್ನು ಅತ್ತೆ-ಮಾವನಿಂದ ವಾಪಸ್ ಬೇಕು. ಇಲ್ಲ, ಅವರು ಅದನ್ನು ಇಟ್ಟುಕೊಳ್ಳಲಿ. ಅದನ್ನು ಕೇಳಬೇಕೇ ಎಂದು ನಿರ್ಧರಿಸಲು ಸಾಧ್ಯವಿಲ್ಲ.",
        "ಒಂದು ಕ್ಷಣ ನನ್ನ ಮದುವೆಯ ಆಭರಣಗಳು ವಾಪಸ್ ಬೇಕು ಎಂದು ಬಯಸುತ್ತೇನೆ, ಮರುಕ್ಷಣ ಅವುಗಳನ್ನು ಅವರ ಬಳಿಯೇ ಬಿಡಬೇಕು ಎಂದು ಅನಿಸುತ್ತದೆ. ನನ್ನ ಚಿನ್ನದ ಬಗ್ಗೆ ಗೊಂದಲವಿದೆ."],
    ro=["Nanna [[stridhan_claim:chinna]]vannu atte-mavaninda vapas beku. Illa, avaru adannu ittukollali. Adannu kelabeke anta nirdharisalu sadhyavilla.",
        "Ondu kshana nanna maduveya abharanagalu vapas beku anta bayasuttene, marukshana avugalannu avara baliye bidabeku anta anisuttade. Nanna chinnada bagge gondalavide."],
    issues={"stridhan": "uncertain"},
    facts={"stridhan_claim": "conflicting", "in_scope": "supported"},
    enums=dict(SPOUSE)))
_reg(B("neg_residence", "neg",
    en=["I do not want to live in that house anymore. I only want [[maintenance:maintenance]] from my husband.",
        "I have already left the house and I do not want to go back there. My question is only about monthly support."],
    kn=["ಆ ಮನೆಯಲ್ಲಿ ಇನ್ನು ವಾಸಿಸಲು ಬಯಸುವುದಿಲ್ಲ. ನನ್ನ ಗಂಡನಿಂದ [[maintenance:ಜೀವನಾಂಶ]] ಮಾತ್ರ ಬೇಕು.",
        "ನಾನು ಈಗಾಗಲೇ ಮನೆ ಬಿಟ್ಟಿದ್ದೇನೆ, ಅಲ್ಲಿಗೆ ಮರಳಲು ಬಯಸುವುದಿಲ್ಲ. ನನ್ನ ಪ್ರಶ್ನೆ ತಿಂಗಳ ಬೆಂಬಲದ ಬಗ್ಗೆ ಮಾತ್ರ."],
    ro=["Aa maneyalli innu vaasisalu bayasuvudilla. Nanna gandana inda [[maintenance:jeevanamsha]] matra beku.",
        "Nanu egagale mane bittiddene, allige maralalu bayasuvudilla. Nanna prashne tingala bembalada bagge matra."],
    issues={"residence": "denied", "maintenance": "requested"},
    facts={"residence_claim": "denied", "money_fact": "supported",
           "in_scope": "supported"},
    enums=dict(SPOUSE)))
_reg(B("neg_stridhan", "neg",
    en=["I do not want my [[stridhan_claim:gold]] back. Let my in-laws keep it. I only want a [[divorce:divorce]] from my husband.",
        "My jewellery can stay with them, I am not asking for it. I only want to end the marriage."],
    kn=["ನನ್ನ [[stridhan_claim:ಚಿನ್ನ]] ವಾಪಸ್ ಬೇಡ. ಅತ್ತೆ-ಮಾವ ಅದನ್ನು ಇಟ್ಟುಕೊಳ್ಳಲಿ. ನನ್ನ ಗಂಡನಿಂದ [[divorce:ವಿಚ್ಛೇದನ]] ಮಾತ್ರ ಬೇಕು.",
        "ನನ್ನ ಆಭರಣಗಳು ಅವರ ಬಳಿಯೇ ಇರಲಿ, ನಾನು ಅವುಗಳನ್ನು ಕೇಳುತ್ತಿಲ್ಲ. ಮದುವೆ ಕೊನೆಗೊಳಿಸಲು ಮಾತ್ರ ಬಯಸುತ್ತೇನೆ."],
    ro=["Nanna [[stridhan_claim:chinna]] vapas beda. Atte-mava adannu ittukollali. Nanna gandana inda [[divorce:vichchhedana]] matra beku.",
        "Nanna abharanagalu avara baliye irali, nanu avugalannu keluttilla. Maduve konegolisalu matra bayasuttene."],
    issues={"stridhan": "denied", "divorce": "requested"},
    facts={"stridhan_claim": "denied", "divorce_asked": "supported",
           "in_scope": "supported"},
    enums=dict(SPOUSE)))
_reg(B("neg_joint", "neg",
    en=["I do not want any share in the house we bought together. I only want [[custody:custody]] of my {child_word}.",
        "My husband can keep the flat, I want nothing from it. I only want my {child_word} to live with me."],
    kn=["ನಾವು ಒಟ್ಟಿಗೆ ಖರೀದಿಸಿದ ಮನೆಯಲ್ಲಿ ಯಾವುದೇ ಪಾಲು ಬೇಡ. ನನ್ನ {child_word}ನ [[custody:ಪಾಲನೆ]] ಮಾತ್ರ ಬೇಕು.",
        "ನನ್ನ ಗಂಡ ಫ್ಲ್ಯಾಟ್ ಇಟ್ಟುಕೊಳ್ಳಬಹುದು, ಅದರಿಂದ ನನಗೆ ಏನೂ ಬೇಡ. ನನ್ನ {child_word} ನನ್ನ ಜೊತೆ ಇರಬೇಕು ಅಷ್ಟೇ."],
    ro=["Navu ottige khareedisa maneyalli yavude palu beda. Nanna {child_word}na [[custody:paalane]] matra beku.",
        "Nanna ganda flat ittukollabahudu, adarinda nanage enu beda. Nanna {child_word} nanna jothe irabeku ashte."],
    issues={"joint_property": "denied", "custody": "requested"},
    facts={"joint_property_claim": "denied", "custody_claim": "supported",
           "child_fact": "supported", "minor_child": "supported",
           "in_scope": "supported"},
    enums=dict(SPOUSE)))
_reg(B("neg_dvcomp", "neg",
    en=["I do not want any money for my injuries. I only want protection from my husband's beatings.",
        "I am not asking for compensation. I only want the [[violence:violence]] at home to stop."],
    kn=["ನನ್ನ ಗಾಯಗಳಿಗೆ ಯಾವುದೇ ಹಣ ಬೇಡ. ನನ್ನ ಗಂಡನ ಹೊಡೆತದಿಂದ ರಕ್ಷಣೆ ಮಾತ್ರ ಬೇಕು.",
        "ನಾನು ಪರಿಹಾರ ಕೇಳುತ್ತಿಲ್ಲ. ಮನೆಯಲ್ಲಿ [[violence:ಹಿಂಸೆ]] ನಿಲ್ಲಬೇಕು ಅಷ್ಟೇ."],
    ro=["Nanna gayagalige yavude hana beda. Nanna gandana hodetinda rakshane matra beku.",
        "Nanu parihara keluttilla. Maneyalli [[violence:himse]] nillabeku ashte."],
    issues={"dv_compensation": "denied", "violence": "requested"},
    facts={"dv_injury_comp_asked": "denied", "violence": "supported",
           "in_scope": "supported"},
    enums=dict(SPOUSE)))
_reg(B("neg_restitution", "neg",
    en=["I do not want my husband back at all. I want a [[divorce:divorce]], not a reunion.",
        "He can stay away, I never want him to return. I only want to end the marriage legally."],
    kn=["ನನ್ನ ಗಂಡ ವಾಪಸ್ ಬರುವುದು ಖಂಡಿತ ಬೇಡ. ನನಗೆ [[divorce:ವಿಚ್ಛೇದನ]] ಬೇಕು, ಮರುಸೇರ್ಪಡೆ ಬೇಡ.",
        "ಅವನು ದೂರವೇ ಇರಬಹುದು, ಅವನು ಮರಳಿ ಬರುವುದು ನನಗೆ ಎಂದೂ ಬೇಡ. ಮದುವೆಯನ್ನು ಕಾನೂನುಬದ್ಧವಾಗಿ ಕೊನೆಗೊಳಿಸಲು ಮಾತ್ರ ಬಯಸುತ್ತೇನೆ."],
    ro=["Nanna ganda vapas baruvudu khandita beda. Nanage [[divorce:vichchhedana]] beku, maruserpade beda.",
        "Avanu doorave irabahudu, avanu marali baruvudu nanage endu beda. Maduveyannu kanunubaddhavagi konegolisalu matra bayasuttene."],
    issues={"restitution": "denied", "divorce": "requested"},
    facts={"restitution_asked": "denied", "divorce_asked": "supported",
           "in_scope": "supported"},
    enums=dict(SPOUSE)))

# --- hard negative G: incidental mentions (background, NOT requested) -------
_reg(B("bg_violence_past", "hn_g",
    en=["My husband hit me once two years ago, but that is in the past. My question now is only about [[maintenance:maintenance]] for my {child_word}.",
        "He beat me a long time ago, but I am not asking about that now. I only want money for my {child_word}'s school fees."],
    kn=["ನನ್ನ ಗಂಡ ಎರಡು ವರ್ಷಗಳ ಹಿಂದೆ ಒಮ್ಮೆ ನನ್ನನ್ನು ಹೊಡೆದನು, ಆದರೆ ಅದು ಹಿಂದಿನ ಮಾತು. ನನ್ನ ಪ್ರಶ್ನೆ ಈಗ ನನ್ನ {child_word}ಗಾಗಿ [[maintenance:ಜೀವನಾಂಶ]] ಬಗ್ಗೆ ಮಾತ್ರ.",
        "ಅವನು ಬಹಳ ಹಿಂದೆಯೇ ನನ್ನನ್ನು ಹೊಡೆದನು, ಆದರೆ ಅದರ ಬಗ್ಗೆ ಈಗ ಕೇಳುತ್ತಿಲ್ಲ. ನನ್ನ {child_word}ನ ಶಾಲಾ ಶುಲ್ಕಕ್ಕಾಗಿ ಮಾತ್ರ ಹಣ ಬೇಕು."],
    ro=["Nanna ganda eradu varshagala hinde omme nannannu hodedanu, adare adu hindina matu. Nanna prashne ega nanna {child_word}gagi [[maintenance:jeevanamsha]] bagge matra.",
        "Avanu bahala hindeye nannannu hodedanu, adare adara bagge ega keluttilla. Nanna {child_word}na shala shulka kagi matra hana beku."],
    issues={"violence": "incidental", "maintenance": "requested"},
    facts={"violence": "supported", "money_fact": "supported",
           "child_maintenance_only": "supported", "child_fact": "supported",
           "minor_child": "supported", "school_fees_fact": "supported",
           "in_scope": "supported"},
    enums={"claimant_sex": F, "claimant_role": "spouse",
           "modality_time": "past"}))
_reg(B("bg_stridhan_mention", "hn_g",
    en=["My gold is still with my in-laws, but I am not asking for it now. I only want [[custody:custody]] of my {child_word}.",
        "My wedding jewellery is kept by my husband's family. That is not my question today — I only want my {child_word} to live with me."],
    kn=["ನನ್ನ ಚಿನ್ನ ಇನ್ನೂ ನನ್ನ ಅತ್ತೆ-ಮಾವನ ಬಳಿಯೇ ಇದೆ, ಆದರೆ ಅದನ್ನು ಈಗ ಕೇಳುತ್ತಿಲ್ಲ. ನನ್ನ {child_word}ನ [[custody:ಪಾಲನೆ]] ಮಾತ್ರ ಬೇಕು.",
        "ನನ್ನ ಮದುವೆಯ ಆಭರಣಗಳನ್ನು ನನ್ನ ಗಂಡನ ಮನೆಯವರು ಇಟ್ಟುಕೊಂಡಿದ್ದಾರೆ. ಅದು ಇಂದಿನ ನನ್ನ ಪ್ರಶ್ನೆಯಲ್ಲ — ನನ್ನ {child_word} ನನ್ನ ಜೊತೆ ಇರಬೇಕು ಅಷ್ಟೇ."],
    ro=["Nanna chinna innu nanna atte-mavana baliye ide, adare adannu ega keluttilla. Nanna {child_word}na [[custody:paalane]] matra beku.",
        "Nanna maduveya abharanagalannu nanna gandana maneyavaru ittukondiddare. Adu indina nanna prashneyalla — nanna {child_word} nanna jothe irabeku ashte."],
    issues={"stridhan": "incidental", "custody": "requested"},
    facts={"stridhan_claim": "supported", "custody_claim": "supported",
           "child_fact": "supported", "minor_child": "supported",
           "in_scope": "supported"},
    enums=dict(SPOUSE)))
_reg(B("bg_residence_mention", "hn_g",
    en=["We live in our own house, and there is no problem about the house. My question is only about getting a [[divorce:divorce]].",
        "The house is not an issue between us. I only want to know how to end my marriage."],
    kn=["ನಾವು ನಮ್ಮ ಸ್ವಂತ ಮನೆಯಲ್ಲಿ ವಾಸಿಸುತ್ತೇವೆ, ಮನೆಯ ಬಗ್ಗೆ ಯಾವುದೇ ಸಮಸ್ಯೆ ಇಲ್ಲ. ನನ್ನ ಪ್ರಶ್ನೆ [[divorce:ವಿಚ್ಛೇದನ]] ಪಡೆಯುವ ಬಗ್ಗೆ ಮಾತ್ರ.",
        "ಮನೆ ನಮ್ಮ ನಡುವೆ ಸಮಸ್ಯೆಯಲ್ಲ. ನನ್ನ ಮದುವೆಯನ್ನು ಹೇಗೆ ಕೊನೆಗೊಳಿಸುವುದು ಎಂದು ಮಾತ್ರ ತಿಳಿಯಬೇಕು."],
    ro=["Navu namma swanta maneyalli vaasistevu, maneya bagge yavude samasye illa. Nanna prashne [[divorce:vichchhedana]] padeyuva bagge matra.",
        "Mane namma naduve samasyealla. Nanna maduveyannu hege konegolisuvudu anta matra tiliyabeku."],
    issues={"residence": "incidental", "divorce": "requested"},
    facts={"divorce_asked": "supported", "in_scope": "supported"},
    enums=dict(SPOUSE)))
_reg(B("bg_joint_property", "hn_g",
    en=["We also own a flat together, but my question today is only about [[maintenance:maintenance]] from my husband.",
        "There is a joint house in both our names, but I am not asking about it now. I only need monthly support."],
    kn=["ನಾವು ಜಂಟಿಯಾಗಿ ಫ್ಲ್ಯಾಟ್ ಸಹ ಹೊಂದಿದ್ದೇವೆ, ಆದರೆ ಇಂದಿನ ನನ್ನ ಪ್ರಶ್ನೆ ನನ್ನ ಗಂಡನಿಂದ [[maintenance:ಜೀವನಾಂಶ]] ಬಗ್ಗೆ ಮಾತ್ರ.",
        "ಇಬ್ಬರ ಹೆಸರಿನಲ್ಲಿ ಜಂಟಿ ಮನೆ ಇದೆ, ಆದರೆ ಅದರ ಬಗ್ಗೆ ಈಗ ಕೇಳುತ್ತಿಲ್ಲ. ನನಗೆ ತಿಂಗಳ ಬೆಂಬಲ ಮಾತ್ರ ಬೇಕು."],
    ro=["Navu jantiyagi flat saha hondiddeve, adare indina nanna prashne nanna gandana inda [[maintenance:jeevanamsha]] bagge matra.",
        "Ibbara hesarinalli janti mane ide, adare adara bagge ega keluttilla. Nanage tingala bembala matra beku."],
    issues={"joint_property": "incidental", "maintenance": "requested"},
    facts={"joint_property_claim": "supported", "money_fact": "supported",
           "in_scope": "supported"},
    enums=dict(SPOUSE)))
_reg(B("bg_birth_cert", "hn_g",
    en=["My {child_word} has no birth certificate yet, but that is not my question today. I only want to ask about [[maintenance:maintenance]] for my {child_word}.",
        "We have not made a birth certificate for my {child_word} so far. Today I only want help with school fees support."],
    kn=["ನನ್ನ {child_word}ಗೆ ಇನ್ನೂ ಜನನ ಪ್ರಮಾಣಪತ್ರವಿಲ್ಲ, ಆದರೆ ಅದು ಇಂದಿನ ನನ್ನ ಪ್ರಶ್ನೆಯಲ್ಲ. ನನ್ನ {child_word}ಗಾಗಿ [[maintenance:ಜೀವನಾಂಶ]] ಬಗ್ಗೆ ಮಾತ್ರ ಕೇಳಲು ಬಯಸುತ್ತೇನೆ.",
        "ನನ್ನ {child_word}ಗಾಗಿ ಇಲ್ಲಿಯವರೆಗೆ ಜನನ ಪ್ರಮಾಣಪತ್ರ ಮಾಡಿಸಿಲ್ಲ. ಇಂದು ಶಾಲಾ ಶುಲ್ಕ ಬೆಂಬಲದ ಬಗ್ಗೆ ಮಾತ್ರ ಸಹಾಯ ಬೇಕು."],
    ro=["Nanna {child_word}ge innu janana pramanapatravilla, adare adu indina nanna prashneyalla. Nanna {child_word}gagi [[maintenance:jeevanamsha]] bagge matra kelalu bayasuttene.",
        "Nanna {child_word}gagi illiyavarage janana pramanapatra madisilla. Indu shala shulka bembalada bagge matra sahaya beku."],
    issues={"birth_certificate": "incidental", "maintenance": "requested"},
    facts={"money_fact": "supported", "child_maintenance_only": "supported",
           "child_fact": "supported", "minor_child": "supported",
           "school_fees_fact": "supported", "in_scope": "supported"},
    enums=dict(SPOUSE)))

# --- hard negative H: modality traps (hypothetical / quoted / past) --------
_reg(B("hypo_custody", "hn_h",
    en=["Suppose a mother takes her child away and the father cannot see the child. Could the father ask the court for [[custody:custody]]?",
        "If a wife leaves with the child, what could the husband do to get his child back?"],
    kn=["ಒಂದು ವೇಳೆ ತಾಯಿ ಮಗುವನ್ನು ಕರೆದುಕೊಂಡು ಹೋಗಿ ತಂದೆಗೆ ಮಗುವನ್ನು ನೋಡಲು ಬಿಡದಿದ್ದರೆ, ತಂದೆ ಕೋರ್ಟ್‌ನಲ್ಲಿ [[custody:ಪಾಲನೆ]] ಕೇಳಬಹುದೇ?",
        "ಹೆಂಡತಿ ಮಗುವಿನೊಂದಿಗೆ ಹೋದರೆ, ತನ್ನ ಮಗುವನ್ನು ವಾಪಸ್ ಪಡೆಯಲು ಗಂಡ ಏನು ಮಾಡಬಹುದು?"],
    ro=["Ondu vele tayi maguvannu karedukondu hogi tandege maguvannu nodalu bidadiddare, tande court nalli [[custody:paalane]] kelabahude?",
        "Hendati maguvinondige hodare, tanna maguvannu vapas padeyalu ganda enu madabahudu?"],
    issues={},
    facts={"in_scope": "supported"},
    enums={"claimant_sex": "U", "claimant_role": "other",
           "modality_time": "hypothetical"}))
_reg(B("hypo_stridhan", "hn_h",
    en=["If a woman's in-laws refuse to return her gold, can she ask the court for her [[stridhan_claim:gold]] back?",
        "Suppose a husband sells his wife's jewellery without asking her. What could she do about it?"],
    kn=["ಒಂದು ವೇಳೆ ಮಹಿಳೆಯ ಅತ್ತೆ-ಮಾವ ಅವಳ ಚಿನ್ನವನ್ನು ಹಿಂದಿರುಗಿಸಲು ನಿರಾಕರಿಸಿದರೆ, ಅವಳು ಕೋರ್ಟ್‌ನಲ್ಲಿ ತನ್ನ [[stridhan_claim:ಚಿನ್ನ]] ವಾಪಸ್ ಕೇಳಬಹುದೇ?",
        "ಒಂದು ವೇಳೆ ಗಂಡ ಹೆಂಡತಿಯನ್ನು ಕೇಳದೆ ಅವಳ ಆಭರಣಗಳನ್ನು ಮಾರಿದರೆ, ಅವಳು ಅದರ ಬಗ್ಗೆ ಏನು ಮಾಡಬಹುದು?"],
    ro=["Ondu vele mahileyaga atte-mava avala chinnavannu hindirugisalu nirakarisidare, avalu court nalli tanna [[stridhan_claim:chinna]] vapas kelabahude?",
        "Ondu vele ganda hendatiyannu kelade avala abharanagalannu maridare, avalu adara bagge enu madabahudu?"],
    issues={},
    facts={"in_scope": "supported"},
    enums={"claimant_sex": "U", "claimant_role": "other",
           "modality_time": "hypothetical"}))
_reg(B("quoted_maintenance", "hn_h",
    en=["My neighbour told me, \"My husband gives me no money for the house.\" She wants to know if she can ask for [[maintenance:maintenance]].",
        "A woman at my workplace said, \"My husband stopped paying me anything.\" She asked me what the law says."],
    kn=["ನನ್ನ ನೆರೆಯವರು ನನಗೆ ಹೇಳಿದರು, \"ನನ್ನ ಗಂಡ ಮನೆಗೆ ಹಣ ಕೊಡುವುದಿಲ್ಲ.\" ಅವಳು [[maintenance:ಜೀವನಾಂಶ]] ಕೇಳಬಹುದೇ ಎಂದು ತಿಳಿಯಲು ಬಯಸುತ್ತಾಳೆ.",
        "ನನ್ನ ಕೆಲಸದ ಸ್ಥಳದಲ್ಲಿ ಒಬ್ಬ ಮಹಿಳೆ ಹೇಳಿದಳು, \"ನನ್ನ ಗಂಡ ನನಗೆ ಏನೂ ಕೊಡುವುದನ್ನು ನಿಲ್ಲಿಸಿದನು.\" ಕಾನೂನು ಏನು ಹೇಳುತ್ತದೆ ಎಂದು ಅವಳು ಕೇಳಿದಳು."],
    ro=["Nanna nereyavaru nanage helidaru, \"Nanna ganda manege hana koduvudilla.\" Avalu [[maintenance:jeevanamsha]] kelabahude anta tiliyalu bayasutale.",
        "Nanna kelasa sthaladalli obba mahile helidalu, \"Nanna ganda nanage enu koduvudannu nillisidanu.\" Kanoonu enu heluttade anta avalu kelidalu."],
    issues={},
    facts={"in_scope": "supported"},
    enums={"claimant_sex": "U", "claimant_role": "other",
           "modality_time": "quoted"}))
_reg(B("quoted_residence", "hn_h",
    en=["My cousin told me, \"My in-laws threw me out of the house.\" She wants to know if she can go back to her home.",
        "My friend said, \"My husband locked me out of the house.\" She asked me what she can do."],
    kn=["ನನ್ನ ಸೋದರ ಸಂಬಂಧಿ ನನಗೆ ಹೇಳಿದಳು, \"ನನ್ನ ಅತ್ತೆ-ಮಾವ ನನ್ನನ್ನು ಮನೆಯಿಂದ ಹೊರಹಾಕಿದರು.\" ಅವಳು ತನ್ನ ಮನೆಗೆ ಮರಳಬಹುದೇ ಎಂದು ತಿಳಿಯಲು ಬಯಸುತ್ತಾಳೆ.",
        "ನನ್ನ ಗೆಳತಿ ಹೇಳಿದಳು, \"ನನ್ನ ಗಂಡ ನನ್ನನ್ನು ಮನೆಯಿಂದ ಹೊರಗೆ ಬೀಗ ಹಾಕಿದನು.\" ಅವಳು ಏನು ಮಾಡಬಹುದು ಎಂದು ಕೇಳಿದಳು."],
    ro=["Nanna sodara sambandhi nanage helidalu, \"Nanna atte-mava nannannu maneyinda horahakidaru.\" Avalu tanna manege maralabahude anta tiliyalu bayasutale.",
        "Nanna gelati helidalu, \"Nanna ganda nannannu maneyinda horage beega hakidanu.\" Avalu enu madabahudu anta kelidalu."],
    issues={},
    facts={"in_scope": "supported"},
    enums={"claimant_sex": "U", "claimant_role": "other",
           "modality_time": "quoted"}))
_reg(B("past_violence_stopped", "hn_h",
    en=["My husband used to beat me, but he stopped two years ago. My question now is only about [[maintenance:maintenance]] from him.",
        "He hit me in the past, but there has been no violence for a long time. I only want monthly support now."],
    kn=["ನನ್ನ ಗಂಡ ಮೊದಲು ನನ್ನನ್ನು ಹೊಡೆಯುತ್ತಿದ್ದನು, ಆದರೆ ಎರಡು ವರ್ಷಗಳ ಹಿಂದೆ ನಿಲ್ಲಿಸಿದನು. ನನ್ನ ಪ್ರಶ್ನೆ ಈಗ ಅವನಿಂದ [[maintenance:ಜೀವನಾಂಶ]] ಬಗ್ಗೆ ಮಾತ್ರ.",
        "ಅವನು ಹಿಂದೆ ನನ್ನನ್ನು ಹೊಡೆದಿದ್ದನು, ಆದರೆ ಬಹಳ ಸಮಯದಿಂದ ಯಾವುದೇ ಹಿಂಸೆ ಇಲ್ಲ. ನನಗೆ ಈಗ ತಿಂಗಳ ಬೆಂಬಲ ಮಾತ್ರ ಬೇಕು."],
    ro=["Nanna ganda modalu nannannu hodeyuttiddanu, adare eradu varshagala hinde nillisidanu. Nanna prashne ega avaninda [[maintenance:jeevanamsha]] bagge matra.",
        "Avanu hinde nannannu hodediddanu, adare bahala samayada inda yavude himse illa. Nanage ega tingala bembala matra beku."],
    issues={"violence": "incidental", "maintenance": "requested"},
    facts={"violence": "supported", "money_fact": "supported",
           "in_scope": "supported"},
    enums={"claimant_sex": F, "claimant_role": "spouse",
           "modality_time": "past"}))
_reg(B("past_threats", "hn_h",
    en=["Two years ago my husband threatened to throw me out of the house, but nothing happened after that. I only want to know about getting a [[divorce:divorce]] now.",
        "My husband once said he would lock me out, but he never did it. My question today is only about divorce."],
    kn=["ಎರಡು ವರ್ಷಗಳ ಹಿಂದೆ ನನ್ನ ಗಂಡ ನನ್ನನ್ನು ಮನೆಯಿಂದ ಹೊರಹಾಕುವುದಾಗಿ ಬೆದರಿಸಿದನು, ಆದರೆ ಆ ನಂತರ ಏನೂ ಆಗಲಿಲ್ಲ. [[divorce:ವಿಚ್ಛೇದನ]] ಪಡೆಯುವ ಬಗ್ಗೆ ಮಾತ್ರ ಈಗ ತಿಳಿಯಬೇಕು.",
        "ನನ್ನ ಗಂಡ ಒಮ್ಮೆ ನನ್ನನ್ನು ಹೊರಗೆ ಬೀಗ ಹಾಕುವುದಾಗಿ ಹೇಳಿದನು, ಆದರೆ ಅದನ್ನು ಎಂದೂ ಮಾಡಲಿಲ್ಲ. ಇಂದಿನ ನನ್ನ ಪ್ರಶ್ನೆ ವಿಚ್ಛೇದನದ ಬಗ್ಗೆ ಮಾತ್ರ."],
    ro=["Eradu varshagala hinde nanna ganda nannannu maneyinda horahakuvudagi bedarisidanu, adare aa nantara enu agalilla. [[divorce:vichchhedana]] padeyuva bagge matra ega tiliyabeku.",
        "Nanna ganda omme nannannu horage beega hakuvudagi helidanu, adare adannu endu madalilla. Indina nanna prashne divorce da bagge matra."],
    issues={"residence": "incidental", "divorce": "requested"},
    facts={"divorce_asked": "supported", "in_scope": "supported"},
    enums={"claimant_sex": F, "claimant_role": "spouse",
           "modality_time": "past"}))

# --- recall-swarm expansion, Lane 11 reconciliation (2026-11-27) --------
# Patterns from docs/kaanoon_phrasing_patterns.md (Lane 11 study sample
# KAN-S01–S16 ONLY, contract R7 — never from the held-out eval set) that
# were NOT yet covered by the blocks above. Each pattern below is our own
# statutory-grammar wording informed by the pattern, never a copied
# excerpt (the patterns file itself carries only 2–3 short fragments per
# pattern). Patterns already covered and NOT re-added: numbered
# multi-question asks (multi_ask_*), third-party askers (third_party,
# quoted_*), fear of the other parent taking the child
# (child_risk_abduction), settlement lump sum (maint_lump_sum), "asked to
# leave" eviction story (now residence_asked_to_leave), soft-negation
# (now neg_soft_*). Deliberately NOT added: unedited lay misspellings
# (Lane 05 already covers spelling variants like "maintanance"; adding
# more misspelt templates would teach wrong spellings), the
# property-owner-side "let her out" eviction ask (no Laya section for an
# owner evicting a daughter-in-law), "I have stopped going to court"
# non-attendance (no schema fact), the mother's-gold-vs-father variant
# (not spousal stridhan — would mislabel stridhan_claim).
_reg(B("narr_maint_separated", "core",
    en=["I have been living separately from my husband for two years. He gives me nothing for the house or for our {child_word}. Kindly advise how I should proceed.",
        "My husband and I have lived apart for three years, and he sends no money at all. What am I supposed to do now?"],
    kn=["ನಾನು ಎರಡು ವರ್ಷಗಳಿಂದ ನನ್ನ ಗಂಡನಿಂದ ಬೇರೆಯಾಗಿ ವಾಸಿಸುತ್ತಿದ್ದೇನೆ. ಮನೆಗಾಗಿ ಅಥವಾ ನಮ್ಮ {child_word}ಗಾಗಿ ಅವನು ಏನೂ ಕೊಡುವುದಿಲ್ಲ. ಮುಂದೆ ಹೇಗೆ ಹೋಗಬೇಕು ಎಂದು ದಯವಿಟ್ಟು ಸಲಹೆ ನೀಡಿ.",
        "ನನ್ನ ಗಂಡ ಮತ್ತು ನಾನು ಮೂರು ವರ್ಷಗಳಿಂದ ಬೇರೆಯಾಗಿ ವಾಸಿಸುತ್ತಿದ್ದೇವೆ, ಅವನು ಯಾವುದೇ ಹಣ ಕಳುಹಿಸುವುದಿಲ್ಲ. ಈಗ ನಾನು ಏನು ಮಾಡಬೇಕು?"],
    ro=["Nanu eradu varshagalinda nanna gandana inda bereyagi vaasistiddene. Manegagi athava namma {child_word}gagi avanu enu koduvudilla. Munde hege hogabeku anta dayavittu salahe needi.",
        "Nanna ganda mattu nanu mooru varshagalinda bereyagi vaasistiddeve, avanu yavude hana kaluhisuvudilla. Eega nanu enu madabeku?"],
    issues={"maintenance": "requested"},
    facts={"money_fact": "supported", "in_scope": "supported"},
    enums=dict(SPOUSE)))
_reg(B("narr_custody_separate", "core",
    en=["I want to live separately from my husband with my {child_age}-year-old {child_word}. My husband drinks and shouts at home. What are the legal steps to protect myself and my {child_word}?",
        "I have been living apart from my husband with my {child_word} for a year. He keeps saying he will take my {child_word} away from me."],
    kn=["ನನ್ನ {child_age} ವರ್ಷದ {child_word}ನೊಂದಿಗೆ ನನ್ನ ಗಂಡನಿಂದ ಬೇರೆಯಾಗಿ ವಾಸಿಸಲು ಬಯಸುತ್ತೇನೆ. ನನ್ನ ಗಂಡ ಮನೆಯಲ್ಲಿ ಕುಡಿದು ಕೂಗಾಡುತ್ತಾನೆ. ನನ್ನನ್ನು ಮತ್ತು ನನ್ನ {child_word}ನನ್ನು ರಕ್ಷಿಸಲು ಕಾನೂನುಬದ್ಧ ಹೆಜ್ಜೆಗಳು ಯಾವುವು?",
        "ನಾನು ಒಂದು ವರ್ಷದಿಂದ ನನ್ನ {child_word}ನೊಂದಿಗೆ ನನ್ನ ಗಂಡನಿಂದ ಬೇರೆಯಾಗಿ ವಾಸಿಸುತ್ತಿದ್ದೇನೆ. ಅವನು ನನ್ನ {child_word}ನನ್ನು ನನ್ನಿಂದ ಕರೆದುಕೊಂಡು ಹೋಗುತ್ತೇನೆ ಎಂದು ಹೇಳುತ್ತಲೇ ಇದ್ದಾನೆ."],
    ro=["Nanna {child_age} varshada {child_word}nodige nanna gandana inda bereyagi vaasisalu bayasuttene. Nanna ganda maneyalli kudidu koogaduttane. Nannannu mattu nanna {child_word}nannu rakshisalu kanunubaddha hejjegalu yavuvu?",
        "Nanu ondu varshada inda nanna {child_word}nodige nanna gandana inda bereyagi vaasistiddene. Avanu nanna {child_word}nannu nanninda karedukondu hoguttene anta heluttalle iddane."],
    issues={"custody": "requested"},
    facts={"custody_claim": "supported", "child_fact": "supported",
           "minor_child": "supported", "in_scope": "supported"},
    enums=dict(SPOUSE)))
_reg(B("stridhan_display", "hn_d",
    en=["All my jewellery was displayed at the wedding, and we have photos and video of it. My in-laws are keeping it all. How do I get my [[stridhan_claim:gold]] back?",
        "My wedding jewellery was shown to everyone at the wedding. My husband's family still refuses to return it, even though we have the video as proof."],
    kn=["ನನ್ನ ಎಲ್ಲಾ ಆಭರಣಗಳನ್ನು ಮದುವೆಯಲ್ಲಿ ತೋರಿಸಲಾಗಿತ್ತು, ಅವುಗಳ ಫೋಟೋ ಮತ್ತು ವಿಡಿಯೋ ನಮ್ಮ ಬಳಿ ಇದೆ. ನನ್ನ ಅತ್ತೆ-ಮಾವ ಎಲ್ಲವನ್ನೂ ಇಟ್ಟುಕೊಂಡಿದ್ದಾರೆ. ನನ್ನ [[stridhan_claim:ಚಿನ್ನ]] ವಾಪಸ್ ಹೇಗೆ ಪಡೆಯುವುದು?",
        "ನನ್ನ ಮದುವೆಯ ಆಭರಣಗಳನ್ನು ಮದುವೆಯಲ್ಲಿ ಎಲ್ಲರಿಗೂ ತೋರಿಸಲಾಗಿತ್ತು. ವಿಡಿಯೋ ಸಾಕ್ಷಿಯಾಗಿದ್ದರೂ ನನ್ನ ಗಂಡನ ಮನೆಯವರು ಅದನ್ನು ಹಿಂದಿರುಗಿಸಲು ನಿರಾಕರಿಸುತ್ತಿದ್ದಾರೆ."],
    ro=["Nanna ella abharanagalannu maduveyalli torisalagittu, avugala photo mattu video namma bali ide. Nanna atte-mava ellavannu ittukondiddare. Nanna [[stridhan_claim:chinna]] vapas hege padeyuvudu?",
        "Nanna maduveya abharanagalannu maduveyalli ellarigu torisalagittu. Video sakshiyagiddaru nanna gandana maneyavaru adannu hindirugisalu nirakarisuttiddare."],
    issues={"stridhan": "requested"},
    facts={"stridhan_claim": "supported", "in_scope": "supported"},
    enums=dict(SPOUSE)))
_reg(B("maint_partial_fees", "core",
    en=["My husband pays only my {child_word}'s school fees, nothing for the bus, dress, books or food. I need [[maintenance:maintenance]] for all the other expenses of my {child_word}.",
        "He pays the school fees and nothing else. The bus, the dress, the books and the food are all on me. I need support for the rest of my {child_word}'s expenses."],
    kn=["ನನ್ನ ಗಂಡ ನನ್ನ {child_word}ನ ಶಾಲಾ ಶುಲ್ಕವನ್ನು ಮಾತ್ರ ಕೊಡುತ್ತಾನೆ, ಬಸ್, ಡ್ರೆಸ್, ಪುಸ್ತಕ ಅಥವಾ ಊಟಕ್ಕೆ ಏನೂ ಕೊಡುವುದಿಲ್ಲ. ನನ್ನ {child_word}ನ ಉಳಿದ ಎಲ್ಲಾ ಖರ್ಚುಗಳಿಗಾಗಿ [[maintenance:ಜೀವನಾಂಶ]] ಬೇಕು.",
        "ಅವನು ಶಾಲಾ ಶುಲ್ಕವನ್ನು ಮಾತ್ರ ಕೊಡುತ್ತಾನೆ, ಬೇರೆ ಏನೂ ಇಲ್ಲ. ಬಸ್, ಡ್ರೆಸ್, ಪುಸ್ತಕ ಮತ್ತು ಊಟ ಎಲ್ಲವೂ ನನ್ನ ಮೇಲೆಯೇ ಇದೆ. ನನ್ನ {child_word}ನ ಉಳಿದ ಖರ್ಚುಗಳಿಗೆ ಬೆಂಬಲ ಬೇಕು."],
    ro=["Nanna ganda nanna {child_word}na shala shulkavannu matra koduttane, bus, dress, pustaka athava utakke enu koduvudilla. Nanna {child_word}na ulida ella kharchugaligagi [[maintenance:jeevanamsha]] beku.",
        "Avanu shala shulkavannu matra koduttane, bere enu illa. Bus, dress, pustaka mattu uta ellavu nanna meleye ide. Nanna {child_word}na ulida kharchugalige bembala beku."],
    issues={"maintenance": "requested"},
    facts={"money_fact": "supported", "child_maintenance_only": "supported",
           "child_fact": "supported", "minor_child": "supported",
           "school_fees_fact": "supported", "in_scope": "supported"},
    enums=dict(SPOUSE)))
_reg(B("maint_enforcement_fear", "hn_e",
    en=["The court ordered me to pay [[maintenance:maintenance]], and I have not paid for six months. Can the court jail me for not paying?",
        "I missed maintenance payments for a year. Can the court take my property to pay the amount I owe?"],
    kn=["ಕೋರ್ಟ್ ನಾನು [[maintenance:ಜೀವನಾಂಶ]] ಕೊಡಬೇಕು ಎಂದು ಆದೇಶಿಸಿತು, ಆರು ತಿಂಗಳಿಂದ ನಾನು ಕೊಟ್ಟಿಲ್ಲ. ಕೊಡದಿದ್ದಕ್ಕಾಗಿ ಕೋರ್ಟ್ ನನ್ನನ್ನು ಜೈಲಿಗೆ ಹಾಕಬಹುದೇ?",
        "ಒಂದು ವರ್ಷ ಜೀವನಾಂಶ ಪಾವತಿಗಳನ್ನು ತಪ್ಪಿಸಿದೆ. ನಾನು ಕೊಡಬೇಕಾದ ಹಣಕ್ಕಾಗಿ ಕೋರ್ಟ್ ನನ್ನ ಆಸ್ತಿಯನ್ನು ತೆಗೆದುಕೊಳ್ಳಬಹುದೇ?"],
    ro=["Court nanu [[maintenance:jeevanamsha]] kodabeku anta adeshisitu, aaru tingalinda nanu kottilla. Kodadiddakkagi court nannannu jailige hakabahude?",
        "Ondu varsha jeevanamsha pavaticgalannu tappiside. Nanu kodabekada hanakkagi court nanna astiyannu tegedukollabahude?"],
    issues={"maintenance": "incidental"},
    facts={"money_fact": "supported",
           "existing_order_enforcement": "supported",
           "in_scope": "supported"},
    enums=dict(SPOUSE_M)))
_reg(B("divorce_settlement_terms", "core",
    en=["I want to end all the cases between us. I am ready to pay a final settlement amount. Please suggest the terms I can put before the mediator.",
        "I agreed to pay a final settlement so that all our litigations end. What terms should the settlement agreement have?"],
    kn=["ನಮ್ಮ ನಡುವಿನ ಎಲ್ಲಾ ಕೇಸ್‌ಗಳನ್ನು ಕೊನೆಗೊಳಿಸಲು ಬಯಸುತ್ತೇನೆ. ಅಂತಿಮ ಒಪ್ಪಂದದ ಮೊತ್ತ ಕೊಡಲು ಸಿದ್ಧನಿದ್ದೇನೆ. ಮಧ್ಯಸ್ಥರ ಮುಂದೆ ಇಡಬಹುದಾದ ನಿಯಮಗಳನ್ನು ದಯವಿಟ್ಟು ಸೂಚಿಸಿ.",
        "ನಮ್ಮ ಎಲ್ಲಾ ವ್ಯಾಜ್ಯಗಳು ಕೊನೆಗೊಳ್ಳಲು ಅಂತಿಮ ಒಪ್ಪಂದದ ಮೊತ್ತ ಕೊಡಲು ಒಪ್ಪಿದ್ದೇನೆ. ಒಪ್ಪಂದದಲ್ಲಿ ಯಾವ ನಿಯಮಗಳು ಇರಬೇಕು?"],
    ro=["Namma naduvina ella case galannu konegolisalu bayasuttene. Antima oppandada motta kodalu siddhaniddene. Madhyastara munde idabahudada niyamagalanu dayavittu soochisi.",
        "Namma ella vyajyagalu konegollalu antima oppandada motta kodalu oppiddene. Oppandadalli yava niyamagalu irabeku?"],
    issues={"divorce": "requested"},
    facts={"divorce_asked": "supported", "lump_sum_settlement": "supported",
           "money_fact": "supported", "in_scope": "supported"},
    enums=dict(SPOUSE_M)))
_reg(B("residence_asked_to_leave", "hn_b",
    en=["One day my husband asked me to leave the house, saying he needs some time alone. When I tried to return, he did not take me back.",
        "My husband told me to leave our matrimonial house. I went away, and now he will not let me come back home."],
    kn=["ಒಂದು ದಿನ ನನ್ನ ಗಂಡ ನನಗೆ ಸ್ವಲ್ಪ ಸಮಯ ಒಬ್ಬಂಟಿಯಾಗಿರಬೇಕು ಎಂದು ಮನೆ ಬಿಟ್ಟು ಹೋಗುವಂತೆ ಕೇಳಿದನು. ನಾನು ಹಿಂತಿರುಗಲು ಪ್ರಯತ್ನಿಸಿದಾಗ ಅವನು ನನ್ನನ್ನು ಮರಳಿ ತೆಗೆದುಕೊಳ್ಳಲಿಲ್ಲ.",
        "ನನ್ನ ಗಂಡ ನಮ್ಮ ಮನೆ ಬಿಟ್ಟು ಹೋಗುವಂತೆ ಹೇಳಿದನು. ನಾನು ಹೋದೆ, ಈಗ ಅವನು ನನ್ನನ್ನು ಮನೆಗೆ ಮರಳಿ ಬರಲು ಬಿಡುತ್ತಿಲ್ಲ."],
    ro=["Ondu dina nanna ganda nanage swalpa samaya obbantiyagirabeku anta mane bittu hoguvante kelidanu. Nanu hintirugalu prayatnisidaga avanu nannannu marali tegedukollalilla.",
        "Nanna ganda namma mane bittu hoguvante helidanu. Nanu hode, ega avanu nannannu manege marali baralu biduttilla."],
    issues={"residence": "requested"},
    facts={"residence_claim": "supported",
           "coercive_eviction_or_lockout": "supported",
           "in_scope": "supported"},
    enums=dict(SPOUSE)))
_reg(B("joint_property_rights", "core",
    en=["Can a wife claim rights in the joint property of her husband? The agreement and share certificates are in both our names.",
        "My husband and I bought a flat together. Can I claim my rights in this [[joint_property_claim:joint property]]?"],
    kn=["ಹೆಂಡತಿ ತನ್ನ ಗಂಡನ ಜಂಟಿ ಆಸ್ತಿಯಲ್ಲಿ ಹಕ್ಕುಗಳನ್ನು ಕೇಳಬಹುದೇ? ಒಪ್ಪಂದ ಮತ್ತು ಷೇರು ಪ್ರಮಾಣಪತ್ರಗಳು ಇಬ್ಬರ ಹೆಸರಿನಲ್ಲಿವೆ.",
        "ನನ್ನ ಗಂಡ ಮತ್ತು ನಾನು ಒಟ್ಟಿಗೆ ಫ್ಲ್ಯಾಟ್ ಖರೀದಿಸಿದೆವು. ಈ [[joint_property_claim:ಜಂಟಿ ಆಸ್ತಿ]]ಯಲ್ಲಿ ನನ್ನ ಹಕ್ಕುಗಳನ್ನು ಕೇಳಬಹುದೇ?"],
    ro=["Hendati tanna gandana janti astiyalli hakkugalannu kelabahude? Oppanda mattu sheru pramanapatragalu ibbara hesarinallive.",
        "Nanna ganda mattu nanu ottige flat khareedisidevu. Ee [[joint_property_claim:janti asti]]yalli nanna hakkugalannu kelabahude?"],
    issues={"joint_property": "requested"},
    facts={"joint_property_claim": "supported", "in_scope": "supported"},
    enums=dict(SPOUSE)))
_reg(B("third_party_son", "hn_f",
    en=["I am asking for my mother. Her husband, my father, gives her no money and beats her. What can she do to get protection and support?",
        "My mother-in-law is not treated well by her son and daughter-in-law. She gets no money for food or medicines. What help can she get?"],
    kn=["ನಾನು ನನ್ನ ತಾಯಿಗಾಗಿ ಕೇಳುತ್ತಿದ್ದೇನೆ. ಅವಳ ಗಂಡ, ನನ್ನ ತಂದೆ, ಅವಳಿಗೆ ಹಣ ಕೊಡುವುದಿಲ್ಲ ಮತ್ತು ಅವಳನ್ನು ಹೊಡೆಯುತ್ತಾನೆ. ರಕ್ಷಣೆ ಮತ್ತು ಬೆಂಬಲ ಪಡೆಯಲು ಅವಳು ಏನು ಮಾಡಬಹುದು?",
        "ನನ್ನ ಅತ್ತೆಗೆ ಅವರ ಮಗ ಮತ್ತು ಸೊಸೆ ಚೆನ್ನಾಗಿ ನಡೆಸಿಕೊಳ್ಳುವುದಿಲ್ಲ. ಊಟ ಅಥವಾ ಔಷಧಿಗೆ ಅವರಿಗೆ ಹಣ ಸಿಗುವುದಿಲ್ಲ. ಅವರಿಗೆ ಏನು ಸಹಾಯ ಸಿಗುತ್ತದೆ?"],
    ro=["Nanu nanna tayigagi keluttiddene. Avala ganda, nanna tande, avalige hana koduvudilla mattu avalannu hodeyuttane. Rakshane mattu bembala padeyalu avalu enu madabahudu?",
        "Nanna attege avara maga mattu sose chennagi nadesikolluvudilla. Uta athava aushadhige avarige hana siguvudilla. Avarige enu sahaya siguttade?"],
    issues={},
    facts={"in_scope": "supported"},
    enums={"claimant_sex": "U", "claimant_role": "other"}))
_reg(B("neg_soft_divorce", "neg",
    en=["My wife is not agreeing for the divorce, and I do not want to force her. I only want [[maintenance:maintenance]] for our {child_word}.",
        "She will not agree to end the marriage, so a divorce is not possible now. I only need money for my {child_word}'s school fees."],
    kn=["ನನ್ನ ಹೆಂಡತಿ ವಿಚ್ಛೇದನಕ್ಕೆ ಒಪ್ಪುತ್ತಿಲ್ಲ, ಅವಳನ್ನು ಒತ್ತಾಯಿಸಲು ನನಗೆ ಇಷ್ಟವಿಲ್ಲ. ನಮ್ಮ {child_word}ಗಾಗಿ [[maintenance:ಜೀವನಾಂಶ]] ಮಾತ್ರ ಬೇಕು.",
        "ಅವಳು ಮದುವೆ ಕೊನೆಗೊಳಿಸಲು ಒಪ್ಪುವುದಿಲ್ಲ, ಆದ್ದರಿಂದ ಈಗ ವಿಚ್ಛೇದನ ಸಾಧ್ಯವಿಲ್ಲ. ನನ್ನ {child_word}ನ ಶಾಲಾ ಶುಲ್ಕಕ್ಕಾಗಿ ಮಾತ್ರ ಹಣ ಬೇಕು."],
    ro=["Nanna hendati divorce ge opputtilla, avalannu ottayisalu nanage ishtavilla. Namma {child_word}gagi [[maintenance:jeevanamsha]] matra beku.",
        "Avalu maduve konegolisalu oppuvudilla, adarinda ega divorce sadhyavilla. Nanna {child_word}na shala shulka kagi matra hana beku."],
    issues={"divorce": "denied", "maintenance": "requested"},
    facts={"divorce_asked": "denied", "money_fact": "supported",
           "child_maintenance_only": "supported", "child_fact": "supported",
           "minor_child": "supported", "school_fees_fact": "supported",
           "in_scope": "supported"},
    enums=dict(SPOUSE_M)))
_reg(B("neg_soft_js", "neg",
    en=["I never want to marry again, so a divorce is not essential for me. I only want to live separately from my husband with a court order.",
        "Ending the marriage is not necessary for me. I only want [[judicial_separation_only:judicial separation]] and to live apart."],
    kn=["ನಾನು ಮತ್ತೆ ಮದುವೆಯಾಗಲು ಎಂದೂ ಬಯಸುವುದಿಲ್ಲ, ಆದ್ದರಿಂದ ವಿಚ್ಛೇದನ ನನಗೆ ಅಗತ್ಯವಿಲ್ಲ. ಕೋರ್ಟ್ ಆದೇಶದೊಂದಿಗೆ ನನ್ನ ಗಂಡನಿಂದ ಬೇರೆಯಾಗಿ ವಾಸಿಸಲು ಮಾತ್ರ ಬಯಸುತ್ತೇನೆ.",
        "ಮದುವೆ ಕೊನೆಗೊಳಿಸುವುದು ನನಗೆ ಅಗತ್ಯವಿಲ್ಲ. ನನಗೆ [[judicial_separation_only:ನ್ಯಾಯಾಂಗ ಬೇರ್ಪಡಿಕೆ]] ಮಾತ್ರ ಬೇಕು, ಬೇರೆಯಾಗಿ ವಾಸಿಸಲು ಬಯಸುತ್ತೇನೆ."],
    ro=["Nanu matte maduveyagalu endu bayasuvudilla, adarinda divorce nanage agatyavilla. Court adeshadondige nanna gandana inda bereyagi vaasisalu matra bayasuttene.",
        "Maduve konegolisuvudu nanage agatyavilla. Nanage [[judicial_separation_only:nyayanga berpadike]] matra beku, bereyagi vaasisalu bayasuttene."],
    issues={"divorce": "denied"},
    facts={"judicial_separation_only": "supported",
           "divorce_asked": "denied", "in_scope": "supported"},
    enums=dict(SPOUSE)))

# --- hard negative A: custody vs residence co-location --------------------
_reg(B("coloc_stay_with_child", "hn_a",
    en=["I want my {child_age}-year-old {child_word} to keep living at home with me. This is about living together at home.",
        "My {child_word} and I live in our house. I want us to keep staying in this house together."],
    kn=["ನನ್ನ {child_age} ವರ್ಷದ {child_word} ಮನೆಯಲ್ಲಿ ನನ್ನ ಜೊತೆಯೇ ವಾಸ ಮುಂದುವರಿಸಬೇಕೆಂದು ಬಯಸುತ್ತೇನೆ. ಇದು ಮನೆಯಲ್ಲಿ ಒಟ್ಟಿಗೆ ವಾಸಿಸುವ ಬಗ್ಗೆ.",
        "ನನ್ನ {child_word} ಮತ್ತು ನಾನು ನಮ್ಮ ಮನೆಯಲ್ಲಿ ವಾಸಿಸುತ್ತೇವೆ. ನಾವು ಈ ಮನೆಯಲ್ಲಿ ಒಟ್ಟಿಗೆ ಇರುವುದನ್ನು ಮುಂದುವರಿಸಬೇಕು."],
    ro=["Nanna {child_age} varshada {child_word} maneyalli nanna joteye vaasa munduvarisabekendu bayasuttene. Idu maneyalli ottige vaasisuva bagge.",
        "Nanna {child_word} mattu nanu namma maneyalli vaasistevu. Navu ee maneyalli ottige iruvudannu munduvarisabeku."],
    issues={"residence": "requested", "custody": "incidental"},
    facts={"residence_claim": "supported", "custody_claim": "denied",
           "child_fact": "supported", "minor_child": "supported",
           "in_scope": "supported"},
    enums=dict(SPOUSE)))
_reg(B("coloc_custody_word", "hn_a",
    en=["My {child_word} should remain in my care, not go to my husband. I am asking for [[custody:custody]] of my {child_word}.",
        "My husband wants to take our {child_word} away. I want the court to give me [[custody:custody]]."],
    kn=["ನನ್ನ {child_word} ನನ್ನ ಆರೈಕೆಯಲ್ಲಿ ಇರಬೇಕು, ನನ್ನ ಗಂಡನ ಬಳಿ ಅಲ್ಲ. ನನ್ನ {child_word}ನ [[custody:ಪಾಲನೆ]] ಕೇಳುತ್ತಿದ್ದೇನೆ.",
        "ನನ್ನ ಗಂಡ ನಮ್ಮ {child_word}ನನ್ನು ಕರೆದುಕೊಂಡು ಹೋಗಲು ಬಯಸುತ್ತಾನೆ. ಕೋರ್ಟ್ ನನಗೆ [[custody:ಪಾಲನೆ]] ನೀಡಬೇಕು."],
    ro=["Nanna {child_word} nanna aaraikeyalli irabeku, nanna gandana bali alla. Nanna {child_word}na [[custody:paalane]] keluttiddene.",
        "Nanna ganda namma {child_word}nannu karedukondu hogalu bayasuttane. Court nanage [[custody:paalane]] needabeku."],
    issues={"custody": "requested", "residence": "incidental"},
    facts={"custody_claim": "supported", "residence_claim": "denied",
           "child_fact": "supported", "minor_child": "supported",
           "in_scope": "supported"},
    enums=dict(SPOUSE)))

# --- hard negative F: hypothetical / third-party / quoted / pre-BNSS -------
_reg(B("hypothetical", "hn_f",
    en=["Suppose a woman's husband stops giving her any money. Could she ask the court for [[maintenance:maintenance]]?",
        "If a husband throws his wife out of their house, what rights would she have to stay there?",
        "Imagine a mother whose son earns well but gives her nothing. Would she be able to ask for support?"],
    kn=["ಒಂದು ವೇಳೆ ಒಬ್ಬ ಮಹಿಳೆಯ ಗಂಡ ಅವಳಿಗೆ ಹಣ ಕೊಡುವುದನ್ನು ನಿಲ್ಲಿಸಿದರೆ, ಅವಳು ಕೋರ್ಟ್‌ನಲ್ಲಿ [[maintenance:ಜೀವನಾಂಶ]] ಕೇಳಬಹುದೇ?",
        "ಒಂದು ವೇಳೆ ಗಂಡ ಹೆಂಡತಿಯನ್ನು ಮನೆಯಿಂದ ಹೊರಹಾಕಿದರೆ, ಅಲ್ಲಿ ಇರಲು ಅವಳಿಗೆ ಏನು ಹಕ್ಕುಗಳಿರುತ್ತವೆ?",
        "ಒಬ್ಬ ತಾಯಿಯ ಮಗ ಚೆನ್ನಾಗಿ ಸಂಪಾದಿಸಿದರೂ ಅವಳಿಗೆ ಏನೂ ಕೊಡದಿದ್ದರೆ, ಅವಳು ಬೆಂಬಲ ಕೇಳಬಹುದೇ ಎಂದು ಊಹಿಸಿ."],
    ro=["Ondu vele obba mahileyaga ganda avalige hana koduvudannu nillisidare, avalu court nalli [[maintenance:jeevanamsha]] kelabahude?",
        "Ondu vele ganda hendatiyannu maneyinda horahakidare, alli iralu avalige enu hakkugaliruttave?",
        "Obba tayiya maga chennagi sampadisidaru avalige enu kodadiddare, avalu bembala kelabahude anta uuhisi."],
    issues={},
    facts={"in_scope": "supported"},
    enums={"claimant_sex": "U", "claimant_role": "other",
           "modality_time": "hypothetical"}))
_reg(B("third_party", "hn_f",
    en=["My friend's husband beats her at home. What can she do to get protection and support?",
        "My neighbour's daughter was thrown out of her house by her in-laws. What help can she get?",
        "My sister's husband gives her no money for the house. Can she ask for [[maintenance:maintenance]]?"],
    kn=["ನನ್ನ ಗೆಳತಿಯ ಗಂಡ ಮನೆಯಲ್ಲಿ ಅವಳನ್ನು ಹೊಡೆಯುತ್ತಾನೆ. ರಕ್ಷಣೆ ಮತ್ತು ಬೆಂಬಲ ಪಡೆಯಲು ಅವಳು ಏನು ಮಾಡಬಹುದು?",
        "ನನ್ನ ನೆರೆಯವರ ಮಗಳನ್ನು ಅತ್ತೆ-ಮಾವ ಮನೆಯಿಂದ ಹೊರಹಾಕಿದರು. ಅವಳಿಗೆ ಏನು ಸಹಾಯ ಸಿಗುತ್ತದೆ?",
        "ನನ್ನ ತಂಗಿಯ ಗಂಡ ಮನೆಗೆ ಹಣ ಕೊಡುವುದಿಲ್ಲ. ಅವಳು [[maintenance:ಜೀವನಾಂಶ]] ಕೇಳಬಹುದೇ?"],
    ro=["Nanna gelatiya ganda maneyalli avalannu hodeyuttane. Rakshane mattu bembala padeyalu avalu enu madabahudu?",
        "Nanna nereyavara magalannu atte-mava maneyinda horahakidaru. Avalige enu sahaya siguttade?",
        "Nanna tangiya ganda manege hana koduvudilla. Avalu [[maintenance:jeevanamsha]] kelabahude?"],
    issues={},
    facts={"in_scope": "supported"},
    enums={"claimant_sex": "U", "claimant_role": "other"}))
_reg(B("quoted", "hn_f",
    en=["My sister told me, \"My husband beats me and gives me no money.\" She wants to know what she can do.",
        "A woman at work said, \"My in-laws took my gold and will not return it.\" She asked me what the law says."],
    kn=["ನನ್ನ ತಂಗಿ ನನಗೆ ಹೇಳಿದಳು, \"ನನ್ನ ಗಂಡ ನನ್ನನ್ನು ಹೊಡೆಯುತ್ತಾನೆ ಮತ್ತು ಹಣ ಕೊಡುವುದಿಲ್ಲ.\" ಅವಳು ಏನು ಮಾಡಬಹುದು ಎಂದು ತಿಳಿಯಲು ಬಯಸುತ್ತಾಳೆ.",
        "ಕೆಲಸದಲ್ಲಿ ಒಬ್ಬ ಮಹಿಳೆ ಹೇಳಿದಳು, \"ನನ್ನ ಅತ್ತೆ-ಮಾವ ನನ್ನ ಚಿನ್ನ ತೆಗೆದುಕೊಂಡು ವಾಪಸ್ ಕೊಡುವುದಿಲ್ಲ.\" ಕಾನೂನು ಏನು ಹೇಳುತ್ತದೆ ಎಂದು ಅವಳು ಕೇಳಿದಳು."],
    ro=["Nanna tangi nanage helidalu, \"Nanna ganda nannannu hodeyuttane mattu hana koduvudilla.\" Avalu enu madabahudu anta tiliyalu bayasutale.",
        "Kelasadalli obba mahile helidalu, \"Nanna atte-mava nanna chinna tegedukondu vapas koduvudilla.\" Kanoonu enu heluttade anta avalu kelidalu."],
    issues={},
    facts={"in_scope": "supported"},
    enums={"claimant_sex": "U", "claimant_role": "other",
           "modality_time": "quoted"}))
_reg(B("pre_bnss", "hn_f",
    en=["In 2023, before the new criminal law came in, the court ordered my husband to pay me under the old maintenance law. He has not paid since then.",
        "My husband was ordered to pay support under the old CrPC 125 law in 2022. He stopped paying last year. What can I do now?"],
    kn=["2023ರಲ್ಲಿ, ಹೊಸ ಕ್ರಿಮಿನಲ್ ಕಾನೂನು ಬರುವ ಮೊದಲು, ಕೋರ್ಟ್ ನನ್ನ ಗಂಡ ಹಳೆಯ ಜೀವನಾಂಶ ಕಾನೂನಿನಡಿ ಹಣ ಕೊಡಬೇಕು ಎಂದು ಆದೇಶಿಸಿತ್ತು. ಅಂದಿನಿಂದ ಅವನು ಕೊಟ್ಟಿಲ್ಲ.",
        "2022ರಲ್ಲಿ ಹಳೆಯ CrPC 125 ಕಾನೂನಿನಡಿ ನನ್ನ ಗಂಡ ಬೆಂಬಲ ಕೊಡಬೇಕು ಎಂದು ಆದೇಶಿಸಲಾಗಿತ್ತು. ಕಳೆದ ವರ್ಷ ಅವನು ಕೊಡುವುದನ್ನು ನಿಲ್ಲಿಸಿದನು. ಈಗ ನಾನು ಏನು ಮಾಡಬಹುದು?"],
    ro=["2023 ralli, hosa criminal kanoonu baruva modalu, court nanna ganda haleya jeevanamsha kanoonina adi hana kodabeku anta adeshisittu. Andininda avanu kottilla.",
        "2022 ralli haleya CrPC 125 kanoonina adi nanna ganda bembala kodabeku anta adeshisalagittu. Kaleda varsha avanu koduvudannu nillisidanu. Eega nanu enu madabahudu?"],
    issues={"maintenance": "requested"},
    facts={"money_fact": "supported",
           "existing_order_enforcement": "supported",
           "in_scope": "supported"},
    enums={"claimant_sex": F, "claimant_role": "spouse",
           "modality_time": "past"}))
_reg(B("past_event", "hn_f",
    en=["My husband left our home five years ago and never sent any money after that. I managed alone all these years.",
        "Three years ago my husband stopped paying for our {child_word}'s school. I have been paying everything myself since then."],
    kn=["ನನ್ನ ಗಂಡ ಐದು ವರ್ಷಗಳ ಹಿಂದೆ ನಮ್ಮ ಮನೆ ಬಿಟ್ಟು ಹೋದನು, ಆ ನಂತರ ಎಂದೂ ಹಣ ಕಳುಹಿಸಲಿಲ್ಲ. ಈ ಎಲ್ಲಾ ವರ್ಷಗಳೂ ನಾನೊಬ್ಬಳೇ ನಿಭಾಯಿಸಿದೆ.",
        "ಮೂರು ವರ್ಷಗಳ ಹಿಂದೆ ನನ್ನ ಗಂಡ ನಮ್ಮ {child_word}ನ ಶಾಲೆಗೆ ಹಣ ಕೊಡುವುದನ್ನು ನಿಲ್ಲಿಸಿದನು. ಅಂದಿನಿಂದ ಎಲ್ಲವನ್ನೂ ನಾನೇ ಕೊಡುತ್ತಿದ್ದೇನೆ."],
    ro=["Nanna ganda aidu varshagala hinde namma mane bittu hodanu, aa nantara endu hana kaluhisalilla. Ee ella varshagalu nanobbale nibhayiside.",
        "Mooru varshagala hinde nanna ganda namma {child_word}na shalege hana koduvudannu nillisidanu. Andininda ellavannu nane koduttiddene."],
    issues={"maintenance": "requested"},
    facts={"money_fact": "supported", "in_scope": "supported"},
    enums={"claimant_sex": F, "claimant_role": "spouse",
           "modality_time": "past"}))

# --- negation primaries ----------------------------------------------------
_reg(B("neg_maintenance", "neg",
    en=["I do not want any [[maintenance:maintenance]] from my husband. I only want [[custody:custody]] of my {child_word}.",
        "I am not asking for money. I only want my {child_age}-year-old {child_word} to remain in my care."],
    kn=["ನನ್ನ ಗಂಡನಿಂದ ಯಾವುದೇ [[maintenance:ಜೀವನಾಂಶ]] ಬೇಡ. ನನ್ನ {child_word}ನ [[custody:ಪಾಲನೆ]] ಮಾತ್ರ ಬೇಕು.",
        "ನಾನು ಹಣ ಕೇಳುತ್ತಿಲ್ಲ. ನನ್ನ {child_age} ವರ್ಷದ {child_word} ನನ್ನ ಆರೈಕೆಯಲ್ಲಿ ಇರಬೇಕು ಅಷ್ಟೇ."],
    ro=["Nanna gandana inda yavude [[maintenance:jeevanamsha]] beda. Nanna {child_word}na [[custody:paalane]] matra beku.",
        "Nanu hana keluttilla. Nanna {child_age} varshada {child_word} nanna aaraikeyalli irabeku ashte."],
    issues={"maintenance": "denied", "custody": "requested"},
    facts={"money_fact": "denied", "custody_claim": "supported",
           "child_fact": "supported", "minor_child": "supported",
           "in_scope": "supported"},
    enums=dict(SPOUSE)))
_reg(B("neg_divorce", "neg",
    en=["I do not want a [[divorce:divorce]] at all. I only want my husband to start paying [[maintenance:maintenance]] again.",
        "Ending the marriage is not what I want. I just need monthly support from my husband."],
    kn=["ನನಗೆ [[divorce:ವಿಚ್ಛೇದನ]] ಖಂಡಿತ ಬೇಡ. ನನ್ನ ಗಂಡ ಮತ್ತೆ [[maintenance:ಜೀವನಾಂಶ]] ಕೊಡಲು ಪ್ರಾರಂಭಿಸಬೇಕು ಅಷ್ಟೇ.",
        "ಮದುವೆ ಕೊನೆಗೊಳಿಸುವುದು ನನಗೆ ಬೇಡ. ನನ್ನ ಗಂಡನಿಂದ ತಿಂಗಳ ಬೆಂಬಲ ಬೇಕು ಅಷ್ಟೇ."],
    ro=["Nanage [[divorce:vichchhedana]] khandita beda. Nanna ganda matte [[maintenance:jeevanamsha]] kodalu prarambhisabeku ashte.",
        "Maduve konegolisuvudu nanage beda. Nanna gandana inda tingala bembala beku ashte."],
    issues={"divorce": "denied", "maintenance": "requested"},
    facts={"divorce_asked": "denied", "money_fact": "supported",
           "in_scope": "supported"},
    enums=dict(SPOUSE)))
_reg(B("neg_custody", "neg",
    en=["I am not asking for the children's [[custody:custody]]. I only want monthly support for myself and my {child_word}.",
        "Custody is already settled between us. I only need help with monthly support."],
    kn=["ಮಕ್ಕಳ [[custody:ಪಾಲನೆ]] ಕೇಳುತ್ತಿಲ್ಲ. ನನಗಾಗಿ ಮತ್ತು ನನ್ನ {child_word}ಗಾಗಿ ತಿಂಗಳ ಬೆಂಬಲ ಮಾತ್ರ ಬೇಕು.",
        "ಪಾಲನೆ ನಮ್ಮ ನಡುವೆ ಈಗಾಗಲೇ ತೀರ್ಮಾನವಾಗಿದೆ. ತಿಂಗಳ ಬೆಂಬಲಕ್ಕಾಗಿ ಮಾತ್ರ ಸಹಾಯ ಬೇಕು."],
    ro=["Makkala [[custody:paalane]] keluttilla. Nanagagi mattu nanna {child_word}gagi tingala bembala matra beku.",
        "Paalane namma naduve egagale teermanavagide. Tingala bembalakkagi matra sahaya beku."],
    issues={"custody": "denied", "maintenance": "requested"},
    facts={"custody_claim": "denied", "money_fact": "supported",
           "child_fact": "supported", "minor_child": "supported",
           "in_scope": "supported"},
    enums=dict(SPOUSE)))

_reg(B("neg_decree_mutual", "neg",
    en=["We do not want a [[mutual_consent:mutual consent divorce]], and there is no decree yet. I only want [[maintenance:maintenance]].",
        "There is no court decree between us, and we have not agreed to a mutual divorce."],
    kn=["ನಮಗೆ [[mutual_consent:ಪರಸ್ಪರ ಒಪ್ಪಿಗೆಯ ವಿಚ್ಛೇದನ]] ಬೇಡ, ಇನ್ನೂ ಯಾವುದೇ ತೀರ್ಪು ಇಲ್ಲ. ನನಗೆ [[maintenance:ಜೀವನಾಂಶ]] ಮಾತ್ರ ಬೇಕು.",
        "ನಮ್ಮ ನಡುವೆ ಕೋರ್ಟ್ ತೀರ್ಪು ಇಲ್ಲ, ಪರಸ್ಪರ ಒಪ್ಪಿಗೆಯ ವಿಚ್ಛೇದನಕ್ಕೂ ಒಪ್ಪಿಲ್ಲ."],
    ro=["Namage [[mutual_consent:paraspara oppigeya divorce]] beda, innu yavude teerpu illa. Nanage [[maintenance:jeevanamsha]] matra beku.",
        "Namma naduve court teerpu illa, paraspara oppigeya divorce kku oppilla."],
    issues={"divorce": "denied", "maintenance": "requested"},
    facts={"mutual_consent": "denied", "decree": "denied",
           "divorce_asked": "denied", "money_fact": "supported",
           "in_scope": "supported"},
    enums=dict(SPOUSE)))
_reg(B("neg_no_order", "neg",
    en=["No court has ordered [[maintenance:maintenance]] for me yet. I want to ask for it for the first time.",
        "There is no maintenance order in my favour so far. Can I ask the court to make one?"],
    kn=["ಕೋರ್ಟ್ ಇನ್ನೂ ನನಗೆ [[maintenance:ಜೀವನಾಂಶ]] ಆದೇಶಿಸಿಲ್ಲ. ಮೊದಲ ಬಾರಿಗೆ ಕೇಳಲು ಬಯಸುತ್ತೇನೆ.",
        "ನನ್ನ ಪರವಾಗಿ ಇಲ್ಲಿಯವರೆಗೆ ಯಾವುದೇ ಜೀವನಾಂಶ ಆದೇಶವಿಲ್ಲ. ಕೋರ್ಟ್ ಆದೇಶ ಮಾಡುವಂತೆ ಕೇಳಬಹುದೇ?"],
    ro=["Court innu nanage [[maintenance:jeevanamsha]] adeshisilla. Modala barige kelalu bayasuttene.",
        "Nanna paravagi illiyavarage yavude jeevanamsha adeshavilla. Court adesha maduvante kelabahude?"],
    issues={"maintenance": "requested"},
    facts={"existing_order_enforcement": "denied",
           "money_fact": "supported", "in_scope": "supported"},
    enums=dict(SPOUSE)))

# --- conflicting ------------------------------------------------------------
_reg(B("conflict_divorce", "conflict",
    en=["I want a [[divorce:divorce]] from my husband. Actually, no, I do not want a divorce, I want him to come back home and live with me.",
        "One moment I want to end the marriage, the next moment I want my husband back. I am confused about what to ask for."],
    kn=["ನನ್ನ ಗಂಡನಿಂದ [[divorce:ವಿಚ್ಛೇದನ]] ಬೇಕು. ಇಲ್ಲ, ವಿಚ್ಛೇದನ ಬೇಡ, ಅವನು ಮನೆಗೆ ಮರಳಿ ನನ್ನ ಜೊತೆ ಬದುಕಬೇಕು.",
        "ಒಂದು ಕ್ಷಣ ಮದುವೆ ಕೊನೆಗೊಳಿಸಲು ಬಯಸುತ್ತೇನೆ, ಮರುಕ್ಷಣ ನನ್ನ ಗಂಡ ವಾಪಸ್ ಬೇಕು. ಏನು ಕೇಳಬೇಕೆಂದು ಗೊಂದಲವಿದೆ."],
    ro=["Nanna gandana inda [[divorce:vichchhedana]] beku. Illa, divorce beda, avanu manege marali nanna jothe badukabeku.",
        "Ondu kshana maduve konegolisalu bayasuttene, marukshana nanna ganda vapas beku. Enu kelabekendu gondalavide."],
    issues={"divorce": "uncertain", "restitution": "requested"},
    facts={"divorce_asked": "conflicting", "restitution_asked": "supported",
           "in_scope": "supported"},
    enums=dict(SPOUSE)))

# --- hard negative F: 12 out-of-scope domains ------------------------------
# Each OOS block: in_scope denied, every issue uncertain, every other fact
# unknown. The family-law trigger word (husband/wife/friend's divorce etc.)
# is present only as noise, never as a claim.
OOS_DOMAINS = [
    ("oos_rent", "rent / landlord-tenant",
     ["My landlord has increased my house rent again and will not repair the leaking roof. What can a tenant do?",
      "My husband's landlord is asking for three months' rent in advance. Is that allowed under tenancy law?"],
     ["ನನ್ನ ಮನೆಯ ಮಾಲೀಕರು ಮತ್ತೆ ಬಾಡಿಗೆ ಹೆಚ್ಚಿಸಿದ್ದಾರೆ, ಸೋರುವ ಛಾವಣಿಯನ್ನು ಸರಿಪಡಿಸುವುದಿಲ್ಲ. ಬಾಡಿಗೆದಾರ ಏನು ಮಾಡಬಹುದು?",
      "ನನ್ನ ಗಂಡನ ಮನೆಯ ಮಾಲೀಕರು ಮೂರು ತಿಂಗಳ ಬಾಡಿಗೆ ಮುಂಗಡ ಕೇಳುತ್ತಿದ್ದಾರೆ. ಬಾಡಿಗೆ ಕಾನೂನಿನಲ್ಲಿ ಅದು ಸರಿಯೇ?"],
     ["Nanna maneya malikaru matte badige hechisiddare, soruva chavaniyannu saripadisuvudilla. Badigedara enu madabahudu?",
      "Nanna gandana maneya malikaru mooru tingala badige mungada keluttiddare. Badige kanoonina alli adu sariye?"]),
    ("oos_employment", "employment / salary from employer",
     ["My employer has held back my pay for the last two months. How do I claim my pending salary from my employer?",
      "My boss cut my pay without notice. Where do I complain about unpaid wages?"],
     ["ನನ್ನ ಉದ್ಯೋಗದಾತರು ಕಳೆದ ಎರಡು ತಿಂಗಳಿನಿಂದ ನನ್ನ ಸಂಬಳ ತಡೆಹಿಡಿದಿದ್ದಾರೆ. ನನ್ನ ಉದ್ಯೋಗದಾತರಿಂದ ಬಾಕಿ ಸಂಬಳವನ್ನು ಹೇಗೆ ಕೇಳುವುದು?",
      "ನನ್ನ ಬಾಸ್ ಸೂಚನೆ ಇಲ್ಲದೆ ನನ್ನ ಸಂಬಳ ಕಡಿತ ಮಾಡಿದರು. ಪಾವತಿಯಾಗದ ವೇತನದ ಬಗ್ಗೆ ಎಲ್ಲಿ ದೂರು ನೀಡುವುದು?"],
     ["Nanna udyogadataru kaleda eradu tingalinda nanna sambala tadehididdare. Nanna udyogadatarinda baki sambalavannu hege keluvudu?",
      "Nanna boss soochane illade nanna sambala kadita madidaru. Pavatiyagada vetanada bagge elli duru needuvudu?"]),
    ("oos_consumer", "consumer refund",
     ["I bought a washing machine online and it stopped working in a week. The shop refuses a refund. What can I do?",
      "The store sold me a damaged phone and will not replace it. How do I get my money back?"],
     ["ನಾನು ಆನ್‌ಲೈನ್‌ನಲ್ಲಿ ವಾಷಿಂಗ್ ಮಷೀನ್ ಖರೀದಿಸಿದೆ, ಒಂದು ವಾರದಲ್ಲಿ ಅದು ಕೆಲಸ ಮಾಡುವುದನ್ನು ನಿಲ್ಲಿಸಿತು. ಅಂಗಡಿ ಹಣ ವಾಪಸ್ ಕೊಡಲು ನಿರಾಕರಿಸುತ್ತಿದೆ. ನಾನು ಏನು ಮಾಡಬಹುದು?",
      "ಅಂಗಡಿ ನನಗೆ ಹಾನಿಗೊಳಗಾದ ಫೋನ್ ಮಾರಿತು, ಬದಲಿಸಲು ನಿರಾಕರಿಸುತ್ತಿದೆ. ನನ್ನ ಹಣವನ್ನು ಹೇಗೆ ವಾಪಸ್ ಪಡೆಯುವುದು?"],
     ["Nanu online nalli washing machine khareedide, ondu varadalli adu kelasa maduvudannu nillisitu. Angadi hana vapas kodalu nirakarisuttide. Nanu enu madabahudu?",
      "Angadi nanage hanigolagada phone maritu, badalisalu nirakarisuttide. Nanna hanavannu hege vapas padeyuvudu?"]),
    ("oos_cheque", "cheque bounce",
     ["A man gave me a cheque for fifty thousand rupees and it bounced. How do I recover the cheque amount?",
      "My friend borrowed money from me and his cheque was returned unpaid. What is the process for a bounced cheque?"],
     ["ಒಬ್ಬ ವ್ಯಕ್ತಿ ನನಗೆ ಐವತ್ತು ಸಾವಿರ ರೂಪಾಯಿ ಚೆಕ್ ಕೊಟ್ಟನು, ಅದು ಬೌನ್ಸ್ ಆಯಿತು. ಚೆಕ್ ಮೊತ್ತವನ್ನು ಹೇಗೆ ವಾಪಸ್ ಪಡೆಯುವುದು?",
      "ನನ್ನ ಗೆಳೆಯ ನನ್ನಿಂದ ಹಣ ಎರವಲು ಪಡೆದನು, ಅವನ ಚೆಕ್ ಪಾವತಿಯಾಗದೆ ವಾಪಸ್ ಬಂತು. ಬೌನ್ಸ್ ಚೆಕ್‌ಗೆ ಪ್ರಕ್ರಿಯೆ ಏನು?"],
     ["Obba vyakti nanage aivattu savira rupayi cheque kottanu, adu bounce ayitu. Cheque mottavannu hege vapas padeyuvudu?",
      "Nanna geleya nanninda hana eravalu padedanu, avana cheque pavati agade vapas bantu. Bounce cheque ge prakriye enu?"]),
    ("oos_tax", "income tax",
     ["I received an income tax notice for the last financial year. How do I reply to the tax department?",
      "My tax refund has not come for eight months. Where do I check the status of my refund?"],
     ["ಕಳೆದ ಆರ್ಥಿಕ ವರ್ಷಕ್ಕೆ ನನಗೆ ಆದಾಯ ತೆರಿಗೆ ನೋಟಿಸ್ ಬಂದಿದೆ. ತೆರಿಗೆ ಇಲಾಖೆಗೆ ಹೇಗೆ ಉತ್ತರಿಸುವುದು?",
      "ನನ್ನ ತೆರಿಗೆ ಮರುಪಾವತಿ ಎಂಟು ತಿಂಗಳಿಂದ ಬಂದಿಲ್ಲ. ನನ್ನ ಮರುಪಾವತಿಯ ಸ್ಥಿತಿಯನ್ನು ಎಲ್ಲಿ ಪರಿಶೀಲಿಸುವುದು?"],
     ["Kaleda arthika varshakke nanage adaya terige notice bandide. Terige ilakhege hege uttarisuvudu?",
      "Nanna terige marupavati entu tingalinda bandilla. Nanna marupavatiya sthitiyannu elli parishilisuvudu?"]),
    ("oos_theft", "criminal theft by a stranger",
     ["A thief stole my scooter from outside my house last night. How do I file a police complaint?",
      "Someone broke into my shop and stole cash from the drawer. What should I do first?"],
     ["ಕಳ್ಳನೊಬ್ಬ ಕಳೆದ ರಾತ್ರಿ ನನ್ನ ಮನೆಯ ಹೊರಗಿನಿಂದ ನನ್ನ ಸ್ಕೂಟರ್ ಕದ್ದನು. ಪೊಲೀಸ್ ದೂರು ಹೇಗೆ ನೀಡುವುದು?",
      "ಯಾರೋ ನನ್ನ ಅಂಗಡಿಗೆ ನುಗ್ಗಿ ಡ್ರಾಯರ್‌ನಿಂದ ಹಣ ಕದ್ದರು. ಮೊದಲು ನಾನು ಏನು ಮಾಡಬೇಕು?"],
     ["Kallanobba kaleda ratri nanna maneya horaginda nanna scooter kaddanu. Police duru hege needuvudu?",
      "Yaro nanna angadige nuggi drawer inda hana kaddaru. Modalu nanu enu madabeku?"]),
    ("oos_neighbour", "neighbour property dispute",
     ["My neighbour built a wall on my land without permission. How do I stop this encroachment?",
      "The people next door play loud music all night. Where do I complain about the noise?"],
     ["ನನ್ನ ನೆರೆಯವರು ಅನುಮತಿ ಇಲ್ಲದೆ ನನ್ನ ಜಮೀನಿನಲ್ಲಿ ಗೋಡೆ ಕಟ್ಟಿದ್ದಾರೆ. ಈ ಒತ್ತುವರಿಯನ್ನು ಹೇಗೆ ನಿಲ್ಲಿಸುವುದು?",
      "ಪಕ್ಕದ ಮನೆಯವರು ರಾತ್ರಿಯೆಲ್ಲ ಜೋರಾಗಿ ಸಂಗೀತ ಕೇಳುತ್ತಾರೆ. ಶಬ್ದದ ಬಗ್ಗೆ ಎಲ್ಲಿ ದೂರು ನೀಡುವುದು?"],
     ["Nanna nereyavaru anumati illade nanna jameeninalli gode kattiddare. Ee ottuvariyannu hege nillisuvudu?",
      "Pakkada maneyavaru ratriyella joragi sangeeta keluttare. Shabdada bagge elli duru needuvudu?"]),
    ("oos_traffic", "traffic challan",
     ["I got a traffic challan for jumping a signal. How do I pay the fine online?",
      "My driving licence was taken by the traffic police. How do I get it back?"],
     ["ಸಿಗ್ನಲ್ ಜಂಪ್ ಮಾಡಿದ್ದಕ್ಕಾಗಿ ನನಗೆ ಟ್ರಾಫಿಕ್ ಚಲನ್ ಬಂದಿದೆ. ದಂಡವನ್ನು ಆನ್‌ಲೈನ್‌ನಲ್ಲಿ ಹೇಗೆ ಪಾವತಿಸುವುದು?",
      "ಟ್ರಾಫಿಕ್ ಪೊಲೀಸರು ನನ್ನ ಡ್ರೈವಿಂಗ್ ಲೈಸೆನ್ಸ್ ತೆಗೆದುಕೊಂಡರು. ಅದನ್ನು ಹೇಗೆ ವಾಪಸ್ ಪಡೆಯುವುದು?"],
     ["Signal jump madiddakkagi nanage traffic challan bandide. Dandavannu online nalli hege pavatisuvudu?",
      "Traffic policesu nanna driving licence tegedukondaru. Adannu hege vapas padeyuvudu?"]),
    ("oos_bank_loan", "bank loan",
     ["The bank is asking me to repay a personal loan I took three years ago. Can I ask for more time to repay?",
      "My home loan interest rate went up and my monthly payment increased. Can I change to another bank?"],
     ["ಬ್ಯಾಂಕ್ ಮೂರು ವರ್ಷಗಳ ಹಿಂದೆ ನಾನು ತೆಗೆದುಕೊಂಡ ವೈಯಕ್ತಿಕ ಸಾಲವನ್ನು ಮರುಪಾವತಿಸಲು ಕೇಳುತ್ತಿದೆ. ಮರುಪಾವತಿಸಲು ಹೆಚ್ಚು ಸಮಯ ಕೇಳಬಹುದೇ?",
      "ನನ್ನ ಗೃಹ ಸಾಲದ ಬಡ್ಡಿ ದರ ಹೆಚ್ಚಾಯಿತು, ನನ್ನ ತಿಂಗಳ ಪಾವತಿ ಹೆಚ್ಚಾಯಿತು. ಬೇರೆ ಬ್ಯಾಂಕ್‌ಗೆ ಬದಲಾಯಿಸಬಹುದೇ?"],
     ["Bank mooru varshagala hinde nanu tegedukonda vaiyaktika salavannu marupavatisalu keluttide. Marupavatisalu hechu samaya kelabahude?",
      "Nanna gruha salada baddi dara hechayitu, nanna tingala pavati hechayitu. Bere bank ge badalayisabahude?"]),
    ("oos_visa", "visa / immigration",
     ["My work visa expires next month and my company has not renewed it. How do I extend my visa?",
      "I want to travel abroad for a job. What documents do I need for a work permit?"],
     ["ನನ್ನ ಕೆಲಸದ ವೀಸಾ ಮುಂದಿನ ತಿಂಗಳು ಮುಕ್ತಾಯಗೊಳ್ಳುತ್ತದೆ, ನನ್ನ ಕಂಪನಿ ಅದನ್ನು ನವೀಕರಿಸಿಲ್ಲ. ನನ್ನ ವೀಸಾವನ್ನು ಹೇಗೆ ವಿಸ್ತರಿಸುವುದು?",
      "ನಾನು ಕೆಲಸಕ್ಕಾಗಿ ವಿದೇಶಕ್ಕೆ ಪ್ರಯಾಣಿಸಲು ಬಯಸುತ್ತೇನೆ. ವರ್ಕ್ ಪರ್ಮಿಟ್‌ಗೆ ಯಾವ ದಾಖಲೆಗಳು ಬೇಕು?"],
     ["Nanna kelasa visa mundina tingalu muktayagolluttade, nanna company adannu navikarisilla. Nanna visavannu hege vistarisuvudu?",
      "Nanu kelasakkagi videshakke prayanisalu bayasuttene. Work permit ge yava dakhalegalu beku?"]),
    ("oos_school_admin", "school admission (non-maintenance)",
     ["The school near my house is not giving admission to my child. Where do I complain about school admissions?",
      "My child's school increased the fees suddenly. Is there a limit on how much a school can charge?"],
     ["ನನ್ನ ಮನೆಯ ಹತ್ತಿರದ ಶಾಲೆ ನನ್ನ ಮಗುವಿಗೆ ಪ್ರವೇಶ ನೀಡುತ್ತಿಲ್ಲ. ಶಾಲಾ ಪ್ರವೇಶದ ಬಗ್ಗೆ ಎಲ್ಲಿ ದೂರು ನೀಡುವುದು?",
      "ನನ್ನ ಮಗುವಿನ ಶಾಲೆ ಇದ್ದಕ್ಕಿದ್ದಂತೆ ಶುಲ್ಕ ಹೆಚ್ಚಿಸಿದೆ. ಶಾಲೆ ಎಷ್ಟು ವಿಧಿಸಬಹುದು ಎಂಬುದಕ್ಕೆ ಮಿತಿ ಇದೆಯೇ?"],
     ["Nanna maneya hattirada shale nanna maguvige pravesha needuttilla. Shala praveshada bagge elli duru needuvudu?",
      "Nanna maguvina shale iddakkidante shulka hechiside. Shale eshtu vidhisabahudu embudakke miti ideye?"]),
    ("oos_workplace", "workplace harassment (non-domestic)",
     ["My husband's boss shouts at him at work and has cut his pay. How can my husband complain about his boss?",
      "My wife's manager harasses her at the office and gives her extra work every day. Where does she complain about workplace harassment?"],
     ["ನನ್ನ ಗಂಡನ ಬಾಸ್ ಕೆಲಸದಲ್ಲಿ ಅವನ ಮೇಲೆ ಕೂಗಾಡುತ್ತಾನೆ ಮತ್ತು ಅವನ ಸಂಬಳ ಕಡಿತ ಮಾಡಿದ್ದಾನೆ. ನನ್ನ ಗಂಡ ತನ್ನ ಬಾಸ್ ಬಗ್ಗೆ ಹೇಗೆ ದೂರು ನೀಡಬಹುದು?",
      "ನನ್ನ ಹೆಂಡತಿಯ ಮ್ಯಾನೇಜರ್ ಕಚೇರಿಯಲ್ಲಿ ಅವಳನ್ನು ಕಿರುಕುಳ ಮಾಡುತ್ತಾನೆ ಮತ್ತು ಪ್ರತಿದಿನ ಹೆಚ್ಚುವರಿ ಕೆಲಸ ಕೊಡುತ್ತಾನೆ. ಕೆಲಸದ ಸ್ಥಳದ ಕಿರುಕುಳದ ಬಗ್ಗೆ ಅವಳು ಎಲ್ಲಿ ದೂರು ನೀಡಬೇಕು?"],
     ["Nanna gandana boss kelasadalli avana mele koogaduttane mattu avana sambala kadita madiddane. Nanna ganda tanna boss bagge hege duru needabahudu?",
      "Nanna hendatiya manager kacheriyalli avalannu kirukula maduttane mattu pratidina hechuvari kelasa koduttane. Kelasa sthalada kirukula bagge avalu elli duru needabeku?"]),
    ("oos_shop_sale", "business shop sale",
     ["I want to sell my shop to another businessman. What papers do I need to sell a shop?",
      "My business partner and I want to sell our shop together. How do we divide the sale money between us?"],
     ["ನಾನು ನನ್ನ ಅಂಗಡಿಯನ್ನು ಬೇರೊಬ್ಬ ವ್ಯಾಪಾರಿಗೆ ಮಾರಲು ಬಯಸುತ್ತೇನೆ. ಅಂಗಡಿ ಮಾರಲು ಯಾವ ಕಾಗದಗಳು ಬೇಕು?",
      "ನನ್ನ ವ್ಯಾಪಾರ ಪಾಲುದಾರ ಮತ್ತು ನಾನು ನಮ್ಮ ಅಂಗಡಿಯನ್ನು ಒಟ್ಟಿಗೆ ಮಾರಲು ಬಯಸುತ್ತೇವೆ. ಮಾರಾಟದ ಹಣವನ್ನು ನಮ್ಮ ನಡುವೆ ಹೇಗೆ ಹಂಚಿಕೊಳ್ಳುವುದು?"],
     ["Nanu nanna angadiyannu berobba vyaparige maralu bayasuttene. Angadi maralu yava kagadagalu beku?",
      "Nanna vyapara paludara mattu nanu namma angadiyannu ottige maralu bayasutteve. Maratada hanavannu namma naduve hege hanchikolluvudu?"]),
    ("oos_hospital_bill", "hospital bill dispute",
     ["The hospital charged me twice for the same treatment. How do I get the extra hospital bill amount back?",
      "My husband was admitted to a private hospital and they gave a very high bill. Can I dispute a hospital bill?"],
     ["ಆಸ್ಪತ್ರೆ ಅದೇ ಚಿಕಿತ್ಸೆಗೆ ಎರಡು ಬಾರಿ ಶುಲ್ಕ ವಿಧಿಸಿದೆ. ಹೆಚ್ಚುವರಿ ಆಸ್ಪತ್ರೆ ಬಿಲ್ ಮೊತ್ತವನ್ನು ಹೇಗೆ ವಾಪಸ್ ಪಡೆಯುವುದು?",
      "ನನ್ನ ಗಂಡ ಖಾಸಗಿ ಆಸ್ಪತ್ರೆಗೆ ದಾಖಲಾಗಿದ್ದನು, ಅವರು ತುಂಬಾ ಹೆಚ್ಚಿನ ಬಿಲ್ ಕೊಟ್ಟರು. ಆಸ್ಪತ್ರೆ ಬಿಲ್ ಬಗ್ಗೆ ವಿವಾದ ಮಾಡಬಹುದೇ?"],
     ["Aspatre ade chikitsege eradu bari shulka vidhiside. Hechuvari aspatre bill mottavannu hege vapas padeyuvudu?",
      "Nanna ganda khasagi aspatrege dakhalagiddanu, avaru tumba hechchina bill kottaru. Aspatre bill bagge vivada madabahude?"]),
    ("oos_dowry_punishment", "dowry punishment question (no Laya section)",
     ["My neighbour says that asking for money at the wedding will be held as dowry. What is the punishment for dowry under the law?",
      "Will giving gold at the wedding be treated as dowry? What happens if someone asks for dowry?"],
     ["ಮದುವೆಯಲ್ಲಿ ಹಣ ಕೇಳುವುದು ವರದಕ್ಷಿಣೆ ಎಂದು ಹೇಳುತ್ತಾರೆ ಎಂದು ನನ್ನ ನೆರೆಯವರು ಹೇಳುತ್ತಾರೆ. ಕಾನೂನಿನಲ್ಲಿ ವರದಕ್ಷಿಣೆಗೆ ಶಿಕ್ಷೆ ಏನು?",
      "ಮದುವೆಯಲ್ಲಿ ಚಿನ್ನ ಕೊಡುವುದು ವರದಕ್ಷಿಣೆ ಎಂದು ಪರಿಗಣಿಸಲಾಗುತ್ತದೆಯೇ? ಯಾರಾದರೂ ವರದಕ್ಷಿಣೆ ಕೇಳಿದರೆ ಏನಾಗುತ್ತದೆ?"],
     ["Maduveyalli hana keluvudu varadakshine anta heluttare anta nanna nereyavaru heluttare. Kanoonina alli varadakshinege shikshe enu?",
      "Maduveyalli chinna koduvudu varadakshine anta pariganisalaguttadeye? Yaradaru varadakshine kelidare enaguttade?"]),
    ("oos_business", "business partnership",
     ["My business partner took money from our company account without telling me. How do I settle a partnership dispute?",
      "I want to close my partnership firm. What is the process to dissolve a business partnership?"],
     ["ನನ್ನ ವ್ಯಾಪಾರ ಪಾಲುದಾರ ನನಗೆ ಹೇಳದೆ ನಮ್ಮ ಕಂಪನಿ ಖಾತೆಯಿಂದ ಹಣ ತೆಗೆದುಕೊಂಡನು. ಪಾಲುದಾರಿಕೆ ವಿವಾದವನ್ನು ಹೇಗೆ ಬಗೆಹರಿಸುವುದು?",
      "ನನ್ನ ಪಾಲುದಾರಿಕೆ ಸಂಸ್ಥೆಯನ್ನು ಮುಚ್ಚಲು ಬಯಸುತ್ತೇನೆ. ವ್ಯಾಪಾರ ಪಾಲುದಾರಿಕೆಯನ್ನು ವಿಸರ್ಜಿಸಲು ಪ್ರಕ್ರಿಯೆ ಏನು?"],
     ["Nanna vyapara paludara nanage helade namma company khateyinda hana tegedukondanu. Paludarike vivadavannu hege bageharisuvudu?",
      "Nanna paludarike samstheyannu mucchalu bayasuttene. Vyapara paludarikeyannu visarjisalu prakriye enu?"]),
]

for _bid, _domain, _en, _kn, _ro in OOS_DOMAINS:
    _reg(B(_bid, "hn_f", en=_en, kn=_kn, ro=_ro,
           issues={}, facts={"in_scope": "denied"},
           enums={"claimant_sex": "U", "claimant_role": "other"}))

# --- forum add-on (appended as a second sentence) --------------------------
FORUM_ADDON = {
    "en": ["Where should I file my case?",
           "Where do I file a case for this?"],
    "kn": ["ನಾನು ಎಲ್ಲಿ ಕೇಸ್ ಹಾಕಬೇಕು?",
           "ಇದಕ್ಕಾಗಿ ಎಲ್ಲಿ ಅರ್ಜಿ ಹಾಕಬೇಕು?"],
    "kn_roman": ["Nanu elli case hakabeku?",
                 "Idakkagi elli arji hakabeku?"],
}

# --- neutral framing (label-neutral; only multiplies surface variety) -----
# Prefixes/suffixes carry no new issue or fact: they are emotional/neutral
# openers and closers. Span offsets are shifted by the prefix length.
FRAMING = {
    "en": {
        "prefix": ["Please help me. ", "I need some advice. ",
                   "I am writing to ask for help. ",
                   "Please suggest what I should do. "],
        "suffix": [" I am very worried about this.",
                   " I feel lost about all of this.",
                   " This has been happening for a long time.",
                   " Please guide me on what to do next."],
    },
    "kn": {
        "prefix": ["ದಯವಿಟ್ಟು ನನಗೆ ಸಹಾಯ ಮಾಡಿ. ", "ನನಗೆ ಸ್ವಲ್ಪ ಸಲಹೆ ಬೇಕು. ",
                   "ಸಹಾಯ ಕೇಳಲು ಬರೆಯುತ್ತಿದ್ದೇನೆ. "],
        "suffix": [" ಇದರ ಬಗ್ಗೆ ನನಗೆ ತುಂಬಾ ಚಿಂತೆಯಾಗಿದೆ.",
                   " ಇದರ ಬಗ್ಗೆ ನನಗೆ ತುಂಬಾ ಗೊಂದಲವಿದೆ.",
                   " ಇದು ಬಹಳ ಸಮಯದಿಂದ ನಡೆಯುತ್ತಿದೆ."],
    },
    "kn_roman": {
        "prefix": ["Dayavittu nanage sahaya madi. ",
                   "Nanage swalpa salahe beku. ",
                   "Sahaya kelalu bareyuttiddene. "],
        "suffix": [" Idara bagge nanage tumba chinteyagide.",
                   " Idara bagge nanage tumba gondalavide.",
                   " Idu bahala samayadinda nadeyuttide."],
    },
}

# --- preset multi-issue combos (block ids) ---------------------------------
COMBOS = [
    ["divorce_want", "maint_wife"],
    ["divorce_want", "maint_wife", "custody_mother"],
    ["maint_wife", "custody_mother"],
    ["custody_mother", "maint_child_only"],
    ["residence_thrown_out", "violence_beats"],
    ["violence_beats", "maint_wife", "residence_thrown_out"],
    ["stridhan_held", "maint_wife"],
    ["stridhan_held", "residence_thrown_out"],
    ["stridhan_sold", "maint_wife"],
    ["divorce_want", "custody_mother"],
    ["divorce_pending", "maint_interim_pending"],
    ["divorce_decree_done", "maint_lump_sum"],
    ["joint_property_hma_pending", "maint_wife"],
    ["maint_arrears", "joint_property_no_hma"],
    ["birth_cert", "maint_child_only"],
    ["violence_dv_comp", "lockout"],
    ["violence_child_risk", "custody_mother"],
    ["maint_wife", "residence_live_in_house"],
    ["custody_father", "maint_wife"],
    ["stridhan_held", "custody_mother", "maint_wife"],
    ["residence_explicit_only", "maint_wife"],
    ["lockout", "maint_wife"],
    ["divorce_mutual", "maint_lump_sum"],
    ["neg_maintenance", "custody_mother"],
    ["maint_elder_parent", "procedure_court"],
    ["coloc_stay_with_child", "maint_wife"],
    ["coloc_custody_word", "maint_wife"],
    ["pre_bnss", "maint_arrears"],
    ["birth_cert_late", "maint_child_only"],
    ["dv_comp_medical", "maint_wife"],
    ["restitution_wife_left", "neg_divorce"],
    ["procedure_documents", "maint_wife"],
    ["child_risk_abduction", "violence_beats"],
    ["multi_ask_maint_stridhan", "custody_mother"],
    ["conflict_custody", "maint_wife"],
    ["mutual_agreed_terms", "maint_lump_sum"],
    ["being_filed_maintenance", "custody_mother"],
    ["stridhan_after_decree", "maint_post_decree"],
    ["bg_stridhan_mention", "maint_wife"],
    ["past_violence_stopped", "custody_mother"],
    ["joint_property", "maint_wife"],
    ["joint_property_no_hma", "custody_mother"],
    ["divorce_pending", "custody_mother"],
    ["maint_interim_pending", "stridhan_held"],
    ["residence_explicit_only", "custody_mother"],
    ["joint_property_hma_pending", "custody_mother"],
    ["divorce_decree_done", "stridhan_after_decree"],
    ["maint_child_self", "procedure_court"],
    ["maint_elder_parent", "maint_child_only"],
    ["joint_property", "divorce_pending"],
    ["joint_property", "being_filed_maintenance"],
]

CORE_SINGLE = ["maint_wife", "maint_child_only", "maint_lump_sum",
               "maint_interim_pending", "maint_post_decree", "custody_mother",
               "custody_father", "residence_thrown_out",
               "residence_live_in_house", "violence_beats", "violence_threats",
               "divorce_want", "divorce_mutual", "stridhan_held",
               "joint_property", "birth_cert", "procedure_court",
               "procedure_how_file", "maint_child_self",
               "birth_cert_late", "birth_cert_correction", "birth_cert_lost",
               "procedure_documents", "procedure_fees", "procedure_timeline",
               "child_risk_alcoholic", "child_risk_abduction",
               "child_risk_neglect", "mutual_agreed_terms",
               "multi_ask_maint_stridhan", "multi_ask_custody_maint",
               "narr_maint_separated", "narr_custody_separate",
               "maint_partial_fees", "divorce_settlement_terms",
               "joint_property_rights"]

# Allocation: (kind, count). Sums to N_TOTAL = 8000.
PLAN = [
    ("single", 2000),
    ("combo", 1900),
    ("hn_a", 350),
    ("hn_b", 450),
    ("hn_c", 550),
    ("hn_d", 450),
    ("hn_e", 400),
    ("hn_f", 900),
    ("neg", 350),
    ("conflict", 200),
    ("hn_g", 250),
    ("hn_h", 200),
]
assert sum(c for _, c in PLAN) == N_TOTAL

HN_BLOCKS = {
    "hn_a": ["coloc_stay_with_child", "coloc_custody_word"],
    "hn_b": ["residence_explicit_only", "lockout", "violence_dv_comp",
             "dv_comp_medical", "dv_comp_mental", "dv_comp_lost_wages",
             "residence_asked_to_leave"],
    "hn_c": ["divorce_pending", "divorce_being_filed", "divorce_js_only",
             "divorce_restitution", "divorce_decree_done",
             "js_only_living_apart", "being_filed_custody",
             "being_filed_maintenance", "mutual_refused",
             "restitution_wife_left", "restitution_desertion"],
    "hn_d": ["stridhan_sold", "stridhan_safe", "stridhan_never_asked",
             "joint_property_hma_pending", "joint_property_no_hma",
             "stridhan_after_decree", "stridhan_display"],
    "hn_e": ["maint_arrears", "maint_vary", "maint_elder_parent",
             "maint_male_self", "maint_father_child_only",
             "maint_enforcement_fear"],
    "hn_f": ["hypothetical", "third_party", "quoted", "pre_bnss",
             "past_event", "third_party_son"],
    "hn_f_oos": [b for b, _, _, _, _ in OOS_DOMAINS],
    "neg": ["neg_maintenance", "neg_divorce", "neg_custody",
            "neg_decree_mutual", "neg_no_order",
            "neg_residence", "neg_stridhan", "neg_joint", "neg_dvcomp",
            "neg_restitution", "neg_soft_divorce", "neg_soft_js"],
    "conflict": ["conflict_divorce", "conflict_custody",
                 "conflict_maintenance", "conflict_residence",
                 "conflict_stridhan"],
    "hn_g": ["bg_violence_past", "bg_stridhan_mention",
             "bg_residence_mention", "bg_joint_property", "bg_birth_cert"],
    "hn_h": ["hypo_custody", "hypo_stridhan", "quoted_maintenance",
             "quoted_residence", "past_violence_stopped", "past_threats"],
}

# ---------------------------------------------------------------- generation
SPAN_RE = re.compile(r"\[\[([A-Za-z_0-9]+):([^\]]+)\]\]")

_INTENT_RANK = {"uncertain": 0, "denied": 1, "incidental": 2, "requested": 3}
_MODALITY_RANK = {"present": 0, "past": 1, "future": 2,
                  "hypothetical": 3, "quoted": 4}


def _render_block(block, lang, rng):
    """Render one block template in `lang`; return (clean_text, spans)."""
    key = {"en": "en", "kn": "kn", "kn_roman": "ro"}[lang]
    template = rng.choice(block[key])
    slots = {k: rng.choice(v) for k, v in SLOTS[lang].items()}
    text = template.format(**slots)
    spans = []
    out = []
    pos = 0
    for m in SPAN_RE.finditer(text):
        out.append(text[pos:m.start()])
        start = sum(len(s) for s in out)
        phrase = m.group(2)
        out.append(phrase)
        spans.append({"key": m.group(1),
                      "kind": "fact" if m.group(1) in FACTS else "issue",
                      "text": phrase, "start": start,
                      "end": start + len(phrase)})
        pos = m.end()
    out.append(text[pos:])
    return "".join(out), spans


def _merge_issues(base, extra, warnings):
    for k, v in extra.items():
        if k not in base:
            base[k] = v
            continue
        old = base[k]
        if old == v:
            continue
        if {old, v} == {"requested", "denied"}:
            base[k] = "uncertain"
            warnings.append(f"issue-conflict:{k}")
        elif _INTENT_RANK[v] > _INTENT_RANK[old]:
            base[k] = v


def _merge_facts(base, extra, warnings):
    for k, v in extra.items():
        old = base.get(k, "unknown")
        if old == v:
            continue
        if old == "unknown":
            base[k] = v
        elif v == "unknown":
            continue
        else:
            base[k] = "conflicting"
            warnings.append(f"fact-conflict:{k}:{old}/{v}")


def _merge_enums(base, extra):
    for k, v in extra.items():
        if k == "modality_time":
            if _MODALITY_RANK[v] > _MODALITY_RANK[base.get(k, "present")]:
                base[k] = v
        elif base.get(k) in (None, "U", "other"):
            base[k] = v
        elif base.get(k) != v:
            pass  # keep primary block's sex/role on conflict


def build_record(block_ids, lang, rng):
    """Compose one record from 1+ blocks. Returns (record-dict, warnings)."""
    warnings = []
    issues = {i: "uncertain" for i in ISSUES}
    facts = {f: "unknown" for f in FACTS}  # every block must set in_scope
    enums = {"claimant_sex": "U", "claimant_role": "other",
             "modality_time": "present"}
    texts, spans = [], []
    for bid in block_ids:
        block = BLOCKS[bid]
        text, bspans = _render_block(block, lang, rng)
        offset = sum(len(t) + 1 for t in texts)  # +1 for the joining space
        for s in bspans:
            spans.append({"key": s["key"], "kind": s["kind"],
                          "text": s["text"], "start": s["start"] + offset,
                          "end": s["end"] + offset})
        texts.append(text)
        _merge_issues(issues, block["issues"], warnings)
        _merge_facts(facts, block["facts"], warnings)
        _merge_enums(enums, block["enums"])
    # Forum add-on: 25% of non-procedure, in-scope records ask which court.
    if rng.random() < 0.25 and issues.get("procedure") != "requested" \
            and facts["in_scope"] == "supported" \
            and "hypothetical" not in block_ids \
            and "quoted" not in block_ids:
        key = {"en": "en", "kn": "kn", "kn_roman": "kn_roman"}[lang]
        texts.append(rng.choice(FORUM_ADDON[key]))
        if issues["procedure"] == "uncertain":
            issues["procedure"] = "incidental"
    text = " ".join(texts)
    # Neutral framing: prefix shifts span offsets; suffix does not.
    if rng.random() < 0.45:
        prefix = rng.choice(FRAMING[lang]["prefix"])
        for s in spans:
            s["start"] += len(prefix)
            s["end"] += len(prefix)
        text = prefix + text
    if rng.random() < 0.35:
        text = text + rng.choice(FRAMING[lang]["suffix"])
    # OOS convention: every issue stays uncertain; facts stay unknown except
    # in_scope denied (already merged). Re-assert after merges.
    if facts["in_scope"] == "denied":
        issues = {i: "uncertain" for i in ISSUES}
    cluster = BLOCKS[block_ids[0]]["cluster"]
    if len(block_ids) > 1:
        cluster = "combo"
    if facts["in_scope"] == "unknown":
        raise ValueError(f"block(s) {block_ids} never set in_scope")
    rec = {"lang": lang, "text": text, "issues": issues, "facts": facts,
           "enums": enums, "spans": spans,
           "meta": {"cluster": cluster, "blocks": list(block_ids)}}
    return rec, warnings


def generate(seed=SEED, exclude_keys=frozenset()):
    rng = random.Random(seed)
    records = []
    seen = set()
    warn_counts = Counter()
    have = Counter()  # bucket -> records made so far (incremental; no rescan)
    lang_pick = (["en"] * 2 + ["kn", "kn_roman"])  # 50% EN, 25% KN, 25% roman
    attempts = 0
    while len(records) < N_TOTAL:
        attempts += 1
        if attempts > N_TOTAL * 100:
            raise RuntimeError("could not reach 5000 unique records")
        bucket = None
        for kind, count in PLAN:
            if have[kind] < count:
                bucket = kind
                break
        if bucket is None:
            break
        lang = rng.choice(lang_pick)
        if bucket == "single":
            bids = [rng.choice(CORE_SINGLE)]
        elif bucket == "combo":
            bids = list(rng.choice(COMBOS))
        elif bucket == "hn_f":
            # ~58% family-law hn_f (hypothetical / third-party / quoted /
            # pre-BNSS / past) vs ~42% OOS domains, so OOS is ~250/600.
            pool = (HN_BLOCKS["hn_f"] if rng.random() < 0.58
                    else HN_BLOCKS["hn_f_oos"])
            bids = [rng.choice(pool)]
        else:
            bids = [rng.choice(HN_BLOCKS[bucket])]
        rec, warns = build_record(bids, lang, rng)
        for w in warns:
            warn_counts[w] += 1
        key = (lang, rec["text"])
        if key in seen or key in exclude_keys:
            continue
        seen.add(key)
        records.append(rec)
        have[_bucket_of(rec)] += 1
    rng.shuffle(records)
    val = records[:N_VAL]
    train = records[N_VAL:]
    for i, r in enumerate(train, 1):
        r["id"] = f"SYN-TR-{i:04d}"
        r["meta"]["split"] = "train"
    for i, r in enumerate(val, 1):
        r["id"] = f"SYN-VA-{i:04d}"
        r["meta"]["split"] = "validation"
    # Reorder keys: id first.
    for r in train + val:
        r2 = {"id": r.pop("id")}
        r2.update(r)
        r.clear()
        r.update(r2)
    return train, val, warn_counts


def _bucket_of(rec):
    cluster = rec["meta"]["cluster"]
    if cluster == "combo":
        return "combo"
    if cluster == "core":
        return "single"
    return cluster


def validate(train, val):
    """Schema + span-offset self-check; raises on the first bad record."""
    seen_texts = set()
    for r in train + val:
        assert set(r["issues"]) == set(ISSUES), r["id"]
        assert set(r["facts"]) == set(FACTS), r["id"]
        assert all(v in INTENTS for v in r["issues"].values()), r["id"]
        assert all(v in FACT_STATES for v in r["facts"].values()), r["id"]
        assert r["enums"]["claimant_sex"] in ("F", "M", "U"), r["id"]
        assert r["enums"]["claimant_role"] in (
            "spouse", "parent", "child", "other"), r["id"]
        assert r["enums"]["modality_time"] in (
            "present", "past", "future", "hypothetical", "quoted"), r["id"]
        assert r["lang"] in ("en", "kn", "kn_roman"), r["id"]
        for s in r["spans"]:
            assert r["text"][s["start"]:s["end"]] == s["text"], (r["id"], s)
            assert s["kind"] in ("fact", "issue"), r["id"]
        key = (r["lang"], r["text"])
        assert key not in seen_texts, ("duplicate text", r["id"])
        seen_texts.add(key)


def manifest(train, val, frozen_sha=None, frozen_at=None, frozen_note=None):
    allr = train + val
    return {
        "name": "synthetic_v7_1",
        "seed": SEED,
        "n_total": len(allr),
        "n_train": len(train),
        "n_validation": len(val),
        "frozen_validation_sha256": frozen_sha,
        "frozen_validation_at": frozen_at,
        "frozen_validation_note": frozen_note,
        "method": "statutory-grammar paraphrase templates + hard-negative "
                  "perturbations; never from test banks. v7.1 recall-swarm "
                  "expansion (Lane 02, 2026-11-27): 5,000 -> 8,000 records; "
                  "new thin-cluster blocks (conflict, birth_certificate, "
                  "procedure, dv_compensation, restitution, child_safety, "
                  "being_filed, judicial_separation), incidental-mention "
                  "traps (hn_g), modality traps (hn_h), 3 new OOS domains, "
                  "Kaanoon-informed lay phrasing patterns (own wording "
                  "only, no Kaanoon text copied); Lane 05 kn_templates "
                  "wired in when present",
        "languages": dict(Counter(r["lang"] for r in allr)),
        "clusters": dict(Counter(r["meta"]["cluster"] for r in allr)),
        "issues_requested": {
            i: sum(1 for r in allr if r["issues"][i] == "requested")
            for i in ISSUES},
        "issues_denied": {
            i: sum(1 for r in allr if r["issues"][i] == "denied")
            for i in ISSUES},
        "facts_supported": {
            f: sum(1 for r in allr if r["facts"][f] == "supported")
            for f in FACTS},
        "facts_denied": {
            f: sum(1 for r in allr if r["facts"][f] == "denied")
            for f in FACTS},
        "facts_conflicting": {
            f: sum(1 for r in allr if r["facts"][f] == "conflicting")
            for f in FACTS},
        "enums_sex": dict(Counter(r["enums"]["claimant_sex"] for r in allr)),
        "enums_role": dict(Counter(r["enums"]["claimant_role"] for r in allr)),
        "enums_modality": dict(Counter(r["enums"]["modality_time"]
                                       for r in allr)),
        "mean_words_en": round(sum(len(r["text"].split()) for r in allr
                                   if r["lang"] == "en") /
                               max(1, sum(1 for r in allr
                                          if r["lang"] == "en")), 2),
        "schema": {"issues": ISSUES, "facts": FACTS,
                   "intents": list(INTENTS), "fact_states": list(FACT_STATES)},
    }


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", default="data/synthetic_v7_1",
                    help="output directory")
    ap.add_argument("--seed", type=int, default=SEED)
    ap.add_argument("--new-split", action="store_true",
                    help="explicitly allow regenerating validation.jsonl "
                         "(coordinator-ordered new split version only; "
                         "without it, an existing validation.jsonl is "
                         "FROZEN and never overwritten)")
    args = ap.parse_args(argv)
    # Recall-swarm R4: wire Lane 05 KN/Kanglish templates when present.
    # kn_templates.py lives beside this file (scripts/); it only mutates
    # this module's in-memory registries (BLOCKS / CORE_SINGLE /
    # HN_BLOCKS / COMBOS) and never writes data files. If it is absent,
    # the corpus builds without it (note printed, deterministic either way
    # for a fixed builder + kn_templates pair).
    try:
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        import kn_templates
        kn_templates.validate()
        kn_templates.wire_into_builder(sys.modules[__name__])
        print("wired Lane 05 kn_templates:",
              kn_templates.counts()["variants"])
    except ImportError:
        print("Lane 05 kn_templates not present; building without it")
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    # FREEZE (coordinator, 2026-11-27): once validation.jsonl exists on
    # disk it is FROZEN — a rebuild regenerates train.jsonl only and never
    # rewrites validation.jsonl. Any further expansion goes to train only
    # (or to a new versioned split file, e.g. validation-v2.jsonl, with
    # its own manifest entry — use --new-split only when the coordinator
    # explicitly orders a new split version).
    frozen_val = None
    frozen_sha = frozen_at = frozen_note = None
    val_path = out / "validation.jsonl"
    man_path = out / "manifest.json"
    if val_path.exists() and not args.new_split:
        frozen_val = [json.loads(line) for line in
                      val_path.read_text(encoding="utf-8").splitlines()
                      if line.strip()]
        frozen_sha = hashlib.sha256(val_path.read_bytes()).hexdigest()
        if man_path.exists():
            old_man = json.loads(man_path.read_text(encoding="utf-8"))
            old_sha = old_man.get("frozen_validation_sha256")
            if old_sha is not None and old_sha != frozen_sha:
                raise SystemExit(
                    f"FROZEN validation.jsonl hash mismatch: manifest "
                    f"records {old_sha} but file hashes {frozen_sha}; "
                    f"refusing to build (the frozen file must not change)")
            frozen_at = old_man.get("frozen_validation_at")
            frozen_note = old_man.get("frozen_validation_note")
        if frozen_at is None:
            frozen_at = datetime.now(timezone.utc).isoformat()
        if frozen_note is None:
            frozen_note = (
                "Frozen 2026-11-27 (recall swarm, coordinator freeze): "
                "validation.jsonl is the frozen split; all "
                "validation-split numbers are measured against this exact "
                "file; further expansion goes to train.jsonl only.")
        print(f"FROZEN validation.jsonl kept as-is "
              f"(sha256 {frozen_sha[:12]}…, {len(frozen_val)} records); "
              f"regenerating train.jsonl only")
    if frozen_val is not None:
        train, gen_val, warns = generate(seed=args.seed)
        if [(r["id"], r["lang"], r["text"]) for r in gen_val] == \
                [(r["id"], r["lang"], r["text"]) for r in frozen_val]:
            # Builder unchanged since the freeze: generated split is
            # identical, so train is byte-identical too. Keep both.
            val = frozen_val
        else:
            # Builder changed since the freeze: regenerate train
            # excluding every frozen validation (lang, text), so no
            # train record can duplicate or 8-gram-collide with the
            # frozen split through the shared template pool.
            exclude = {(r["lang"], r["text"]) for r in frozen_val}
            train, _gen_val2, warns = generate(
                seed=args.seed, exclude_keys=exclude)
            val = frozen_val
            print("builder changed since freeze: train regenerated "
                  "excluding frozen validation texts; validation "
                  "untouched")
    else:
        if args.new_split and val_path.exists():
            print("WARNING: --new-split: regenerating FROZEN "
                  "validation.jsonl (coordinator-ordered only)")
        train, val, warns = generate(seed=args.seed)
    validate(train, val)
    with open(out / "train.jsonl", "w", encoding="utf-8") as fh:
        for r in train:
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")
    if frozen_val is None:
        with open(out / "validation.jsonl", "w", encoding="utf-8") as fh:
            for r in val:
                fh.write(json.dumps(r, ensure_ascii=False) + "\n")
        frozen_sha = hashlib.sha256(val_path.read_bytes()).hexdigest()
    man = manifest(train, val, frozen_sha=frozen_sha,
                   frozen_at=frozen_at, frozen_note=frozen_note)
    man["merge_warnings"] = dict(warns)
    with open(out / "manifest.json", "w", encoding="utf-8") as fh:
        json.dump(man, fh, ensure_ascii=False, indent=1)
    with open(out / "schema.json", "w", encoding="utf-8") as fh:
        json.dump({"issues": ISSUES, "facts": FACTS,
                   "intents": list(INTENTS), "fact_states": list(FACT_STATES),
                   "enums": {
                       "claimant_sex": ["F", "M", "U"],
                       "claimant_role": ["spouse", "parent", "child", "other"],
                       "modality_time": ["present", "past", "future",
                                         "hypothetical", "quoted"]},
                   "span": {"key": "fact-or-issue name",
                            "kind": "fact | issue",
                            "text": "surface phrase",
                            "start": "char offset", "end": "char offset"}},
                  fh, ensure_ascii=False, indent=1)
    print(f"wrote {len(train)} train + {len(val)} validation "
          f"-> {out} (seed={args.seed})")
    print("languages:", man["languages"])
    print("clusters:", man["clusters"])
    print("merge warnings:", dict(warns) or "none")
    return 0


if __name__ == "__main__":
    sys.exit(main())
