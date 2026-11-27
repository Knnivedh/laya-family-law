#!/usr/bin/env python3
"""LAYA v7.1 recall swarm — Lane 05: Kannada / Kanglish paraphrase templates.

NEW blocks for the synthetic corpus builder (``scripts/build_synthetic_corpus.py``,
Lane 02's file — this file is NEVER imported by the builder on its own; Lane 02
wires it in with :func:`wire_into_builder`). Same block shape as the builder's
``B()`` helper: ``{id, cluster, en, kn, ro, issues, facts, enums}`` with
``[[key:phrase]]`` span markup and ``{slot}`` placeholders (slots are the
builder's ``SLOTS`` for each language).

Why these blocks exist (user target 2026-11-27 ~19:19 IST: unseen questions
>= 70% exact; Sealed Kannada-8 is 4/8 = 50%): the KN / Kanglish split is the
thinnest part of the corpus. Validation-split counts (``data/synthetic_v7_1/
validation.jsonl``, 500 records; KN-family = kn 153 + kn_roman 119 = 272):

    issue requested (kn + kn_roman): restitution 5, birth_certificate 7,
    dv_compensation 6, procedure 8, joint_property 13, stridhan 18,
    violence 17, divorce 22, custody 39, residence 46, maintenance 134.

    fact supported (kn + kn_roman): child_safety_risk 2, being_filed 4,
    interim_asked 5, lump_sum_settlement 6, judicial_separation_only 6,
    mutual_consent 6, dv_injury_comp_asked 6, stridhan_sold_or_mortgaged 6,
    demand_made 14, existing_order_enforcement 16.

These 25 blocks target exactly those thin issues/facts, in Kannada script
AND Roman Kanglish, including:

* colloquial / spoken forms (ದುಡ್ಡು ಕೊಡಲ್ಲ, ಮನೆಯಿಂದ ಆಚೆ ಹಾಕಿದ್ದಾರೆ,
  ಬಂಗಾರ ಇಟ್ಕೊಂಡಿದ್ದಾರೆ, ಹೊಡೆಯುತ್ತಾನೆ — plan §3.2 axes),
* common Roman spelling variants (jeevanamsha / jeevanamsa / jeevanaamsha /
  jivanaamsha, vichhedana / vichchhedana, paalane / palane, stridhan /
  streedhan, maintanance),
* code-mixed forms ("maintenance beku", "divorce beku", "custody beku",
  "residence beku", "stridhan vapas beku", "lump sum beku", "interim
  maintenance beku", "birth certificate beku").

Every sentence was written fresh from the statutory concepts (BNSS s.144 /
s.144(3) / s.146, HMA ss.9/13/13B/24/25/26/27, PWDVA ss.17/18/19/20/22,
GWA 1890, HMGA s.6, BNS s.316, Births & Deaths Act 1969). NEVER from test
banks: no sealed, ground-truth or fixture question text was read, copied or
paraphrased here. Leakage is verified afterwards by
``scripts/check_ngram_leakage.py`` (Lane 02 re-runs the gate after wiring).

Kannada wording caveat: these templates are plain, everyday Kannada written
for the corpus; they have NOT had a native-speaker audit yet — P2.1 must
audit them before any training run treats the KN split as gold (same caveat
as the builder's own KN templates).

Wiring (Lane 02): ``from kn_templates import wire_into_builder`` then
``wire_into_builder(build_synthetic_corpus)`` — registers the blocks,
extends ``CORE_SINGLE`` / ``HN_BLOCKS`` / ``COMBOS``. Nothing in this file
edits the builder or the data files.
"""
from __future__ import annotations

import re

__all__ = ["KN_EXTRA_BLOCKS", "WIRING", "KN_COMBOS", "wire_into_builder"]

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
CLUSTERS = ("core", "combo", "hn_a", "hn_b", "hn_c", "hn_d", "hn_e",
            "hn_f", "neg", "conflict")
# Slot names the builder provides per language (SLOTS in the builder).
SLOT_NAMES = ("child_age", "child_word", "amount", "duration", "gold_value")
SPAN_RE = re.compile(r"\[\[([A-Za-z_0-9]+):([^\]]+)\]\]")
SLOT_RE = re.compile(r"\{([A-Za-z_0-9]+)\}")

F = "F"
M = "M"
SPOUSE = {"claimant_sex": F, "claimant_role": "spouse"}
SPOUSE_M = {"claimant_sex": M, "claimant_role": "spouse"}


def B(bid, cluster, en, kn, ro, issues=None, facts=None, enums=None):
    """Same shape as the builder's B() helper (see its docstring)."""
    return {"id": bid, "cluster": cluster, "en": en, "kn": kn, "ro": ro,
            "issues": issues or {}, "facts": facts or {},
            "enums": enums or {}}


# --------------------------------------------------------------------------
# Core: maintenance / custody / residence / stridhan — colloquial KN + Kanglish
# --------------------------------------------------------------------------
KN_EXTRA_BLOCKS = [
    B("kn_maint_duddu", "core",
      en=["My husband gives me no money at all for the house. I need [[maintenance:maintenance]].",
          "My husband pays nothing towards running the house. I need money to live on."],
      kn=["ನನ್ನ ಗಂಡ ಮನೆಗೆ ದುಡ್ಡು ಕೊಡಲ್ಲ. ನನಗೆ [[maintenance:ಜೀವನಾಂಶ]] ಬೇಕು.",
          "ನನ್ನ ಗಂಡ ಹಣ ಕೊಡುತ್ತಿಲ್ಲ, ನನಗೆ ಮನೆ ನಡೆಸಲು ದುಡ್ಡು ಬೇಕು.",
          "ಗಂಡ ಮನೆಗೆ ದುಡ್ಡು ಕೊಡುವುದನ್ನು ನಿಲ್ಲಿಸಿದ್ದಾನೆ, ನನಗೆ ಜೀವನಾಂಶ ಬೇಕು."],
      ro=["Nanna ganda manege duddu kodalla. Nanage [[maintenance:jeevanamsa]] beku.",
          "Nanna ganda hana koduttilla, nanage [[maintenance:maintenance]] beku.",
          "Ganda manege duddu koduvudannu nillisidanu, nanage jeevanamsha beku."],
      issues={"maintenance": "requested"},
      facts={"money_fact": "supported", "in_scope": "supported"},
      enums=dict(SPOUSE)),
    B("kn_maint_spelling", "core",
      en=["My husband gives me no money. I need [[maintenance:maintenance]] from him.",
          "I need [[maintenance:maintenance]] from my husband; he pays nothing for the house."],
      kn=["ನನ್ನ ಗಂಡ ಹಣ ಕೊಡುತ್ತಿಲ್ಲ. ನನಗೆ [[maintenance:ಜೀವನಾಂಶ]] ಬೇಕು.",
          "ಗಂಡನಿಂದ [[maintenance:ಜೀವನಾಂಶ]] ಬೇಕು, ಮನೆ ನಡೆಸಲು ಹಣವಿಲ್ಲ."],
      ro=["Nanage [[maintenance:jeevanamsa]] beku, ganda hana koduttilla.",
          "Nanage [[maintenance:jeevanaamsha]] beku.",
          "Nanage [[maintenance:jivanaamsha]] beku, [[maintenance:maintenance]] beku.",
          "Nanage [[maintenance:maintanance]] beku, ganda duddu kodalla."],
      issues={"maintenance": "requested"},
      facts={"money_fact": "supported", "in_scope": "supported"},
      enums=dict(SPOUSE)),
    B("kn_custody_colloq", "core",
      en=["I want [[custody:custody]] of my {child_age}-year-old {child_word}; my {child_word} should stay with me.",
          "My {child_word} must remain with me. I am asking for [[custody:custody]]."],
      kn=["ನನ್ನ {child_age} ವರ್ಷದ {child_word}ನ [[custody:ಪಾಲನೆ]] ನನಗೆ ಬೇಕು, {child_word} ನನ್ನ ಜೊತೆ ಇರಬೇಕು.",
          "ನನ್ನ {child_word} ನನ್ನ ಬಳಿಯೇ ಇರಬೇಕು, [[custody:ಪಾಲನೆ]] ನನಗೆ ಕೊಡಿ.",
          "{child_word} ನನ್ನ ಜೊತೆ ಇರಬೇಕು, ಪಾಲನೆ ನನಗೆ ಬೇಕು."],
      ro=["Nanna {child_age} varshada {child_word}na [[custody:paalane]] nanage beku, {child_word} nanna jothe irabeku.",
          "Nanna {child_word} nanna bali irabeku, [[custody:custody]] beku.",
          "{child_word}na [[custody:palane]] nanage beku."],
      issues={"custody": "requested"},
      facts={"custody_claim": "supported", "child_fact": "supported",
             "minor_child": "supported", "in_scope": "supported"},
      enums=dict(SPOUSE)),
    B("kn_residence_colloq", "core",
      en=["My husband has thrown me out of the house. I want to stay in my home.",
          "I want to keep living in our house; I will not leave it."],
      kn=["ನನ್ನ ಗಂಡ ನನ್ನನ್ನು ಮನೆಯಿಂದ ಆಚೆ ಹಾಕಿದ್ದಾರೆ, ಮನೆಯಲ್ಲೇ ಇರಬೇಕು.",
          "ನಾನು ನಮ್ಮ ಮನೆಯಲ್ಲೇ ಇರಲು ಬಯಸುತ್ತೇನೆ, ಮನೆ ಬಿಟ್ಟು ಹೋಗುವುದಿಲ್ಲ.",
          "ನನ್ನನ್ನು ಮನೆಯಿಂದ ಹೊರಹಾಕಿದ್ದಾರೆ, ನನಗೆ ಮನೆಯಲ್ಲೇ ಇರಲು ಹಕ್ಕು ಬೇಕು."],
      ro=["Nanna ganda nannannu maneyinda horahakidare, maneyalle irabeku.",
          "Nanu namma maneyalle iralu bayasuttene, mane bittu hoguvudilla.",
          "Nanage [[residence:residence]] beku, maneyalli irabeku."],
      issues={"residence": "requested"},
      facts={"residence_claim": "supported",
             "coercive_eviction_or_lockout": "supported",
             "in_scope": "supported"},
      enums=dict(SPOUSE)),
    B("kn_stridhan_colloq", "core",
      en=["My in-laws are keeping my gold. I want it back.",
          "My in-laws hold on to the gold from my wedding and refuse to hand it over."],
      kn=["ನನ್ನ ಬಂಗಾರವನ್ನು ಅತ್ತೆ-ಮಾವ ಇಟ್ಕೊಂಡಿದ್ದಾರೆ, ವಾಪಸ್ ಬೇಕು.",
          "ನನ್ನ ಮದುವೆಯ ಚಿನ್ನ ನನ್ನ ಗಂಡನ ಮನೆಯಲ್ಲಿದೆ, ವಾಪಸ್ ಕೊಡುತ್ತಿಲ್ಲ.",
          "ನನ್ನ [[stridhan_claim:ಚಿನ್ನ]]ವನ್ನು ಅತ್ತೆ-ಮಾವ ಇಟ್ಟುಕೊಂಡಿದ್ದಾರೆ, ಅದನ್ನು ವಾಪಸ್ ಕೊಡಬೇಕು."],
      ro=["Nanna bangaravannu atte-mava itkondiddare, vapas beku.",
          "Nanna maduveya chinna nanna gandana maneyallide, vapas koduttilla.",
          "Nanna [[stridhan_claim:streedhan]] vapas beku."],
      issues={"stridhan": "requested"},
      facts={"stridhan_claim": "supported", "demand_made": "supported",
             "in_scope": "supported"},
      enums=dict(SPOUSE)),
    B("kn_maint_child_fees", "core",
      en=["I need money only for my {child_age}-year-old {child_word}'s [[school_fees_fact:school fees]].",
          "I want [[maintenance:maintenance]] only for my {child_word}'s education, nothing for myself."],
      kn=["ನನ್ನ {child_age} ವರ್ಷದ {child_word}ನ [[school_fees_fact:ಶಾಲಾ ಶುಲ್ಕ]]ಕ್ಕಾಗಿ ಮಾತ್ರ ಹಣ ಬೇಕು.",
          "{child_word}ನ ಓದಿಗಾಗಿ [[maintenance:ಜೀವನಾಂಶ]] ಬೇಕು, ನನಗಾಗಿ ಬೇಡ."],
      ro=["Nanna {child_age} varshada {child_word}na [[school_fees_fact:school fees]] kkagi matra hana beku.",
          "{child_word}na odigagi [[maintenance:jeevanamsha]] beku, nanagagi beda.",
          "Nanna {child_word}na [[school_fees_fact:shala shulka]] kkagi hana beku."],
      issues={"maintenance": "requested"},
      facts={"money_fact": "supported", "child_maintenance_only": "supported",
             "child_fact": "supported", "minor_child": "supported",
             "school_fees_fact": "supported", "in_scope": "supported"},
      enums=dict(SPOUSE)),

    # ------------------------------------------------------------------
    # hn_b: violence / dv compensation / lockout — colloquial KN + Kanglish
    # ------------------------------------------------------------------
    B("kn_dv_comp_colloq", "hn_b",
      en=["My husband beat me so badly I had to go to hospital. I want [[dv_compensation:compensation for my injuries]].",
          "I want [[dv_compensation:compensation]] for the medical costs of the beating."],
      kn=["ನನ್ನ ಗಂಡ ಹೊಡೆದು ಆಸ್ಪತ್ರೆಗೆ ಹೋಗಬೇಕಾಯಿತು, ಗಾಯಗಳಿಗೆ [[dv_compensation:ಪರಿಹಾರ]] ಬೇಕು.",
          "ಹೊಡೆತದಿಂದ ಆದ ಖರ್ಚಿಗಾಗಿ [[dv_compensation:ಪರಿಹಾರ]] ಬೇಕು."],
      ro=["Nanna ganda hodedu aspatrege hogabekayitu, gayagalige [[dv_compensation:parihara]] beku.",
          "Hodetinda ada kharchigagi [[dv_compensation:compensation]] beku."],
      issues={"violence": "requested", "dv_compensation": "requested"},
      facts={"violence": "supported", "dv_injury_comp_asked": "supported",
             "in_scope": "supported"},
      enums=dict(SPOUSE)),
    B("kn_violence_colloq", "hn_b",
      en=["My husband beats me every day and I am afraid.",
          "My husband threatens me; there is [[violence:violence]] at home."],
      kn=["ನನ್ನ ಗಂಡ ಪ್ರತಿದಿನ ನನ್ನನ್ನು ಹೊಡೆಯುತ್ತಾನೆ, ನನಗೆ ಭಯವಾಗಿದೆ.",
          "ನನ್ನ ಗಂಡ ಬೆದರಿಸುತ್ತಾನೆ, ಮನೆಯಲ್ಲಿ [[violence:ಹಿಂಸೆ]] ನಡೆಯುತ್ತಿದೆ."],
      ro=["Nanna ganda pratidina nannannu hodeyuttane, nanage bhayavagide.",
          "Nanna ganda bedarisuttane, maneyalli [[violence:himse]] nadeyuttide.",
          "Ganda hodita, nanage rakshane beku."],
      issues={"violence": "requested"},
      facts={"violence": "supported", "in_scope": "supported"},
      enums=dict(SPOUSE)),
    B("kn_lockout_colloq", "hn_b",
      en=["My husband locked the door and would not let me in.",
          "When I went home the door was shut and I could not get in."],
      kn=["ನನ್ನ ಗಂಡ ಬಾಗಿಲು ಬೀಗ ಹಾಕಿ ನನ್ನನ್ನು ಒಳಗೆ ಬಿಡಲಿಲ್ಲ.",
          "ಮನೆಗೆ ಹೋದಾಗ ಬಾಗಿಲು ಮುಚ್ಚಿತ್ತು, ಒಳಗೆ ಹೋಗಲು ಸಾಧ್ಯವಾಗಲಿಲ್ಲ."],
      ro=["Nanna ganda bagilu beega haki nannannu olage bidalilla.",
          "Manege hodaga bagilu mucchittu, olage hogalu sadhyavagilla."],
      issues={"residence": "requested"},
      facts={"residence_claim": "supported",
             "coercive_eviction_or_lockout": "supported",
             "in_scope": "supported"},
      enums=dict(SPOUSE)),

    # ------------------------------------------------------------------
    # hn_c: divorce / restitution / mutual consent / judicial separation /
    # being filed — colloquial KN + Kanglish
    # ------------------------------------------------------------------
    B("kn_restitution_colloq", "hn_c",
      en=["My husband should come back home and live with me.",
          "I do not want a [[divorce:divorce]]; I want my husband to return."],
      kn=["ನನ್ನ ಗಂಡ ಮನೆಗೆ ಮರಳಿ ಬರಬೇಕು, ನನ್ನ ಜೊತೆ ಬದುಕಬೇಕು.",
          "ನನಗೆ [[divorce:ವಿಚ್ಛೇದನ]] ಬೇಡ, ಗಂಡ ವಾಪಸ್ ಬರಬೇಕು."],
      ro=["Nanna ganda manege marali barabeku, nanna jothe badukabeku.",
          "Nanage [[divorce:divorce]] beda, ganda vapas barabeku.",
          "Ganda marali banni, nanna jothe iri."],
      issues={"restitution": "requested", "divorce": "denied"},
      facts={"restitution_asked": "supported", "divorce_asked": "denied",
             "in_scope": "supported"},
      enums=dict(SPOUSE)),
    B("kn_divorce_mutual_colloq", "hn_c",
      en=["We both agree to end the marriage by [[mutual_consent:mutual consent]].",
          "My husband and I have both agreed to a [[mutual_consent:mutual consent divorce]]."],
      kn=["ನಾವಿಬ್ಬರೂ ಒಪ್ಪಿದ್ದೇವೆ, [[mutual_consent:ಪರಸ್ಪರ ಒಪ್ಪಿಗೆ]]ಯಿಂದ [[divorce:ವಿಚ್ಛೇದನ]] ಬೇಕು.",
          "ಗಂಡ-ಹೆಂಡತಿ ಇಬ್ಬರೂ ಸೇರಿ [[divorce:ವಿಚ್ಛೇದನ]]ಕ್ಕೆ ಒಪ್ಪಿದ್ದೇವೆ."],
      ro=["Navibbaru oppideve, [[mutual_consent:paraspara oppige]]yinda [[divorce:vichhedana]] beku.",
          "Ganda-hendati ibbaru seri [[divorce:divorce]] ge oppideve.",
          "[[mutual_consent:Mutual consent divorce]] beku, ibbaru oppideve."],
      issues={"divorce": "requested"},
      facts={"divorce_asked": "supported", "mutual_consent": "supported",
             "in_scope": "supported"},
      enums=dict(SPOUSE)),
    B("kn_divorce_js_colloq", "hn_c",
      en=["I want [[judicial_separation_only:judicial separation]] only, not a [[divorce:divorce]].",
          "I want to live apart from my husband with a court order, but not end the marriage."],
      kn=["ನನಗೆ [[judicial_separation_only:ನ್ಯಾಯಾಂಗ ಬೇರ್ಪಡಿಕೆ]] ಮಾತ್ರ ಬೇಕು, [[divorce:ವಿಚ್ಛೇದನ]] ಬೇಡ.",
          "ಗಂಡನಿಂದ ಬೇರೆಯಾಗಿ ವಾಸಿಸಲು ಬಯಸುತ್ತೇನೆ, ಮದುವೆ ಮುಗಿಸಲು ಬೇಡ."],
      ro=["Nanage [[judicial_separation_only:nyayanga berpadike]] matra beku, [[divorce:vichhedana]] beda.",
          "Gandana inda bereyagi vaasisalu bayasuttene, maduve mugisalu beda.",
          "[[judicial_separation_only:Judicial separation]] matra beku, [[divorce:divorce]] beda."],
      issues={"divorce": "denied"},
      facts={"judicial_separation_only": "supported",
             "divorce_asked": "denied", "in_scope": "supported"},
      enums=dict(SPOUSE)),
    B("kn_divorce_filing_colloq", "hn_c",
      en=["I am [[being_filed:filing for divorce]] next week.",
          "I have met a lawyer to file my divorce case."],
      kn=["ನಾನು ಮುಂದಿನ ವಾರ [[being_filed:ವಿಚ್ಛೇದನಕ್ಕೆ ಅರ್ಜಿ ಹಾಕುತ್ತಿದ್ದೇನೆ]].",
          "[[being_filed:ವಿಚ್ಛೇದನ ಕೇಸ್ ಹಾಕಲು]] ವಕೀಲರನ್ನು ಭೇಟಿ ಮಾಡಿದ್ದೇನೆ."],
      ro=["Nanu mundina vara [[being_filed:vichhedanakke arji hakuttiddene]].",
          "[[being_filed:Divorce case hakalu]] vakilarannu bheti madiddene.",
          "Nanu [[being_filed:divorce filing]] maduttene, next week case hakuttene."],
      issues={"divorce": "requested"},
      facts={"being_filed": "supported", "divorce_asked": "supported",
             "in_scope": "supported"},
      enums={"claimant_sex": F, "claimant_role": "spouse",
             "modality_time": "future"}),

    # ------------------------------------------------------------------
    # hn_d: stridhan sold / demand never made / demand made / joint property
    # ------------------------------------------------------------------
    B("kn_stridhan_sold_colloq", "hn_d",
      en=["My husband [[stridhan_sold_or_mortgaged:sold my gold]] without asking me. I want it back.",
          "My in-laws pawned my wedding gold; I want its value back."],
      kn=["ನನ್ನ ಗಂಡ ನನ್ನ [[stridhan_claim:ಚಿನ್ನ]]ವನ್ನು [[stridhan_sold_or_mortgaged:ಮಾರಿಬಿಟ್ಟನು]], ವಾಪಸ್ ಬೇಕು.",
          "ನನ್ನ ಬಂಗಾರವನ್ನು [[stridhan_sold_or_mortgaged:ಅಡವಿಟ್ಟಿದ್ದಾರೆ]], ಅದರ ಹಣ ಬೇಕು."],
      ro=["Nanna ganda nanna [[stridhan_claim:chinna]]vannu [[stridhan_sold_or_mortgaged:maribittanu]], vapas beku.",
          "Nanna bangaravannu [[stridhan_sold_or_mortgaged:adavittiddare]], adara hana beku.",
          "Atte-mava nanna chinna [[stridhan_sold_or_mortgaged:maridare]]."],
      issues={"stridhan": "requested"},
      facts={"stridhan_claim": "supported",
             "stridhan_sold_or_mortgaged": "supported",
             "demand_made": "supported", "in_scope": "supported"},
      enums=dict(SPOUSE)),
    B("kn_stridhan_never_asked_colloq", "hn_d",
      en=["I have [[demand_made:never asked]] for my gold back. Can I ask for it now?",
          "My gold is still with them, but I have never demanded it."],
      kn=["ನಾನು ಚಿನ್ನ ವಾಪಸ್ [[demand_made:ಕೇಳಿಯೇ ಇಲ್ಲ]], ಈಗ ಕೇಳಬಹುದೇ?",
          "ನನ್ನ ಚಿನ್ನ ಅವರ ಬಳಿಯೇ ಇದೆ, ನಾನು [[demand_made:ಎಂದೂ ಕೇಳಿಲ್ಲ]]."],
      ro=["Nanu chinna vapas [[demand_made:keliye illa]], ega kelabahude?",
          "Nanna chinna avara baliye ide, nanu [[demand_made:yavattu kelilla]].",
          "Nanu chinna [[demand_made:kelalilla]], ega kelabahude?"],
      issues={"stridhan": "requested"},
      facts={"stridhan_claim": "supported", "demand_made": "denied",
             "in_scope": "supported"},
      enums=dict(SPOUSE)),
    B("kn_stridhan_demand_made_colloq", "hn_d",
      en=["I have asked for my gold and they refuse to give it back.",
          "I have demanded my [[stridhan_claim:stridhan]] several times and they will not return it."],
      kn=["ನಾನು ಚಿನ್ನ [[demand_made:ಕೇಳಿದ್ದೇನೆ]], ಅವರು ಕೊಡಲು ನಿರಾಕರಿಸಿದ್ದಾರೆ.",
          "ಹಲವು ಬಾರಿ [[demand_made:ಬೇಡಿಕೆ ಇಟ್ಟಿದ್ದೇನೆ]], ಚಿನ್ನ ವಾಪಸ್ ಕೊಡುತ್ತಿಲ್ಲ."],
      ro=["Nanu chinna [[demand_made:kelidde]], avaru kodalu nirakarisiddare.",
          "Halavu bari [[demand_made:bedike ittiddene]], chinna vapas koduttilla."],
      issues={"stridhan": "requested"},
      facts={"stridhan_claim": "supported", "demand_made": "supported",
             "in_scope": "supported"},
      enums=dict(SPOUSE)),
    B("kn_joint_prop_colloq", "hn_d",
      en=["I want my share of the house we bought in both our names.",
          "Give me my share of our [[joint_property_claim:joint property]]."],
      kn=["ನಾವಿಬ್ಬರ ಹೆಸರಿನಲ್ಲಿ ಖರೀದಿಸಿದ ಮನೆಯಲ್ಲಿ ನನ್ನ ಪಾಲು ಬೇಕು.",
          "ನಮ್ಮ [[joint_property_claim:ಜಂಟಿ ಆಸ್ತಿ]]ಯಲ್ಲಿ ನನ್ನ ಪಾಲು ಕೊಡಿ."],
      ro=["Navibbara hesarinalli khareedisa maneyalli nanna palu beku.",
          "Namma [[joint_property_claim:janti asti]]yalli nanna palu kodi.",
          "[[joint_property_claim:Joint property]] palu beku, ibbaru hesaru ide."],
      issues={"joint_property": "requested"},
      facts={"joint_property_claim": "supported", "in_scope": "supported"},
      enums=dict(SPOUSE)),

    # ------------------------------------------------------------------
    # hn_e: maintenance arrears / interim / lump sum — colloquial KN + Kanglish
    # ------------------------------------------------------------------
    B("kn_maint_arrears_colloq", "hn_e",
      en=["The court ordered [[maintenance:maintenance]] but my husband has not paid the arrears.",
          "He has not paid [[maintenance:maintenance]] for three months; I want the unpaid amount."],
      kn=["ಕೋರ್ಟ್ ಆದೇಶಿಸಿದರೂ ನನ್ನ ಗಂಡ ಬಾಕಿ [[maintenance:ಜೀವನಾಂಶ]] ಕೊಟ್ಟಿಲ್ಲ.",
          "ಮೂರು ತಿಂಗಳಿಂದ [[maintenance:ಜೀವನಾಂಶ]] ಕೊಟ್ಟಿಲ್ಲ, ಬಾಕಿ ಹಣ ಬೇಕು."],
      ro=["Court adeshisidaru nanna ganda baki [[maintenance:jeevanamsha]] kottilla.",
          "Mooru tingalinda [[maintenance:jeevanamsha]] kottilla, baki hana beku."],
      issues={"maintenance": "requested"},
      facts={"money_fact": "supported",
             "existing_order_enforcement": "supported",
             "in_scope": "supported"},
      enums=dict(SPOUSE)),
    B("kn_maint_interim_colloq", "hn_e",
      en=["While the divorce case is going on, I need [[interim_asked:interim maintenance]].",
          "I need [[maintenance:maintenance]] for now, until the case ends."],
      kn=["ವಿಚ್ಛೇದನ ಕೇಸ್ ನಡೆಯುವಾಗ ಈಗ [[interim_asked:ಜೀವನಾಂಶ]] ಬೇಕು.",
          "ಕೇಸ್ ಮುಗಿಯುವವರೆಗೆ [[interim_asked:ಮಧ್ಯಂತರ ಜೀವನಾಂಶ]] ಬೇಕು."],
      ro=["Divorce case nadeyuvaga ega [[interim_asked:jeevanamsha]] beku.",
          "Case mugiyuvarage [[interim_asked:madhyantara jeevanamsha]] beku.",
          "[[interim_asked:Interim maintenance]] beku, case nadeyuttide."],
      issues={"maintenance": "requested", "divorce": "incidental"},
      facts={"money_fact": "supported", "interim_asked": "supported",
             "proceeding_pending_hma": "supported", "in_scope": "supported"},
      enums=dict(SPOUSE)),
    B("kn_maint_lumpsum_colloq", "hn_e",
      en=["I want a [[lump_sum_settlement:lump sum]] instead of monthly [[maintenance:maintenance]].",
          "Give me one lump sum payment, not monthly support."],
      kn=["ತಿಂಗಳ [[maintenance:ಜೀವನಾಂಶ]] ಬದಲು [[lump_sum_settlement:ಒಟ್ಟು ಹಣ]] ಬೇಕು.",
          "[[lump_sum_settlement:ಒಂದೇ ಬಾರಿಗೆ ಒಟ್ಟು ಹಣ]] ಕೊಡಿ, ತಿಂಗಳು ತಿಂಗಳು ಬೇಡ."],
      ro=["Tingala [[maintenance:jeevanamsha]] badalu [[lump_sum_settlement:ottu hana]] beku.",
          "[[lump_sum_settlement:Onde barige ottu hana]] kodi, tingalu tingalu beda.",
          "[[lump_sum_settlement:Lump sum]] beku, monthly beda."],
      issues={"maintenance": "requested"},
      facts={"money_fact": "supported", "lump_sum_settlement": "supported",
             "in_scope": "supported"},
      enums=dict(SPOUSE)),

    # ------------------------------------------------------------------
    # core: birth certificate / procedure — colloquial KN + Kanglish
    # ------------------------------------------------------------------
    B("kn_birth_cert_colloq", "core",
      en=["I need my {child_age}-year-old {child_word}'s [[birth_certificate:birth certificate]] for school admission.",
          "My {child_word} was born at home and has no [[birth_certificate:birth certificate]]. How do I get one?"],
      kn=["ನನ್ನ {child_age} ವರ್ಷದ {child_word}ನ [[birth_certificate:ಜನನ ಪ್ರಮಾಣಪತ್ರ]] ಬೇಕು, ಶಾಲೆಗೆ ಸೇರಿಸಲು.",
          "{child_word} ಮನೆಯಲ್ಲಿ ಹುಟ್ಟಿದ್ದರಿಂದ [[birth_certificate:ಜನನ ಪ್ರಮಾಣಪತ್ರ]] ಇಲ್ಲ, ಹೇಗೆ ಪಡೆಯುವುದು?"],
      ro=["Nanna {child_age} varshada {child_word}na [[birth_certificate:janana pramanapatra]] beku, shalege serisalu.",
          "{child_word} maneyalli huttiddarinda [[birth_certificate:janana pramanapatra]] illa, hege padeyuvudu?",
          "[[birth_certificate:Birth certificate]] beku, maguvina shalege."],
      issues={"birth_certificate": "requested"},
      facts={"birth_cert_asked": "supported", "child_fact": "supported",
             "minor_child": "supported", "in_scope": "supported"},
      enums=dict(SPOUSE)),
    B("kn_procedure_colloq", "core",
      en=["Which court should I go to for [[procedure:maintenance]]?",
          "How do I file a case, and which papers do I need?"],
      kn=["[[procedure:ಜೀವನಾಂಶ]]ಕ್ಕಾಗಿ ಯಾವ ಕೋರ್ಟ್‌ಗೆ ಹೋಗಬೇಕು?",
          "ಕೇಸ್ ಹೇಗೆ ಹಾಕುವುದು, ಯಾವ ಕಾಗದಗಳು ಬೇಕು?"],
      ro=["[[procedure:Jeevanamsha]]kkagi yava court ge hogabeku?",
          "Case hege hakuvudu, yava kagadagalu beku?",
          "Court ge hege hoguvudu, procedure enu?"],
      issues={"procedure": "requested"},
      facts={"in_scope": "supported"},
      enums=dict(SPOUSE)),

    # ------------------------------------------------------------------
    # hn_a: custody vs residence co-location (KN colloquial)
    # ------------------------------------------------------------------
    B("kn_coloc_home_child_colloq", "hn_a",
      en=["I want my {child_age}-year-old {child_word} to keep living at home with me; this is about staying in the house.",
          "My {child_word} and I want to keep staying in our house together."],
      kn=["ನನ್ನ {child_age} ವರ್ಷದ {child_word} ಮನೆಯಲ್ಲಿ ನನ್ನ ಜೊತೆಯೇ ಇರಬೇಕು, ಇದು ಮನೆಯಲ್ಲಿ ಇರುವ ಬಗ್ಗೆ.",
          "ನನ್ನ {child_word} ಮತ್ತು ನಾನು ನಮ್ಮ ಮನೆಯಲ್ಲೇ ಇರಲು ಬಯಸುತ್ತೇವೆ."],
      ro=["Nanna {child_age} varshada {child_word} maneyalli nanna joteye irabeku, idu maneyalli iruva bagge.",
          "Nanna {child_word} mattu nanu namma maneyalle iralu bayasutteve."],
      issues={"residence": "requested", "custody": "incidental"},
      facts={"residence_claim": "supported", "custody_claim": "denied",
             "child_fact": "supported", "minor_child": "supported",
             "in_scope": "supported"},
      enums=dict(SPOUSE)),

    # ------------------------------------------------------------------
    # neg: maintenance denied, custody only (KN colloquial)
    # ------------------------------------------------------------------
    B("kn_neg_maint_colloq", "neg",
      en=["I do not want [[maintenance:maintenance]]; I only want [[custody:custody]] of my {child_word}.",
          "I am not asking for money, only that my {child_word} stays with me."],
      kn=["ನನಗೆ [[maintenance:ಜೀವನಾಂಶ]] ಬೇಡ, {child_word}ನ [[custody:ಪಾಲನೆ]] ಮಾತ್ರ ಬೇಕು.",
          "ನಾನು ಹಣ ಕೇಳುತ್ತಿಲ್ಲ, {child_word} ನನ್ನ ಬಳಿ ಇರಬೇಕು ಅಷ್ಟೇ."],
      ro=["Nanage [[maintenance:jeevanamsha]] beda, {child_word}na [[custody:paalane]] matra beku.",
          "Nanu hana keluttilla, {child_word} nanna bali irabeku ashte.",
          "[[maintenance:Maintenance]] beda, [[custody:custody]] matra beku."],
      issues={"maintenance": "denied", "custody": "requested"},
      facts={"money_fact": "denied", "custody_claim": "supported",
             "child_fact": "supported", "minor_child": "supported",
             "in_scope": "supported"},
      enums=dict(SPOUSE)),

    # ------------------------------------------------------------------
    # core: child safety risk (KN colloquial)
    # ------------------------------------------------------------------
    B("kn_child_safety_colloq", "core",
      en=["My husband beats our {child_word} too; my {child_word} is not safe at home.",
          "My {child_word} is in danger at home and needs protection."],
      kn=["ನನ್ನ ಗಂಡ ನಮ್ಮ {child_word}ನನ್ನೂ ಹೊಡೆಯುತ್ತಾನೆ, {child_word} ಸುರಕ್ಷಿತವಾಗಿಲ್ಲ.",
          "ಮನೆಯಲ್ಲಿ ನನ್ನ {child_word}ಗೆ ಅಪಾಯವಿದೆ, ರಕ್ಷಣೆ ಬೇಕು."],
      ro=["Nanna ganda namma {child_word}nannu hodeyuttane, {child_word} surakshitavagilla.",
          "Maneyalli nanna {child_word}ge apayavide, rakshane beku.",
          "Ganda {child_word}nannu hodita, magu safe alla."],
      issues={"violence": "requested"},
      facts={"violence": "supported", "child_safety_risk": "supported",
             "child_fact": "supported", "minor_child": "supported",
             "in_scope": "supported"},
      enums=dict(SPOUSE)),
]

# Pool wiring for Lane 02 (mirrors the builder's CORE_SINGLE / HN_BLOCKS /
# COMBOS). ``wire_into_builder`` applies it; the simulation in the lane
# status file used exactly this wiring.
WIRING = {
    "CORE_SINGLE": [
        "kn_maint_duddu", "kn_maint_spelling", "kn_custody_colloq",
        "kn_residence_colloq", "kn_stridhan_colloq", "kn_maint_child_fees",
        "kn_birth_cert_colloq", "kn_procedure_colloq",
        "kn_child_safety_colloq",
    ],
    "hn_a": ["kn_coloc_home_child_colloq"],
    "hn_b": ["kn_dv_comp_colloq", "kn_violence_colloq", "kn_lockout_colloq"],
    "hn_c": ["kn_restitution_colloq", "kn_divorce_mutual_colloq",
             "kn_divorce_js_colloq", "kn_divorce_filing_colloq"],
    "hn_d": ["kn_stridhan_sold_colloq", "kn_stridhan_never_asked_colloq",
             "kn_stridhan_demand_made_colloq", "kn_joint_prop_colloq"],
    "hn_e": ["kn_maint_arrears_colloq", "kn_maint_interim_colloq",
             "kn_maint_lumpsum_colloq"],
    "neg": ["kn_neg_maint_colloq"],
}

KN_COMBOS = [
    ["kn_maint_duddu", "kn_custody_colloq"],
    ["kn_residence_colloq", "kn_violence_colloq"],
    ["kn_stridhan_colloq", "kn_maint_duddu"],
    ["kn_restitution_colloq", "kn_maint_duddu"],
]


def wire_into_builder(builder):
    """Register these blocks in a loaded ``build_synthetic_corpus`` module.

    Lane 02 calls this before ``generate()``. It only mutates the builder's
    in-memory registries (``BLOCKS``, ``CORE_SINGLE``, ``HN_BLOCKS``,
    ``COMBOS``); it never writes data files.
    """
    for b in KN_EXTRA_BLOCKS:
        builder._reg(b)
    for pool, ids in WIRING.items():
        if pool == "CORE_SINGLE":
            builder.CORE_SINGLE.extend(ids)
        else:
            builder.HN_BLOCKS[pool].extend(ids)
    builder.COMBOS.extend(KN_COMBOS)


def counts():
    """Template-variant counts per language + per-issue block counts.

    Returns {"variants": {"en": n, "kn": n, "kn_roman": n},
    "blocks_per_issue_requested": {...}, "blocks_per_issue_denied": {...},
    "blocks_per_fact_supported": {...}}. Used by the lane status file.
    """
    variants = {"en": 0, "kn": 0, "kn_roman": 0}
    req, den, fac = {}, {}, {}
    for b in KN_EXTRA_BLOCKS:
        variants["en"] += len(b["en"])
        variants["kn"] += len(b["kn"])
        variants["kn_roman"] += len(b["ro"])
        for issue, intent in b["issues"].items():
            if intent == "requested":
                req[issue] = req.get(issue, 0) + 1
            elif intent == "denied":
                den[issue] = den.get(issue, 0) + 1
        for fact, state in b["facts"].items():
            if state == "supported":
                fac[fact] = fac.get(fact, 0) + 1
    return {"variants": variants,
            "blocks_per_issue_requested": dict(sorted(req.items())),
            "blocks_per_issue_denied": dict(sorted(den.items())),
            "blocks_per_fact_supported": dict(sorted(fac.items()))}


def validate():
    """Schema self-check: same rules the builder's validate() enforces.

    Raises on the first bad block. Does NOT import the builder (keeps this
    file importable standalone); ids are required to start with ``kn_`` so
    they can never collide with the builder's existing block ids.
    """
    seen = set()
    for b in KN_EXTRA_BLOCKS:
        assert b["id"].startswith("kn_"), b["id"]
        assert b["id"] not in seen, ("duplicate block id", b["id"])
        seen.add(b["id"])
        assert b["cluster"] in CLUSTERS, (b["id"], b["cluster"])
        for lang_key in ("en", "kn", "ro"):
            assert isinstance(b[lang_key], list) and b[lang_key], \
                (b["id"], lang_key)
            for t in b[lang_key]:
                assert isinstance(t, str) and t.strip(), (b["id"], t)
                for m in SPAN_RE.finditer(t):
                    assert m.group(1) in ISSUES or m.group(1) in FACTS, \
                        (b["id"], m.group(1))
                for m in SLOT_RE.finditer(t):
                    assert m.group(1) in SLOT_NAMES, (b["id"], m.group(1))
        for issue, intent in b["issues"].items():
            assert issue in ISSUES, (b["id"], issue)
            assert intent in INTENTS, (b["id"], intent)
        for fact, state in b["facts"].items():
            assert fact in FACTS, (b["id"], fact)
            assert state in FACT_STATES, (b["id"], state)
        for k, v in b["enums"].items():
            assert k in ("claimant_sex", "claimant_role", "modality_time"), \
                (b["id"], k)
            assert v in ("F", "M", "U", "spouse", "parent", "child", "other",
                         "present", "past", "future", "hypothetical",
                         "quoted"), (b["id"], k, v)
        assert b["facts"].get("in_scope") in ("supported", "denied"), \
            (b["id"], "in_scope must be set")
    for pool, ids in WIRING.items():
        assert pool in ("CORE_SINGLE", "hn_a", "hn_b", "hn_c", "hn_d",
                        "hn_e", "neg"), pool
        for bid in ids:
            assert bid in seen, ("wiring references unknown block", bid)
    wired = {bid for ids in WIRING.values() for bid in ids}
    assert wired == seen, ("unwired blocks", sorted(seen - wired))
    for combo in KN_COMBOS:
        assert len(combo) >= 2, combo
        for bid in combo:
            assert bid in seen, ("combo references unknown block", bid)
    return True


def _self_test():
    validate()
    c = counts()
    assert len(KN_EXTRA_BLOCKS) == 25, len(KN_EXTRA_BLOCKS)
    print(f"kn_templates self-test PASS: {len(KN_EXTRA_BLOCKS)} blocks, "
          f"variants en={c['variants']['en']} kn={c['variants']['kn']} "
          f"kn_roman={c['variants']['kn_roman']}")
    print("  blocks per issue (requested):",
          c["blocks_per_issue_requested"])
    print("  blocks per fact (supported):",
          c["blocks_per_fact_supported"])


if __name__ == "__main__":
    _self_test()
