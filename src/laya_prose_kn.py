"""Deterministic Template-Locked Kannada Prose Renderer + Kannada Fp=0 Verifier.

LANE 09 — LAYA v7.1 / 10x plan V71-P6-1 (Kannada templates) and V71-P6-2
(readability / action-plan / document-checklist DESIGN — see "P6-2 DESIGN"
below). Pure Python, zero model calls, zero runtime machine translation,
zero question-text input. Fp = 0 by construction, same as ``laya_prose_v2``.

================================================================================
DRAFT STATUS — READ FIRST — DRAFT STATUS — READ FIRST — DRAFT STATUS
================================================================================
EVERY Kannada template in this module is marked DRAFT — NEEDS P2.1 native
Kannada speaker verification (human step) before it can be claimed correct.
No Kannada wording in this file is verified. ``render_prose_kn`` prepends
``DRAFT_NOTICE_KN`` to every output while ``include_draft_banner=True``
(the default) and every render result carries ``"draft": True`` and
``"p2_1_verified": False``. The banner may be removed ONLY after a signed
P2.1 report is filed (see ``scripts/export_human_audit.py``, P2.1 packet).
Do NOT present any Kannada wording from this module as verified, and do NOT
strip the draft banner in any integration (Lane 01 wiring) before P2.1.
================================================================================

Coverage (20 sections — the 18 English sections + bnss-144-3 + bnss-146):
  bnss-144, bnss-144-3, bnss-146, pwdva-20, hma-24, hma-25, gwa-1890,
  hmga-1956-s6, welfare-principle, hma-26, hma-27, bns-316, pwdva-17,
  pwdva-18, pwdva-19, pwdva-22, hma-13, hma-13b, hma-9,
  births-deaths-act-1969.
All 9 escalation kinds (quantum, court, demand, recovery, custody,
residence, safety, procedure, fact) + safety emergency helplines
(112 / 181 / 1098), INTRO_LINE_KN, CLOSING_LINE_KN, OUT_OF_SCOPE_LINE_KN,
INVALID_RECORD_HANDOFF_KN.

Rules the templates obey (checked by ``prose_forbidden_check_kn`` and the
self-test in ``run_self_test``):
  * 0 question-mark characters anywhere in rendered prose (Forbidden #5).
    The renderer never asks the user to pick a court.
  * No invented rupee amounts (Forbidden #8): no digits with rupee /
    monthly context ever appear in a template.
  * No salary-slip / pay-slip wording, not even in a "missing" clause
    (Forbidden #9): the literal strings are traps for the checker, so the
    checklist says "give whatever records you have; if a record is missing,
    say that it is missing" WITHOUT naming salary slips.
  * HMA s.27 / BNS s.316 are cited ONLY when in kept_ids (D1-A / D2 rule,
    same as the English renderer). HMA s.13 needs divorce_asked or a pending
    proceeding; HMA s.13B needs divorce_asked AND mutual_consent.
  * Statute numbers are rendered only from kept_ids; the checker verifies
    Kannada statutory-pattern parity against kept_ids (Forbidden #7).

API:
  render_prose_kn(rec, facts=None, *, include_draft_banner=True,
                  include_forum_note=False, include_checklist=False)
      -> {"prose", "prose_render_ms", "prose_template_version",
          "unknown_ids", "status", "draft", "p2_1_verified", "lang": "kn"}
  render_prose_localized(rec, facts=None, target_lang="auto")
      -> routes rec["lang"] in {"kn", "kn_roman"} (or target_lang="kn")
         to render_prose_kn; otherwise delegates to the English
         ``laya_prose_v2.render_prose`` (lazy import, no circularity).
  prose_forbidden_check_kn(prose, kept_ids, dropped_ids, facts)
      -> (fp_hits, quality_flags), Kannada parity of the 9 frozen items.
  document_checklist_kn(kept_ids, facts) -> deterministic per-section
      document checklist string (template-locked, Fp=0 checked).
  forum_guidance_kn(kept_ids) -> Bengaluru / metro forum note (opt-in).
  readability_check_kn(prose) -> sentence-length audit for P6-2.

================================================================================
P6-2 DESIGN — Layman Readability, Forum Nuance, Document Checklists (SPEC)
================================================================================
This section is the V71-P6-2 DESIGN SPEC. The Kannada checklist is
IMPLEMENTED here (``document_checklist_kn``); the English checklist is NOT
implemented in this file — it goes through Lane 01's ``laya_prose_v2.py``
via the patch spec in ``docs/10x_swarm_state/lane-09-p6.md`` (Lane 09 must
not edit Lane 01's files).

1. Safety banner (implemented in this module, ``SAFETY_BANNER_KN``):
   When "safety" is in escalation_kinds, the safety banner is the FIRST
   paragraph of the output (before INTRO_LINE_KN): emergency numbers
   112 (police/emergency), 181 (women helpline), 1098 (childline) +
   Protection Officer / One Stop Centre note. Safety fires BEFORE and
   INDEPENDENTLY of kept_ids, claimant_sex, domestic relationship,
   proceeding_pending_hma, demand_made, or clarification holds (Pillar 4,
   V71-P4-3). Non-violent residence-only requests must NOT over-fire it —
   the banner is driven by the escalation kind, never by prose guessing.

2. Court & local forum guidance (``forum_guidance_kn``, opt-in):
   Deterministic forum only (Family Court / Magistrate / Registrar).
   When bnss-144 fires, the optional note reads: where a Family Court is
   established, BNSS s.144 claims are filed in the Family Court under
   FCA s.7(2)(a); otherwise before a Judicial Magistrate First Class.
   This resolves the F1/F2/KN1 confusion WITHOUT asking the user to choose
   a court (Forbidden #5) and WITHOUT breaking the deterministic forum.
   The note is opt-in (``include_forum_note``) so Lane 01 integration can
   decide when it ships; it is template-locked and Fp=0 checked either way.

3. Document & evidence checklist (``document_checklist_kn``):
   Strictly template-locked per kept section, Fp=0 checked:
   - bnss-144 / pwdva-20 / hma-24 / hma-25: marriage proof; income
     information the user already knows; child school-fee records ONLY if
     school_fees_fact is True.
   - bnss-144-3: existing order + list of unpaid instalments and due dates.
   - bnss-146: existing order + proof of changed circumstances.
   - custody (gwa-1890 / hmga-1956-s6 / welfare-principle / hma-26):
     child birth record, school records.
   - hma-27 / bns-316: Stridhan list, photos, copy of the written demand.
   - pwdva-17 / pwdva-19: proof of living in the shared household.
   - pwdva-18 / pwdva-22: medical records, police complaint, message
     records (BSA s.63 electronic proof is named ONLY as "message records"
     in user text; the statute cross-walk lives in the legal registry).
   - hma-13 / hma-13b / hma-9: marriage proof.
   - births-deaths-act-1969: hospital record or other proof of birth.
   Closing line (every checklist): "Give whatever records you have. If a
   record is missing, say that it is missing." Salary slips / pay slips
   are NEVER named in user-facing prose (see the Forbidden #9 trap above).

4. Readability audit (``readability_check_kn``; EN rules apply to both):
   Average sentence length <= 22 words; zero Latin / legalese jargon in
   user text (pendente lite, in specie, mutatis mutandis, and their
   equivalents never appear); plain step ordering — What applies ->
   Which court -> Next steps & documents -> Missing facts -> Disclaimer.
   Kannada sentences are split on "." / "।" and words on whitespace.
   The self-test asserts avg <= 22 words and 0 "?" on every rendered
   template combination.

5. EN checklist patch spec (Lane 01 applies it — full text in the
   Lane 09 status file): add ``action_plan`` / ``document_checklist``
   to ``laya_prose_v2.py`` behind the same template-lock + Fp=0 check,
   with the safety banner first, the FCA s.7(2)(a) forum note, and the
   "provide whatever records you have" closing line. No salary-slip
   naming anywhere in rendered prose.
================================================================================
"""

from __future__ import annotations

import re
import time
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

TEMPLATE_VERSION = "v2.1-kn-draft-p2.1-pending"

# Every template in this module carries this status. Do not change it to
# anything else until a signed P2.1 native-speaker report says so.
DRAFT_STATUS = "DRAFT — NEEDS P2.1 native Kannada speaker verification"

KNOWN_SECTIONS_KN = frozenset({
    "bnss-144", "bnss-144-3", "bnss-146", "pwdva-20", "hma-24", "hma-25",
    "gwa-1890", "hmga-1956-s6", "welfare-principle", "hma-26",
    "hma-27", "bns-316",
    "pwdva-17", "pwdva-18", "pwdva-19", "pwdva-22",
    "hma-13", "hma-13b", "hma-9",
    "births-deaths-act-1969",
})

KNOWN_ESCALATION_KINDS_KN = frozenset({
    "quantum", "court", "demand", "recovery", "custody",
    "residence", "safety", "procedure", "fact",
})

# --- Act names (single source of truth; the checker reuses these) ----------
ACT_BNSS_KN = "ಭಾರತೀಯ ನಾಗರಿಕ ಸುರಕ್ಷಾ ಸಂಹಿತೆ, 2023"
ACT_PWDVA_KN = "ಕೌಟುಂಬಿಕ ದೌರ್ಜನ್ಯ ತಡೆ ಕಾಯ್ದೆ, 2005"
ACT_HMA_KN = "ಹಿಂದೂ ವಿವಾಹ ಕಾಯ್ದೆ, 1955"
ACT_BNS_KN = "ಭಾರತೀಯ ನ್ಯಾಯ ಸಂಹಿತೆ, 2023"
ACT_HMGA_KN = "ಹಿಂದೂ ಅಪ್ರಾಪ್ತ ಮತ್ತು ಪಾಲನಾ ಕಾಯ್ದೆ, 1956"
ACT_GWA_KN = "ಗಾರ್ಡಿಯನ್ಸ್ ಮತ್ತು ವಾರ್ಡ್ಸ್ ಕಾಯ್ದೆ, 1890"
ACT_BIRTHS_KN = "ಜನನ ಮತ್ತು ಮರಣಗಳ ನೋಂದಣಿ ಕಾಯ್ದೆ, 1969"
ACT_FCA_KN = "ಕುಟುಂಬ ನ್ಯಾಯಾಲಯಗಳ ಕಾಯ್ದೆ"

# --- Fixed lines (all DRAFT — NEEDS P2.1 verification) ----------------------
DRAFT_NOTICE_KN = (
    "ಕರಡು ಅನುವಾದ. ಸ್ಥಳೀಯ ಕನ್ನಡ ಪರಿಶೀಲನೆ ಇನ್ನೂ ಬಾಕಿ ಇದೆ. "
    "ಈ ಪದಗಳು ಸರಿಯಾಗಿವೆ ಎಂದು ಇನ್ನೂ ದೃಢಪಟ್ಟಿಲ್ಲ."
)

INTRO_LINE_KN = (
    "ನೀವು ಹೇಳಿರುವುದರ ಆಧಾರದ ಮೇಲೆ, ನಿಮ್ಮ ಪ್ರಶ್ನೆಗೆ ಈ ಕೆಳಗಿನವು ಅನ್ವಯಿಸುತ್ತವೆ. "
    "ಇದು ಸಾಮಾನ್ಯ ಮಾಹಿತಿ ಮಾತ್ರ. ಇದು ಕಾನೂನು ಸಲಹೆ ಅಲ್ಲ. "
    "ನಿಮ್ಮ ಪೂರ್ಣ ವಿವರಗಳನ್ನು ನೋಡಿದ ನಂತರವೇ ವಕೀಲರು ಅಥವಾ ನ್ಯಾಯಾಲಯ ನಿರ್ಧಾರ ತೆಗೆದುಕೊಳ್ಳುತ್ತಾರೆ."
)

CLOSING_LINE_KN = (
    "ಈ ಉತ್ತರವು ನಿಮ್ಮ ಪ್ರಶ್ನೆಗೆ ಗುರುತಿಸಲಾದ ಸೆಕ್ಷನ್ ಗಳ ಆಧಾರದ ಮೇಲೆ ನೀಡಲಾದ ಸಾಮಾನ್ಯ ಮಾಹಿತಿ ಮಾತ್ರ. "
    "ಇದು ನಿಮ್ಮ ಪೂರ್ಣ ಪರಿಸ್ಥಿತಿಗೆ ಕಾನೂನು ಸಲಹೆ ಅಲ್ಲ."
)

OUT_OF_SCOPE_LINE_KN = (
    "ಈ ಪ್ರಶ್ನೆಯು ಈ ವ್ಯವಸ್ಥೆಯು ಒಳಗೊಳ್ಳುವ ಕೌಟುಂಬಿಕ ಕಾನೂನು ವಿಷಯಗಳ ವ್ಯಾಪ್ತಿಯ ಹೊರಗಿದೆ. "
    "ಇದು ನಿಮ್ಮ ಹಕ್ಕುಗಳ ಬಗ್ಗೆ ಏನನ್ನೂ ಹೇಳುವುದಿಲ್ಲ. "
    "ಮಾನವ ಸಲಹೆಗಾರರು ಇದನ್ನು ನೋಡಬೇಕಾಗುತ್ತದೆ."
)

INVALID_RECORD_HANDOFF_KN = (
    "ಈ ವ್ಯವಸ್ಥೆಯು ಸ್ವಯಂಚಾಲಿತ ವರ್ಗೀಕರಣ ದಾಖಲೆಯನ್ನು ಸರಿಯಾಗಿ ಪರಿಶೀಲಿಸಲು ಸಾಧ್ಯವಾಗಲಿಲ್ಲ. "
    "ಆದ್ದರಿಂದ ಇಲ್ಲಿ ಯಾವುದೇ ಕಾನೂನು ಸೆಕ್ಷನ್ ಅಥವಾ ನ್ಯಾಯಾಲಯದ ವಿವರಗಳನ್ನು ನೀಡಲಾಗಿಲ್ಲ. "
    "ದಯವಿಟ್ಟು ನಿಮ್ಮ ಪ್ರಶ್ನೆಯನ್ನು ಮಾನವ ಸಲಹೆಗಾರರು ಅಥವಾ ವಕೀಲರು ಪರಿಶೀಲಿಸಲಿ."
)

SAFETY_BANNER_KN = (
    "ತುರ್ತು ಸಹಾಯ ಬೇಕಾದರೆ ತಕ್ಷಣ ಕರೆ ಮಾಡಿ. ಪೊಲೀಸ್ ಮತ್ತು ತುರ್ತು ಸಹಾಯ 112. "
    "ಮಹಿಳಾ ಸಹಾಯವಾಣಿ 181. ಮಕ್ಕಳ ಸಹಾಯವಾಣಿ 1098. "
    "ರಕ್ಷಣಾ ಅಧಿಕಾರಿ ಅಥವಾ ಒನ್ ಸ್ಟಾಪ್ ಸೆಂಟರ್ ಸಹ ಸಹಾಯ ಮಾಡುತ್ತಾರೆ."
)

FORUM_NOTE_BNSS144_KN = (
    "ಕುಟುಂಬ ನ್ಯಾಯಾಲಯ ಇರುವ ಕಡೆ, ಬಿಎನ್ಎಸ್ಎಸ್ ಸೆಕ್ಷನ್ 144 ರ ಅರ್ಜಿಯನ್ನು "
    "ಕುಟುಂಬ ನ್ಯಾಯಾಲಯಗಳ ಕಾಯ್ದೆಯ ಸೆಕ್ಷನ್ 7(2)(a) ರ ಅಡಿಯಲ್ಲಿ ಕುಟುಂಬ ನ್ಯಾಯಾಲಯದಲ್ಲಿ ಸಲ್ಲಿಸಲಾಗುತ್ತದೆ. "
    "ಇಲ್ಲದಿದ್ದರೆ ಪ್ರಥಮ ದರ್ಜೆ ನ್ಯಾಯಿಕ ಮ್ಯಾಜಿಸ್ಟ್ರೇಟ್ ಅವರ ಮುಂದೆ ಸಲ್ಲಿಸಲಾಗುತ್ತದೆ."
)

COURT_FRAGMENTS_KN = {
    "Family Court": "ಕುಟುಂಬ ನ್ಯಾಯಾಲಯವನ್ನು",
    "Magistrate": "ಮ್ಯಾಜಿಸ್ಟ್ರೇಟ್ ಅವರನ್ನು",
    "Judicial Magistrate First Class": "ಮ್ಯಾಜಿಸ್ಟ್ರೇಟ್ ಅವರನ್ನು",
    "Registrar": "ಜನನ ಮತ್ತು ಮರಣಗಳ ರಿಜಿಸ್ಟ್ರಾರ್ ಅವರನ್ನು",
    "Registrar of Births and Deaths": "ಜನನ ಮತ್ತು ಮರಣಗಳ ರಿಜಿಸ್ಟ್ರಾರ್ ಅವರನ್ನು",
    "District Registrar": "ಜಿಲ್ಲಾ ರಿಜಿಸ್ಟ್ರಾರ್ ಅವರನ್ನು",
}


def _join_clauses(parts: Sequence[str]) -> str:
    return " ".join(p.strip() for p in parts if p and p.strip())


def _normalize_kn_facts(raw_facts: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """Project typed FactEvidence / tri-state strings to plain bool/str values.

    Same contract as laya_prose_v2._normalize_prose_facts, copied locally so
    this module stays standalone: strings like 'unknown' NEVER act truthy.
    """
    out: Dict[str, Any] = {}
    for k, v in (raw_facts or {}).items():
        if hasattr(v, "status") and hasattr(v, "value"):
            st = getattr(v, "status")
            inner = getattr(v, "value")
            if st == "supported":
                out[k] = True if inner is None else inner
            elif st == "denied":
                out[k] = False if inner in (None, True) else inner
            else:
                out[k] = False if k not in {"claimant_sex", "claimant_role"} else "unknown"
        elif isinstance(v, dict) and "status" in v:
            st = v.get("status")
            inner = v.get("value")
            if st == "supported":
                out[k] = True if inner is None else inner
            elif st == "denied":
                out[k] = False if inner in (None, True) else inner
            else:
                out[k] = False if k not in {"claimant_sex", "claimant_role"} else "unknown"
        elif isinstance(v, str) and k not in {"claimant_sex", "claimant_role"}:
            low = v.strip().lower()
            if low in {"true", "yes", "1", "supported"}:
                out[k] = True
            elif low in {"false", "no", "0", "denied", "unknown", "none", "null", "unclear", "conflicting", ""}:
                out[k] = False
            else:
                out[k] = v
        else:
            out[k] = v
    return out


def _payer_kn(facts: Dict[str, Any]) -> str:
    if facts.get("claimant_role") == "parent":
        return "ಎದುರು ಪಕ್ಷದ"
    if facts.get("claimant_sex") == "male":
        return "ನಿಮ್ಮ ಸಂಗಾತಿಯ"
    return "ನಿಮ್ಮ ಗಂಡನ"


# ---------------------------------------------------------------------------
# Section renderers (all DRAFT — NEEDS P2.1 verification)
# ---------------------------------------------------------------------------
def _render_maintenance_kn(kept: set, facts: Dict[str, Any]) -> str:
    if not (kept & {"bnss-144", "bnss-144-3", "bnss-146", "pwdva-20", "hma-24", "hma-25"}):
        return ""
    male = facts.get("claimant_sex") == "male"
    is_parent = facts.get("claimant_role") == "parent"
    child = bool(facts.get("child_fact"))
    school_fees = bool(facts.get("school_fees_fact"))
    parts: List[str] = []

    if kept & {"bnss-144", "pwdva-20"}:
        if is_parent:
            parts.append(
                "ತಮ್ಮನ್ನು ತಾವೇ ನೋಡಿಕೊಳ್ಳಲು ಸಾಧ್ಯವಾಗದ ಪೋಷಕರು, ಸಾಕಷ್ಟು ಆದಾಯವಿರುವ ವಯಸ್ಕ ಮಗುವಿನಿಂದ "
                "ತಿಂಗಳಿಗೆ ಜೀವನಾಂಶ ಕೇಳಬಹುದು."
            )
        elif male:
            if child:
                parts.append("ನಿಮ್ಮ ಮಗುವಿಗಾಗಿ ತಿಂಗಳಿಗೆ ಜೀವನಾಂಶ ಕೇಳಬಹುದು.")
            else:
                parts.append(
                    "ತಿಂಗಳಿಗೆ ಜೀವನಾಂಶವು ಸಾಮಾನ್ಯ ನಿಯಮಗಳ ಅಡಿಯಲ್ಲಿ ಅವಲಂಬನೆ ಮತ್ತು "
                    "ಅನ್ವಯಿಸುವ ಕೌಟುಂಬಿಕ ಪ್ರಕರಣವನ್ನು ಅವಲಂಬಿಸಿರುತ್ತದೆ."
                )
            if "bnss-144" in kept:
                parts.append(
                    "ಭಾರತೀಯ ನಾಗರಿಕ ಸುರಕ್ಷಾ ಸಂಹಿತೆ, 2023 ರ ಸೆಕ್ಷನ್ 144 ರ ಅಡಿಯಲ್ಲಿ, "
                    "ಮಗುವಿನ ಪಾಲನೆಗಾಗಿ ಪೋಷಕರಿಂದ ಜೀವನಾಂಶ ಕೇಳಬಹುದು."
                )
        else:
            if child:
                parts.append("ನಿಮಗಾಗಿ ಮತ್ತು ನಿಮ್ಮ ಮಗುವಿಗಾಗಿ ತಿಂಗಳಿಗೆ ಜೀವನಾಂಶ ಕೇಳಬಹುದು.")
            else:
                parts.append("ನಿಮಗಾಗಿ ತಿಂಗಳಿಗೆ ಜೀವನಾಂಶ ಕೇಳಬಹುದು.")
            if "bnss-144" in kept:
                parts.append(
                    "ಭಾರತೀಯ ನಾಗರಿಕ ಸುರಕ್ಷಾ ಸಂಹಿತೆ, 2023 ರ ಸೆಕ್ಷನ್ 144 ರ ಅಡಿಯಲ್ಲಿ "
                    "ಪತ್ನಿಯು ಗಂಡನಿಂದ ಜೀವನಾಂಶ ಕೇಳಬಹುದು."
                )
            if "pwdva-20" in kept:
                parts.append(
                    "ಕೌಟುಂಬಿಕ ದೌರ್ಜನ್ಯ ತಡೆ ಕಾಯ್ದೆ, 2005 ರ ಸೆಕ್ಷನ್ 20 ರ ಅಡಿಯಲ್ಲಿ "
                    "ನೀವು ಹಣಕಾಸಿನ ಪರಿಹಾರವನ್ನೂ ಕೇಳಬಹುದು."
                )

    if "bnss-144-3" in kept:
        parts.append(
            "ನಿಮ್ಮ ಜೀವನಾಂಶ ಆದೇಶದ ಹಣ ಬಾಕಿ ಇದ್ದರೆ, ಅದನ್ನು ವಸೂಲು ಮಾಡಲು ಅರ್ಜಿ ಸಲ್ಲಿಸಬಹುದು. "
            "ಭಾರತೀಯ ನಾಗರಿಕ ಸುರಕ್ಷಾ ಸಂಹಿತೆ, 2023 ರ ಸೆಕ್ಷನ್ 144(3) ರ ಅಡಿಯಲ್ಲಿ ಬಾಕಿ ಹಣ ವಸೂಲು ಮಾಡಬಹುದು. "
            "ಪ್ರತಿ ಬಾಕಿ ಮೊತ್ತಕ್ಕೆ ಒಂದು ವರ್ಷದ ಕಾಲಮಿತಿ ಇರುತ್ತದೆ. "
            "ಆದ್ದರಿಂದ ಅರ್ಜಿಯ ಸಮಯವನ್ನು ಬೇಗ ಪರಿಶೀಲಿಸಿ. "
            "ಆದೇಶ ಮತ್ತು ಬಾಕಿ ಕಂತುಗಳ ಪಟ್ಟಿಯನ್ನು ಜೊತೆಯಲ್ಲಿ ಇಟ್ಟುಕೊಳ್ಳಿ."
        )
    if "bnss-146" in kept:
        parts.append(
            "ಜೀವನಾಂಶ ಆದೇಶವನ್ನು ಬದಲಾಯಿಸಬೇಕಾದರೆ ಅರ್ಜಿ ಸಲ್ಲಿಸಬಹುದು. "
            "ಭಾರತೀಯ ನಾಗರಿಕ ಸುರಕ್ಷಾ ಸಂಹಿತೆ, 2023 ರ ಸೆಕ್ಷನ್ 146 ರ ಅಡಿಯಲ್ಲಿ "
            "ಪರಿಸ್ಥಿತಿ ಬದಲಾದಾಗ ಆದೇಶವನ್ನು ಬದಲಾಯಿಸಬಹುದು. "
            "ಹಳೆಯ ಆದೇಶ ಮತ್ತು ಪರಿಸ್ಥಿತಿ ಬದಲಾದುದರ ಪುರಾವೆಗಳನ್ನು ಜೊತೆಯಲ್ಲಿ ಇಟ್ಟುಕೊಳ್ಳಿ."
        )
    if "hma-24" in kept:
        if male:
            parts.append(
                "ಹಿಂದೂ ವಿವಾಹ ಕಾಯ್ದೆ, 1955 ರ ಅಡಿಯಲ್ಲಿ ನಿಮ್ಮ ಪ್ರಕರಣ ಈಗಾಗಲೇ ನಡೆಯುತ್ತಿರುವುದರಿಂದ, "
                "ಸ್ವಂತ ಆದಾಯ ಸಾಕಾಗದ ಸಂಗಾತಿಯು ಪ್ರಕರಣ ನಡೆಯುವಾಗ ಮಧ್ಯಂತರ ಜೀವನಾಂಶ ಕೇಳಬಹುದು. "
                "ಸೆಕ್ಷನ್ 24 ರ ಅಡಿಯಲ್ಲಿ ಕುಟುಂಬ ನ್ಯಾಯಾಲಯವು ಇದನ್ನು ನೀಡಬಹುದು."
            )
        else:
            parts.append(
                "ಹಿಂದೂ ವಿವಾಹ ಕಾಯ್ದೆ, 1955 ರ ಅಡಿಯಲ್ಲಿ ನಿಮ್ಮ ಪ್ರಕರಣ ಈಗಾಗಲೇ ನಡೆಯುತ್ತಿರುವುದರಿಂದ, "
                "ಪ್ರಕರಣ ನಡೆಯುವಾಗ ಮಧ್ಯಂತರ ಜೀವನಾಂಶ ಕೇಳಬಹುದು. "
                "ಸೆಕ್ಷನ್ 24 ರ ಅಡಿಯಲ್ಲಿ ಕುಟುಂಬ ನ್ಯಾಯಾಲಯವು ಇದನ್ನು ನೀಡಬಹುದು."
            )
    if "hma-25" in kept:
        parts.append(
            "ತೀರ್ಪು ನೀಡುವಾಗ ಅಥವಾ ನಂತರ ಯಾವಾಗ ಬೇಕಾದರೂ, ಶಾಶ್ವತ ಜೀವನಾಂಶ ಅಥವಾ ಒಟ್ಟು ಮೊತ್ತದ ಜೀವನಾಂಶ ಕೇಳಬಹುದು. "
            "ಹಿಂದೂ ವಿವಾಹ ಕಾಯ್ದೆ, 1955 ರ ಸೆಕ್ಷನ್ 25 ರ ಅಡಿಯಲ್ಲಿ ಇಬ್ಬರು ಸಂಗಾತಿಗಳಲ್ಲಿ ಯಾರಾದರೂ ಇದನ್ನು ಕೇಳಬಹುದು."
        )

    payer = _payer_kn(facts)
    school_clause = " ಮತ್ತು ನಿಮ್ಮ ಮಗುವಿನ ಶಾಲಾ ಶುಲ್ಕಗಳನ್ನು" if (child and school_fees) else ""
    parts.append(
        "ತಿಂಗಳಿಗೆ ಎಷ್ಟು ಮೊತ್ತ ಸಿಗುತ್ತದೆ ಎಂದು ಇಲ್ಲಿ ನಿಗದಿ ಮಾಡಲು ಸಾಧ್ಯವಿಲ್ಲ. "
        f"ಅದು {payer} ಆದಾಯ ಮತ್ತು ನಿಮ್ಮ ಅಗತ್ಯಗಳನ್ನು{school_clause} ಅವಲಂಬಿಸಿರುತ್ತದೆ. "
        "ಮೊತ್ತವನ್ನು ನ್ಯಾಯಾಲಯ ನಿರ್ಧರಿಸುತ್ತದೆ. "
        "ಈ ವ್ಯವಸ್ಥೆಯು ಮೊತ್ತವನ್ನು ನಿರ್ಧರಿಸುವುದಿಲ್ಲವಾದ್ದರಿಂದ ಇಲ್ಲಿ ಯಾವುದೇ ಮೊತ್ತವನ್ನು ಹೇಳಲಾಗಿಲ್ಲ."
    )
    return _join_clauses(parts)


def _render_custody_kn(kept: set, facts: Dict[str, Any]) -> str:
    if not (kept & {"gwa-1890", "hmga-1956-s6", "welfare-principle", "hma-26"}):
        return ""
    # welfare-principle template: the opening sentence itself.
    parts = [
        "ನಿಮ್ಮ ಮಗು ಯಾರ ಜೊತೆ ಇರುತ್ತದೆ ಎಂಬುದನ್ನು ಮಗುವಿನ ಹಿತವನ್ನು ಮೊದಲು ನೋಡಿ ನಿರ್ಧರಿಸಲಾಗುತ್ತದೆ."
    ]
    if "gwa-1890" in kept:
        parts.append("ಗಾರ್ಡಿಯನ್ಸ್ ಮತ್ತು ವಾರ್ಡ್ಸ್ ಕಾಯ್ದೆ, 1890 ಪಾಲನೆಗೆ ಅನ್ವಯಿಸುವ ಕಾಯ್ದೆ.")
    if "hmga-1956-s6" in kept:
        parts.append(
            "ಹಿಂದೂ ಅಪ್ರಾಪ್ತ ಮತ್ತು ಪಾಲನಾ ಕಾಯ್ದೆ, 1956 ರ ಸೆಕ್ಷನ್ 6 ಕೂಡ ಹಿಂದೂ ಮಗುವಿನ ಪಾಲನೆಗೆ ಅನ್ವಯಿಸುತ್ತದೆ."
        )
    if "hma-26" in kept:
        is_pending = bool(facts.get("proceeding_pending_hma", facts.get("proceeding_pending")))
        if is_pending:
            parts.append(
                "ಹಿಂದೂ ವಿವಾಹ ಕಾಯ್ದೆ, 1955 ರ ಅಡಿಯಲ್ಲಿ ನಿಮ್ಮ ಪ್ರಕರಣ ಈಗಾಗಲೇ ನಡೆಯುತ್ತಿರುವುದರಿಂದ, "
                "ಪ್ರಕರಣ ನಡೆಯುವಾಗ ಮಗುವಿನ ಬಗ್ಗೆ ಕುಟುಂಬ ನ್ಯಾಯಾಲಯವು ಸೆಕ್ಷನ್ 26 ರ ಅಡಿಯಲ್ಲಿ ಆದೇಶ ನೀಡಬಹುದು."
            )
        else:
            parts.append(
                "ಹಿಂದೂ ವಿವಾಹ ಕಾಯ್ದೆ, 1955 ರ ಅಡಿಯಲ್ಲಿ ಪ್ರಕರಣ ಸಲ್ಲಿಸುವ ಜೊತೆಗೆ ಮಗುವಿನ ಬಗ್ಗೆ "
                "ಕುಟುಂಬ ನ್ಯಾಯಾಲಯವು ಸೆಕ್ಷನ್ 26 ರ ಅಡಿಯಲ್ಲಿ ಆದೇಶ ನೀಡಬಹುದು."
            )
    return _join_clauses(parts)


def _render_stridhan_and_property_kn(kept: set, facts: Dict[str, Any]) -> str:
    """D1-A / D2 safe Stridhan renderer. NEVER cites HMA s.27 unless kept."""
    has_27 = "hma-27" in kept
    has_316 = "bns-316" in kept
    if not (has_27 or has_316):
        return ""
    parts: List[str] = []
    joint_only = has_27 and not has_316 and bool(facts.get("joint_property_claim", facts.get("joint_property_fact")))
    sold = bool(facts.get("stridhan_sold_or_mortgaged", facts.get("stridhan_sold")))

    if joint_only:
        parts.append(
            "ಇಬ್ಬರು ಸಂಗಾತಿಗಳ ಜಂಟಿ ಒಡೆತನದಲ್ಲಿರುವ, ಮದುವೆಗೆ ಸಂಬಂಧಿಸಿದ ಆಸ್ತಿಯನ್ನು "
            "ನಡೆಯುತ್ತಿರುವ ಅಥವಾ ಸಲ್ಲಿಸುತ್ತಿರುವ ಕೌಟುಂಬಿಕ ಪ್ರಕರಣದ ಒಳಗೆ "
            "ಹಿಂದೂ ವಿವಾಹ ಕಾಯ್ದೆ, 1955 ರ ಸೆಕ್ಷನ್ 27 ರ ಅಡಿಯಲ್ಲಿ ಪರಿಹರಿಸಬಹುದು."
        )
        return _join_clauses(parts)

    parts.append("ಮದುವೆಯಲ್ಲಿ ನಿಮಗೆ ಕೊಟ್ಟ ಬಂಗಾರ, ಹಣ ಮತ್ತು ಉಡುಗೊರೆಗಳು ನಿಮಗೆ ಸೇರಿದವು.")
    if has_27:
        if sold:
            parts.append(
                "ಹಿಂದೂ ವಿವಾಹ ಕಾಯ್ದೆ, 1955 ರ ಪ್ರಕರಣ ನಡೆಯುತ್ತಿರುವುದರಿಂದ ಅಥವಾ ಸಲ್ಲಿಸುತ್ತಿರುವುದರಿಂದ, "
                "ಅವುಗಳನ್ನು ಮಾರಲಾಗಿರುವುದರಿಂದ ಅವುಗಳ ಬೆಲೆಯನ್ನು ಸೆಕ್ಷನ್ 27 ರ ಅಡಿಯಲ್ಲಿ ಹಿಂದಿರುಗಿಸಲು ಕೇಳಬಹುದು."
            )
        else:
            parts.append(
                "ಹಿಂದೂ ವಿವಾಹ ಕಾಯ್ದೆ, 1955 ರ ಪ್ರಕರಣ ನಡೆಯುತ್ತಿರುವುದರಿಂದ ಅಥವಾ ಸಲ್ಲಿಸುತ್ತಿರುವುದರಿಂದ, "
                "ಅವುಗಳನ್ನು ಹಿಂದಿರುಗಿಸಲು ಸೆಕ್ಷನ್ 27 ರ ಅಡಿಯಲ್ಲಿ ಕೇಳಬಹುದು."
            )
    else:
        if sold:
            parts.append(
                "ಹಿಂದೂ ವಿವಾಹ ಕಾಯ್ದೆ, 1955 ರ ಪ್ರಕರಣ ನಡೆಯುತ್ತಿಲ್ಲವಾದರೆ ಅಥವಾ ಸಲ್ಲಿಸುತ್ತಿಲ್ಲವಾದರೆ, "
                "ಅವುಗಳ ಬೆಲೆಯನ್ನು ಕುಟುಂಬ ನ್ಯಾಯಾಲಯದ ಮುಂದೆ ಆಸ್ತಿ ಹಕ್ಕಿನ ಮೂಲಕ ಕೇಳಬಹುದು."
            )
        else:
            parts.append(
                "ಹಿಂದೂ ವಿವಾಹ ಕಾಯ್ದೆ, 1955 ರ ಪ್ರಕರಣ ನಡೆಯುತ್ತಿಲ್ಲವಾದರೆ ಅಥವಾ ಸಲ್ಲಿಸುತ್ತಿಲ್ಲವಾದರೆ, "
                "ಅವುಗಳನ್ನು ಹಿಂದಿರುಗಿಸಲು ಕುಟುಂಬ ನ್ಯಾಯಾಲಯದ ಮುಂದೆ ಆಸ್ತಿ ಹಕ್ಕಿನ ಮೂಲಕ ಕೇಳಬಹುದು."
            )
    if has_316:
        parts.append(
            "ಪತ್ನಿಯ ಆಸ್ತಿಯನ್ನು ಹಿಂದಿರುಗಿಸದೆ ಇಟ್ಟುಕೊಳ್ಳುವುದು ಅಥವಾ ದುರುಪಯೋಗ ಮಾಡುವುದು "
            "ಭಾರತೀಯ ನ್ಯಾಯ ಸಂಹಿತೆ, 2023 ರ ಸೆಕ್ಷನ್ 316 ರ ಅಡಿಯಲ್ಲಿ ಅಪರಾಧವಾಗಬಹುದು."
        )
    return _join_clauses(parts)


def _render_residence_and_dv_kn(kept: set, facts: Dict[str, Any]) -> str:
    if not (kept & {"pwdva-17", "pwdva-18", "pwdva-19", "pwdva-22"}):
        return ""
    parts: List[str] = []
    if kept & {"pwdva-17", "pwdva-19"}:
        parts.append("ಹಂಚಿದ ಮನೆಯಲ್ಲಿ ವಾಸಿಸುವ ಹಕ್ಕು ನಿಮಗಿದೆ.")
    if "pwdva-17" in kept:
        parts.append(
            "ಕೌಟುಂಬಿಕ ದೌರ್ಜನ್ಯ ತಡೆ ಕಾಯ್ದೆ, 2005 ರ ಸೆಕ್ಷನ್ 17 ರ ಅಡಿಯಲ್ಲಿ "
            "ಹಂಚಿದ ಮನೆಯಲ್ಲಿ ವಾಸಿಸುವ ಹಕ್ಕು ನಿಮಗಿದೆ."
        )
    if "pwdva-19" in kept:
        parts.append(
            "ಕೌಟುಂಬಿಕ ದೌರ್ಜನ್ಯ ತಡೆ ಕಾಯ್ದೆ, 2005 ರ ಸೆಕ್ಷನ್ 19 ರ ಅಡಿಯಲ್ಲಿ "
            "ನ್ಯಾಯಾಲಯವು ಹಂಚಿದ ಮನೆಯ ಬಗ್ಗೆ ವಾಸಸ್ಥಳ ಆದೇಶ ನೀಡಬಹುದು."
        )
    if "pwdva-18" in kept:
        parts.append(
            "ಕೌಟುಂಬಿಕ ದೌರ್ಜನ್ಯ ತಡೆ ಕಾಯ್ದೆ, 2005 ರ ಸೆಕ್ಷನ್ 18 ರ ಅಡಿಯಲ್ಲಿ "
            "ನ್ಯಾಯಾಲಯವು ಮನೆಯಲ್ಲಿ ಹಿಂಸೆ, ಬೆದರಿಕೆ ಮತ್ತು ಕಿರುಕುಳವನ್ನು ನಿಲ್ಲಿಸುವ ರಕ್ಷಣಾ ಆದೇಶ ನೀಡಬಹುದು."
        )
    if "pwdva-22" in kept:
        parts.append(
            "ಕೌಟುಂಬಿಕ ದೌರ್ಜನ್ಯ ತಡೆ ಕಾಯ್ದೆ, 2005 ರ ಸೆಕ್ಷನ್ 22 ರ ಅಡಿಯಲ್ಲಿ "
            "ನ್ಯಾಯಾಲಯವು ಕೌಟುಂಬಿಕ ಹಿಂಸೆಯಿಂದಾದ ಗಾಯಗಳಿಗೆ, ಮಾನಸಿಕ ಹಿಂಸೆ ಮತ್ತು ಭಾವನಾತ್ಮಕ ನೋವು ಸೇರಿದಂತೆ, "
            "ಪರಿಹಾರ ನೀಡುವಂತೆ ಆದೇಶಿಸಬಹುದು."
        )
    return _join_clauses(parts)


def _render_divorce_and_restitution_kn(kept: set, facts: Dict[str, Any]) -> Tuple[str, bool]:
    """Returns (paragraph, needs_failsafe_escalation)."""
    parts: List[str] = []
    failsafe = False

    if "hma-13" in kept:
        pend = bool(facts.get("proceeding_pending_hma", facts.get("proceeding_pending")))
        if facts.get("divorce_asked") or pend:
            if pend:
                parts.append(
                    "ನಿಮ್ಮ ವಿಚ್ಛೇದನ ಪ್ರಕರಣ ಈಗಾಗಲೇ ನಡೆಯುತ್ತಿದೆ. "
                    "ಹಿಂದೂ ವಿವಾಹ ಕಾಯ್ದೆ, 1955 ರ ಸೆಕ್ಷನ್ 13 ರ ಅಡಿಯಲ್ಲಿ ಅದನ್ನು ಕುಟುಂಬ ನ್ಯಾಯಾಲಯವು "
                    "ನಿಮ್ಮ ಪ್ರಕರಣದ ವಿವರಗಳು ಮತ್ತು ಪುರಾವೆಗಳ ಆಧಾರದ ಮೇಲೆ ನಿರ್ಧರಿಸುತ್ತದೆ."
                )
            else:
                parts.append(
                    "ನೀವು ವಿಚ್ಛೇದನ ಕೇಳಿದ್ದೀರಿ. "
                    "ಹಿಂದೂ ವಿವಾಹ ಕಾಯ್ದೆ, 1955 ರ ಸೆಕ್ಷನ್ 13 ರ ಅಡಿಯಲ್ಲಿ ವಿಚ್ಛೇದನ ಕೇಳಬಹುದು. "
                    "ಕುಟುಂಬ ನ್ಯಾಯಾಲಯವು ನಿಮ್ಮ ಪ್ರಕರಣದ ವಿವರಗಳು ಮತ್ತು ಪುರಾವೆಗಳ ಆಧಾರದ ಮೇಲೆ ನಿರ್ಧರಿಸುತ್ತದೆ."
                )
        else:
            failsafe = True

    if "hma-13b" in kept:
        if facts.get("divorce_asked") and facts.get("mutual_consent"):
            parts.append(
                "ಇಬ್ಬರು ಸಂಗಾತಿಗಳು ಮದುವೆಯನ್ನು ಕೊನೆಗೊಳಿಸಲು ಒಪ್ಪಿರುವುದರಿಂದ, "
                "ಪರಸ್ಪರ ಒಪ್ಪಿಗೆಯ ವಿಚ್ಛೇದನ ಅರ್ಜಿಯನ್ನು ಹಿಂದೂ ವಿವಾಹ ಕಾಯ್ದೆ, 1955 ರ ಸೆಕ್ಷನ್ 13ಬಿ ರ ಅಡಿಯಲ್ಲಿ "
                "ಕುಟುಂಬ ನ್ಯಾಯಾಲಯದ ಮುಂದೆ ಸಲ್ಲಿಸಬಹುದು."
            )
        else:
            failsafe = True

    if "hma-9" in kept:
        parts.append(
            "ಸಂಗಾತಿಯು ಸರಿಯಾದ ಕಾರಣವಿಲ್ಲದೆ ಇನ್ನೊಬ್ಬ ಸಂಗಾತಿಯ ಜೊತೆ ವಾಸಿಸುವುದನ್ನು ಬಿಟ್ಟಿದ್ದರೆ, "
            "ಹಿಂದೂ ವಿವಾಹ ಕಾಯ್ದೆ, 1955 ರ ಸೆಕ್ಷನ್ 9 ರ ಅಡಿಯಲ್ಲಿ ದಾಂಪತ್ಯ ಹಕ್ಕುಗಳ ಪುನಃಸ್ಥಾಪನೆಗಾಗಿ "
            "ಕುಟುಂಬ ನ್ಯಾಯಾಲಯದ ಮುಂದೆ ಅರ್ಜಿ ಸಲ್ಲಿಸಬಹುದು."
        )

    return _join_clauses(parts), failsafe


def _render_birth_certificate_kn(kept: set) -> str:
    if "births-deaths-act-1969" not in kept:
        return ""
    return (
        "ನಿಮ್ಮ ಮಗುವಿನ ಜನನ ಪ್ರಮಾಣಪತ್ರವನ್ನು ಜನನ ಮತ್ತು ಮರಣಗಳ ರಿಜಿಸ್ಟ್ರಾರ್ ಅವರಿಂದ ಪಡೆಯಬಹುದು. "
        "ಜನನ ನೋಂದಣಿಯನ್ನು ಜನನ ಮತ್ತು ಮರಣಗಳ ನೋಂದಣಿ ಕಾಯ್ದೆ, 1969 ರ ಅಡಿಯಲ್ಲಿ ಮಾಡಲಾಗುತ್ತದೆ. "
        "ಆಸ್ಪತ್ರೆಯು ಪ್ರಮಾಣಪತ್ರ ನೀಡದಿದ್ದರೆ, ಆಸ್ಪತ್ರೆಯ ದಾಖಲೆ ಅಥವಾ ಜನನದ ಬೇರೆ ಪುರಾವೆಯೊಂದಿಗೆ "
        "ರಿಜಿಸ್ಟ್ರಾರ್ ಅವರಿಗೆ ಅರ್ಜಿ ಸಲ್ಲಿಸಬಹುದು. "
        "ತಡವಾಗಿ ನೋಂದಣಿ ಮಾಡುವ ವಿಧಾನವು ಜನನವಾಗಿ ಎಷ್ಟು ಸಮಯವಾಗಿದೆ ಎಂಬುದನ್ನು ಅವಲಂಬಿಸಿರುತ್ತದೆ."
    )


def _render_escalation_lines_kn(kinds: Sequence[str], kept: set, facts: Dict[str, Any]) -> List[str]:
    payer = _payer_kn(facts)
    child = bool(facts.get("child_fact"))
    school_fees = bool(facts.get("school_fees_fact"))
    res_claim = bool(facts.get("residence_claim"))

    kind_set = set(kinds or [])
    order = ["quantum", "court", "demand", "recovery", "custody", "residence", "safety", "procedure", "fact"]
    lines: List[str] = []

    for k in order:
        if k not in kind_set:
            continue
        if k == "quantum":
            sf_part = " ಮತ್ತು ನಿಮ್ಮ ಮಗುವಿನ ಶಾಲಾ ಶುಲ್ಕಗಳು" if (child and school_fees) else ""
            lines.append(
                "ತಿಂಗಳಿಗೆ ಎಷ್ಟು ಮೊತ್ತ ಸಿಗುತ್ತದೆ ಎಂದು ಇಲ್ಲಿ ನಿಗದಿ ಮಾಡಲು ಸಾಧ್ಯವಿಲ್ಲ. "
                f"{payer} ಆದಾಯ ಮತ್ತು ನಿಮ್ಮ ಅಗತ್ಯಗಳು{sf_part} ಗೊತ್ತಾದ ನಂತರ ಮೊತ್ತವನ್ನು ನಿರ್ಧರಿಸಲಾಗುತ್ತದೆ."
            )
        elif k == "court":
            lines.append(
                "ಕೊಟ್ಟಿರುವ ಮಾಹಿತಿಯಿಂದ ಯಾವ ನ್ಯಾಯಾಲಯ ಎಂದು ಹೇಳಲು ಸಾಧ್ಯವಿಲ್ಲ. "
                "ಮಾನವ ಸಲಹೆಗಾರರು ನಿಮ್ಮ ಪ್ರಶ್ನೆಯನ್ನು ನೋಡಿ ಯಾವ ನ್ಯಾಯಾಲಯ ಎಂದು ಹೇಳುತ್ತಾರೆ."
            )
        elif k == "demand":
            lines.append(
                "ನ್ಯಾಯಾಲಯಕ್ಕೆ ಹೋಗುವ ಮೊದಲು, ನಿಮ್ಮ ಆಸ್ತಿಯನ್ನು ಹಿಂದಿರುಗಿಸುವಂತೆ ಲಿಖಿತವಾಗಿ ಕೇಳಿ ಮತ್ತು ಅದರ ಪ್ರತಿಯನ್ನು ಇಟ್ಟುಕೊಳ್ಳಿ."
            )
        elif k == "recovery":
            has_316 = "bns-316" in kept
            has_27 = "hma-27" in kept
            if has_316 and has_27:
                lines.append(
                    "ಮಾರಿದ ಅಥವಾ ಹಿಂದಿರುಗಿಸದ ಆಸ್ತಿಯನ್ನು ವಸೂಲು ಮಾಡಲು ಅಥವಾ ಅದರ ಬೆಲೆ ನಿಗದಿ ಮಾಡಲು "
                    "ಮಾನವ ವಕೀಲರ ಸಹಾಯ ಬೇಕು. "
                    "ಭಾರತೀಯ ನ್ಯಾಯ ಸಂಹಿತೆ, 2023 ರ ಸೆಕ್ಷನ್ 316 ರ ಅಡಿಯಲ್ಲಿ ಪೊಲೀಸ್ ದೂರು ಮತ್ತು "
                    "ಹಿಂದೂ ವಿವಾಹ ಕಾಯ್ದೆ, 1955 ರ ಸೆಕ್ಷನ್ 27 ರ ಅಡಿಯಲ್ಲಿ ಸಿವಿಲ್ ವಸೂಲಿ ಬೇಕಾಗಬಹುದು."
                )
            elif has_316:
                lines.append(
                    "ಮಾರಿದ ಅಥವಾ ಹಿಂದಿರುಗಿಸದ ಆಸ್ತಿಯನ್ನು ವಸೂಲು ಮಾಡಲು ಅಥವಾ ಅದರ ಬೆಲೆ ನಿಗದಿ ಮಾಡಲು "
                    "ಮಾನವ ವಕೀಲರ ಸಹಾಯ ಬೇಕು. "
                    "ಭಾರತೀಯ ನ್ಯಾಯ ಸಂಹಿತೆ, 2023 ರ ಸೆಕ್ಷನ್ 316 ರ ಅಡಿಯಲ್ಲಿ ಪೊಲೀಸ್ ದೂರು ಮತ್ತು "
                    "ಕುಟುಂಬ ನ್ಯಾಯಾಲಯದ ಮುಂದೆ ಸಿವಿಲ್ ವಸೂಲಿ ಬೇಕಾಗಬಹುದು."
                )
            elif has_27:
                lines.append(
                    "ಮಾರಿದ ಅಥವಾ ಹಿಂದಿರುಗಿಸದ ಆಸ್ತಿಯನ್ನು ವಸೂಲು ಮಾಡಲು ಅಥವಾ ಅದರ ಬೆಲೆ ನಿಗದಿ ಮಾಡಲು "
                    "ಮಾನವ ವಕೀಲರ ಸಹಾಯ ಬೇಕು. "
                    "ಹಿಂದೂ ವಿವಾಹ ಕಾಯ್ದೆ, 1955 ರ ಸೆಕ್ಷನ್ 27 ರ ಅಡಿಯಲ್ಲಿ ಸಿವಿಲ್ ವಸೂಲಿ ಬೇಕಾಗಬಹುದು."
                )
            else:
                lines.append(
                    "ಮಾರಿದ ಅಥವಾ ಹಿಂದಿರುಗಿಸದ ಆಸ್ತಿಯನ್ನು ವಸೂಲು ಮಾಡಲು ಅಥವಾ ಅದರ ಬೆಲೆ ನಿಗದಿ ಮಾಡಲು "
                    "ಮಾನವ ವಕೀಲರ ಸಹಾಯ ಬೇಕು. "
                    "ಸಿವಿಲ್ ಆಸ್ತಿ ವಸೂಲಿಗಾಗಿ ಮಾನವ ವಕೀಲರನ್ನು ಸಂಪರ್ಕಿಸಿ."
                )
        elif k == "custody":
            lines.append(
                "ಮಕ್ಕಳ ಪಾಲನೆಯು ಮಗುವಿನ ಹಿತವನ್ನು ಅವಲಂಬಿಸಿರುತ್ತದೆ. ಅದನ್ನು ಕುಟುಂಬ ನ್ಯಾಯಾಲಯ ನಿರ್ಧರಿಸುತ್ತದೆ. "
                "ಮಗುವನ್ನು ಕರೆದೊಯ್ಯುವ ಅಪಾಯವಿದ್ದರೆ, ಮಧ್ಯಂತರ ಪಾಲನೆ ಮತ್ತು ತುರ್ತು ರಕ್ಷಣೆಗಾಗಿ ಮಾನವ ವಕೀಲರು ಸಹಾಯ ಮಾಡಬಹುದು."
            )
        elif k == "residence":
            lines.append(
                "ಹಂಚಿದ ಮನೆಗೆ ಮತ್ತೆ ಪ್ರವೇಶ ಪಡೆಯಲು ಮ್ಯಾಜಿಸ್ಟ್ರೇಟ್ ಅವರ ವಾಸಸ್ಥಳ ಆದೇಶ ಬೇಕು. "
                "ವಾಸಸ್ಥಳ ಅರ್ಜಿ ಸಲ್ಲಿಸಲು ಮಾನವ ಸಲಹೆಗಾರರು ಅಥವಾ ವಕೀಲರ ಸಹಾಯ ಪಡೆಯಿರಿ."
            )
        elif k == "safety":
            lines.append(
                "ಕೌಟುಂಬಿಕ ಹಿಂಸೆ ಅಥವಾ ಬೆದರಿಕೆ ಇರುವುದರಿಂದ, ತಕ್ಷಣದ ರಕ್ಷಣಾ ಆದೇಶ ಪಡೆಯಲು "
                "ರಕ್ಷಣಾ ಅಧಿಕಾರಿ, ಸಹಾಯವಾಣಿ ಅಥವಾ ವಕೀಲರ ಸಹಾಯವನ್ನು ತಕ್ಷಣ ಪಡೆಯಿರಿ. "
                "ತುರ್ತು ಸಹಾಯಕ್ಕೆ 112 ಕ್ಕೆ ಕರೆ ಮಾಡಿ. ಮಹಿಳಾ ಸಹಾಯವಾಣಿ 181. ಮಕ್ಕಳ ಸಹಾಯವಾಣಿ 1098."
            )
        elif k == "procedure":
            lines.append(
                "ಅರ್ಜಿ ಸಲ್ಲಿಸುವ ನಿಖರವಾದ ಹಂತಗಳು ಮತ್ತು ಸಮಯವು ನಿಮ್ಮ ಪ್ರಕರಣದ ವಿವರಗಳನ್ನು ಅವಲಂಬಿಸಿರುತ್ತದೆ. "
                "ಸಂಬಂಧಪಟ್ಟ ಅಧಿಕಾರಿ ಅಥವಾ ಮಾನವ ಸಲಹೆಗಾರರು ಔಪಚಾರಿಕ ಅರ್ಜಿಯ ಬಗ್ಗೆ ಮಾರ್ಗದರ್ಶನ ನೀಡಬಹುದು."
            )
        elif k == "fact":
            extra = []
            if child and school_fees:
                extra.append("ಮಗುವಿನ ಶಾಲಾ ಶುಲ್ಕದ ಮೊತ್ತ")
            if res_claim:
                whereabouts = (
                    "ಎದುರು ಪಕ್ಷ ಈಗ ಎಲ್ಲಿ ವಾಸಿಸುತ್ತಿದ್ದಾರೆ"
                    if facts.get("claimant_role") == "parent"
                    else ("ನಿಮ್ಮ ಸಂಗಾತಿ ಈಗ ಎಲ್ಲಿ ವಾಸಿಸುತ್ತಿದ್ದಾರೆ" if facts.get("claimant_sex") == "male" else "ನಿಮ್ಮ ಗಂಡ ಈಗ ಎಲ್ಲಿ ವಾಸಿಸುತ್ತಿದ್ದಾರೆ")
                )
                extra.append(whereabouts)
            extra_str = (", " + ", ".join(extra)) if extra else ""
            lines.append(
                f"ಕೆಲವು ವಿವರಗಳು ಇನ್ನೂ ಬೇಕು. {payer} ಆದಾಯದ ಅಂದಾಜು ಅಥವಾ ವ್ಯಾಪ್ತಿ{extra_str}. "
                "ನಿಮ್ಮ ಬಳಿ ಇರುವ ದಾಖಲೆಗಳನ್ನು ಕೊಡಿ. ಯಾವುದಾದರೂ ದಾಖಲೆ ಇಲ್ಲದಿದ್ದರೆ, ಅದು ಇಲ್ಲ ಎಂದು ಹೇಳಿ."
            )
    return lines


def _format_court_line_kn(court_live: Sequence[str], court_source: Optional[str]) -> str:
    if court_source in ("fallback-escalate", "out-of-scope"):
        return ""
    frags: List[str] = []
    for c in court_live or []:
        if c.startswith("ESCALATE") or c == "none":
            continue
        frag = COURT_FRAGMENTS_KN.get(c)
        if frag and frag not in frags:
            frags.append(frag)
    if not frags:
        return ""
    if len(frags) == 1:
        joined = frags[0]
    elif len(frags) == 2:
        joined = f"{frags[0]} ಮತ್ತು {frags[1]}"
    else:
        joined = ", ".join(frags[:-1]) + f" ಮತ್ತು {frags[-1]}"
    return f"ನೀವು {joined} ಸಂಪರ್ಕಿಸಬೇಕು."


# --- Template coverage table (auditable; every entry is DRAFT) --------------
# Maps each of the 20 sections to the renderer function that emits it.
SECTION_RENDERERS_KN: Dict[str, Callable[..., str]] = {
    "bnss-144": _render_maintenance_kn,
    "bnss-144-3": _render_maintenance_kn,
    "bnss-146": _render_maintenance_kn,
    "pwdva-20": _render_maintenance_kn,
    "hma-24": _render_maintenance_kn,
    "hma-25": _render_maintenance_kn,
    "gwa-1890": _render_custody_kn,
    "hmga-1956-s6": _render_custody_kn,
    "welfare-principle": _render_custody_kn,
    "hma-26": _render_custody_kn,
    "hma-27": _render_stridhan_and_property_kn,
    "bns-316": _render_stridhan_and_property_kn,
    "pwdva-17": _render_residence_and_dv_kn,
    "pwdva-18": _render_residence_and_dv_kn,
    "pwdva-19": _render_residence_and_dv_kn,
    "pwdva-22": _render_residence_and_dv_kn,
    "hma-13": _render_divorce_and_restitution_kn,
    "hma-13b": _render_divorce_and_restitution_kn,
    "hma-9": _render_divorce_and_restitution_kn,
    "births-deaths-act-1969": _render_birth_certificate_kn,
}
TEMPLATE_COVERAGE_KN: Dict[str, str] = {sid: DRAFT_STATUS for sid in KNOWN_SECTIONS_KN}


# ---------------------------------------------------------------------------
# Main renderer
# ---------------------------------------------------------------------------
def render_prose_kn(
    rec: Dict[str, Any],
    facts: Optional[Dict[str, Any]] = None,
    *,
    include_draft_banner: bool = True,
    include_forum_note: bool = False,
    include_checklist: bool = False,
) -> Dict[str, Any]:
    """Render deterministic Kannada user-facing prose strictly from kept_ids,
    court_live, escalation_kinds, and structured facts. NEVER reads question
    text. Every output is DRAFT until P2.1 sign-off (see module docstring).
    """
    t0 = time.perf_counter()
    facts = _normalize_kn_facts(facts if facts is not None else (rec.get("facts") or {}))
    kept_list = list(rec.get("kept_ids") or [])
    kept = set(kept_list)
    in_scope = bool(rec.get("in_scope", True))
    court_live = list(rec.get("court_live") or [])
    court_source = rec.get("court_source")

    raw_typed = rec.get("escalations_typed") or []
    kinds = [e["kind"] for e in raw_typed if isinstance(e, dict) and "kind" in e]
    if rec.get("escalation_kinds"):
        for k in rec["escalation_kinds"]:
            if k not in kinds:
                kinds.append(k)

    def _finish(prose: str, status: str = "ok", unknown_ids: Optional[List[str]] = None) -> Dict[str, Any]:
        ms = round((time.perf_counter() - t0) * 1000.0, 3)
        return {
            "prose": prose,
            "prose_render_ms": ms,
            "prose_template_version": TEMPLATE_VERSION,
            "unknown_ids": unknown_ids or [],
            "status": status,
            "draft": True,
            "p2_1_verified": False,
            "lang": "kn",
        }

    unknown_ids = sorted(kept - KNOWN_SECTIONS_KN)
    unknown_kinds = sorted(k for k in kinds if k not in KNOWN_ESCALATION_KINDS_KN)
    if unknown_ids or unknown_kinds:
        return _finish(INVALID_RECORD_HANDOFF_KN, status="error", unknown_ids=unknown_ids)

    if not in_scope:
        prose = OUT_OF_SCOPE_LINE_KN
        if include_draft_banner:
            prose = DRAFT_NOTICE_KN + "\n\n" + prose
        return _finish(prose)

    if not kept and in_scope:
        if facts.get("no_dispute_empty") and not kinds:
            prose = (
                "ಕೊಟ್ಟಿರುವ ವಿವರಗಳ ಆಧಾರದ ಮೇಲೆ, ನ್ಯಾಯಾಲಯದ ಮಧ್ಯಪ್ರವೇಶ ಬೇಕಾದ ಯಾವುದೇ ವಿವಾದ ಕಾಣುತ್ತಿಲ್ಲ. "
                "ಆದ್ದರಿಂದ ಇಲ್ಲಿ ಯಾವುದೇ ಕಾನೂನು ಸೆಕ್ಷನ್ ಅನ್ವಯಿಸುವುದಿಲ್ಲ. "
                "ಮುಂದೆ ಯಾವುದಾದರೂ ವಿವಾದ ಬಂದರೆ, ವಕೀಲರನ್ನು ಸಂಪರ್ಕಿಸಿ."
            )
            if include_draft_banner:
                prose = DRAFT_NOTICE_KN + "\n\n" + prose
            return _finish(prose)
        if "court" not in kinds and "procedure" not in kinds:
            kinds.append("court")
        paras = _render_escalation_lines_kn(kinds, kept, facts) + [CLOSING_LINE_KN]
        prose = "\n\n".join(p for p in paras if p)
        if include_draft_banner:
            prose = DRAFT_NOTICE_KN + "\n\n" + prose
        return _finish(prose)

    paras: List[str] = []
    if "safety" in kinds:
        paras.append(SAFETY_BANNER_KN)
    paras.append(INTRO_LINE_KN)

    p_maint = _render_maintenance_kn(kept, facts)
    if p_maint:
        paras.append(p_maint)

    p_cust = _render_custody_kn(kept, facts)
    if p_cust:
        paras.append(p_cust)

    p_strid = _render_stridhan_and_property_kn(kept, facts)
    if p_strid:
        paras.append(p_strid)

    p_res = _render_residence_and_dv_kn(kept, facts)
    if p_res:
        paras.append(p_res)

    p_div, div_failsafe = _render_divorce_and_restitution_kn(kept, facts)
    if p_div:
        paras.append(p_div)
    if div_failsafe and "court" not in kinds:
        kinds.append("court")

    p_birth = _render_birth_certificate_kn(kept)
    if p_birth:
        paras.append(p_birth)

    c_line = _format_court_line_kn(court_live, court_source)
    if c_line:
        paras.append(c_line)

    if include_forum_note:
        forum_note = forum_guidance_kn(kept)
        if forum_note:
            paras.append(forum_note)

    paras.extend(_render_escalation_lines_kn(kinds, kept, facts))

    if include_checklist:
        checklist = document_checklist_kn(kept, facts)
        if checklist:
            paras.append(checklist)

    paras.append(CLOSING_LINE_KN)

    prose = "\n\n".join(p for p in paras if p)
    if include_draft_banner:
        prose = DRAFT_NOTICE_KN + "\n\n" + prose
    return _finish(prose)


def render_prose_localized(
    rec: Dict[str, Any],
    facts: Optional[Dict[str, Any]] = None,
    target_lang: str = "auto",
    **kwargs: Any,
) -> Dict[str, Any]:
    """Language dispatcher (V71-P6-1 integration point for Lane 01).

    rec["lang"] in {"kn", "kn_roman"} or target_lang == "kn" -> Kannada
    renderer in this module. Anything else -> English ``laya_prose_v2``
    renderer (lazy import; this module never imports it at module level).
    """
    lang = target_lang
    if lang == "auto":
        lang = (rec.get("lang") or "en")
    if lang in ("kn", "kn_roman"):
        return render_prose_kn(rec, facts, **kwargs)
    try:
        from laya_prose_v2 import render_prose as render_prose_en
    except ImportError:  # pragma: no cover - src/ not on path
        from src.laya_prose_v2 import render_prose as render_prose_en  # type: ignore
    return render_prose_en(rec, facts)


# ---------------------------------------------------------------------------
# P6-2: forum guidance + document checklist (deterministic, template-locked)
# ---------------------------------------------------------------------------
def forum_guidance_kn(kept_ids: Sequence[str]) -> str:
    """Bengaluru / metro forum note. Empty string unless bnss-144 is kept.

    Informational only — it never asks the user to choose a court.
    DRAFT — NEEDS P2.1 verification.
    """
    if "bnss-144" not in set(kept_ids or []):
        return ""
    return FORUM_NOTE_BNSS144_KN


_CHECKLIST_ITEMS_KN: Dict[str, List[str]] = {
    "bnss-144": ["ಮದುವೆ ಪುರಾವೆ", "ಆದಾಯದ ಬಗ್ಗೆ ನಿಮಗೆ ಗೊತ್ತಿರುವ ಮಾಹಿತಿ"],
    "pwdva-20": ["ಮದುವೆ ಪುರಾವೆ", "ಆದಾಯದ ಬಗ್ಗೆ ನಿಮಗೆ ಗೊತ್ತಿರುವ ಮಾಹಿತಿ"],
    "hma-24": ["ಮದುವೆ ಪುರಾವೆ", "ಆದಾಯದ ಬಗ್ಗೆ ನಿಮಗೆ ಗೊತ್ತಿರುವ ಮಾಹಿತಿ"],
    "hma-25": ["ಮದುವೆ ಪುರಾವೆ", "ಆದಾಯದ ಬಗ್ಗೆ ನಿಮಗೆ ಗೊತ್ತಿರುವ ಮಾಹಿತಿ"],
    "bnss-144-3": ["ಹಳೆಯ ಜೀವನಾಂಶ ಆದೇಶ", "ಬಾಕಿ ಕಂತುಗಳು ಮತ್ತು ದಿನಾಂಕಗಳ ಪಟ್ಟಿ"],
    "bnss-146": ["ಹಳೆಯ ಜೀವನಾಂಶ ಆದೇಶ", "ಪರಿಸ್ಥಿತಿ ಬದಲಾದುದರ ಪುರಾವೆಗಳು"],
    "gwa-1890": ["ಮಗುವಿನ ಜನನ ದಾಖಲೆ", "ಮಗುವಿನ ಶಾಲೆಯ ದಾಖಲೆಗಳು"],
    "hmga-1956-s6": ["ಮಗುವಿನ ಜನನ ದಾಖಲೆ", "ಮಗುವಿನ ಶಾಲೆಯ ದಾಖಲೆಗಳು"],
    "welfare-principle": ["ಮಗುವಿನ ಜನನ ದಾಖಲೆ", "ಮಗುವಿನ ಶಾಲೆಯ ದಾಖಲೆಗಳು"],
    "hma-26": ["ಮಗುವಿನ ಜನನ ದಾಖಲೆ", "ಮಗುವಿನ ಶಾಲೆಯ ದಾಖಲೆಗಳು"],
    "hma-27": ["ಬಂಗಾರ ಮತ್ತು ಉಡುಗೊರೆಗಳ ಪಟ್ಟಿ", "ಫೋಟೋಗಳು", "ಲಿಖಿತವಾಗಿ ಕೇಳಿದ ಪ್ರತಿಯ ಪ್ರತಿ"],
    "bns-316": ["ಬಂಗಾರ ಮತ್ತು ಉಡುಗೊರೆಗಳ ಪಟ್ಟಿ", "ಫೋಟೋಗಳು", "ಲಿಖಿತವಾಗಿ ಕೇಳಿದ ಪ್ರತಿಯ ಪ್ರತಿ"],
    "pwdva-17": ["ಹಂಚಿದ ಮನೆಯಲ್ಲಿ ವಾಸಿಸುತ್ತಿದ್ದುದರ ಪುರಾವೆ"],
    "pwdva-19": ["ಹಂಚಿದ ಮನೆಯಲ್ಲಿ ವಾಸಿಸುತ್ತಿದ್ದುದರ ಪುರಾವೆ"],
    "pwdva-18": ["ವೈದ್ಯಕೀಯ ದಾಖಲೆಗಳು", "ಪೊಲೀಸ್ ದೂರು", "ಸಂದೇಶಗಳು ಮತ್ತು ಇತರ ದಾಖಲೆಗಳು"],
    "pwdva-22": ["ವೈದ್ಯಕೀಯ ದಾಖಲೆಗಳು", "ಪೊಲೀಸ್ ದೂರು", "ಸಂದೇಶಗಳು ಮತ್ತು ಇತರ ದಾಖಲೆಗಳು"],
    "hma-13": ["ಮದುವೆ ಪುರಾವೆ"],
    "hma-13b": ["ಮದುವೆ ಪುರಾವೆ"],
    "hma-9": ["ಮದುವೆ ಪುರಾವೆ"],
    "births-deaths-act-1969": ["ಆಸ್ಪತ್ರೆಯ ದಾಖಲೆ ಅಥವಾ ಜನನದ ಬೇರೆ ಪುರಾವೆ"],
}

CHECKLIST_CLOSING_KN = (
    "ನಿಮ್ಮ ಬಳಿ ಇರುವ ದಾಖಲೆಗಳನ್ನು ಕೊಡಿ. ಯಾವುದಾದರೂ ದಾಖಲೆ ಇಲ್ಲದಿದ್ದರೆ, ಅದು ಇಲ್ಲ ಎಂದು ಹೇಳಿ."
)


def document_checklist_kn(kept_ids: Sequence[str], facts: Optional[Dict[str, Any]] = None) -> str:
    """Deterministic per-section document checklist (template-locked).

    Never names salary slips / pay slips (Forbidden #9 trap — see module
    docstring). School-fee records appear ONLY when school_fees_fact is True.
    DRAFT — NEEDS P2.1 verification.
    """
    facts = _normalize_kn_facts(facts)
    items: List[str] = []
    for sid in kept_ids or []:
        for item in _CHECKLIST_ITEMS_KN.get(sid, []):
            if item not in items:
                items.append(item)
    if facts.get("school_fees_fact") and facts.get("child_fact"):
        fee_item = "ಮಗುವಿನ ಶಾಲಾ ಶುಲ್ಕದ ದಾಖಲೆಗಳು"
        if fee_item not in items:
            items.append(fee_item)
    if not items:
        return ""
    lines = ["ಮುಂದಿನ ಹಂತಗಳು ಮತ್ತು ದಾಖಲೆಗಳು."]
    lines.extend(f"- {item}." for item in items)
    lines.append(CHECKLIST_CLOSING_KN)
    return "\n".join(lines)


def readability_check_kn(prose: str) -> Dict[str, Any]:
    """P6-2 readability audit for Kannada prose.

    Splits sentences on "." / "।", words on whitespace. Pass bar: average
    sentence length <= 22 words and zero question marks.
    """
    sentences = [s.strip() for s in re.split(r"[.।]", prose or "") if s.strip()]
    word_counts = [len(s.split()) for s in sentences]
    avg = round(sum(word_counts) / len(word_counts), 2) if word_counts else 0.0
    return {
        "sentences": len(sentences),
        "avg_sentence_words": avg,
        "max_sentence_words": max(word_counts) if word_counts else 0,
        "has_question_mark": "?" in (prose or ""),
        "passes": bool(sentences) and avg <= 22 and "?" not in (prose or ""),
    }


# ---------------------------------------------------------------------------
# Kannada parity verifier: Frozen Forbidden Items 1-9 + Additions A-E
# ---------------------------------------------------------------------------
# Kannada statutory patterns, ordered so 144(3) is matched before plain 144
# and 13B before plain 13. Each pattern is (regex, section_id).
SECTION_PATTERNS_KN: List[Tuple[str, str]] = [
    (r"ಸೆಕ್ಷನ್ 144\(3\)", "bnss-144-3"),
    (r"ಸೆಕ್ಷನ್ 146\b.{0,60}ಭಾರತೀಯ ನಾಗರಿಕ ಸುರಕ್ಷಾ ಸಂಹಿತೆ|ಭಾರತೀಯ ನಾಗರಿಕ ಸುರಕ್ಷಾ ಸಂಹಿತೆ.{0,60}ಸೆಕ್ಷನ್ 146\b", "bnss-146"),
    (r"ಸೆಕ್ಷನ್ 144(?!\().{0,60}ಭಾರತೀಯ ನಾಗರಿಕ ಸುರಕ್ಷಾ ಸಂಹಿತೆ|ಭಾರತೀಯ ನಾಗರಿಕ ಸುರಕ್ಷಾ ಸಂಹಿತೆ.{0,60}ಸೆಕ್ಷನ್ 144(?!\()", "bnss-144"),
    (r"ಬಿಎನ್ಎಸ್ಎಸ್ ಸೆಕ್ಷನ್ 144\(3\)", "bnss-144-3"),
    (r"ಬಿಎನ್ಎಸ್ಎಸ್ ಸೆಕ್ಷನ್ 144(?!\()", "bnss-144"),
    (r"ಸೆಕ್ಷನ್ 20\b.{0,60}ಕೌಟುಂಬಿಕ ದೌರ್ಜನ್ಯ ತಡೆ ಕಾಯ್ದೆ|ಕೌಟುಂಬಿಕ ದೌರ್ಜನ್ಯ ತಡೆ ಕಾಯ್ದೆ.{0,60}ಸೆಕ್ಷನ್ 20\b", "pwdva-20"),
    (r"ಸೆಕ್ಷನ್ 17\b.{0,60}ಕೌಟುಂಬಿಕ ದೌರ್ಜನ್ಯ ತಡೆ ಕಾಯ್ದೆ|ಕೌಟುಂಬಿಕ ದೌರ್ಜನ್ಯ ತಡೆ ಕಾಯ್ದೆ.{0,60}ಸೆಕ್ಷನ್ 17\b", "pwdva-17"),
    (r"ಸೆಕ್ಷನ್ 18\b.{0,60}ಕೌಟುಂಬಿಕ ದೌರ್ಜನ್ಯ ತಡೆ ಕಾಯ್ದೆ|ಕೌಟುಂಬಿಕ ದೌರ್ಜನ್ಯ ತಡೆ ಕಾಯ್ದೆ.{0,60}ಸೆಕ್ಷನ್ 18\b", "pwdva-18"),
    (r"ಸೆಕ್ಷನ್ 19\b.{0,60}ಕೌಟುಂಬಿಕ ದೌರ್ಜನ್ಯ ತಡೆ ಕಾಯ್ದೆ|ಕೌಟುಂಬಿಕ ದೌರ್ಜನ್ಯ ತಡೆ ಕಾಯ್ದೆ.{0,60}ಸೆಕ್ಷನ್ 19\b", "pwdva-19"),
    (r"ಸೆಕ್ಷನ್ 22\b.{0,60}ಕೌಟುಂಬಿಕ ದೌರ್ಜನ್ಯ ತಡೆ ಕಾಯ್ದೆ|ಕೌಟುಂಬಿಕ ದೌರ್ಜನ್ಯ ತಡೆ ಕಾಯ್ದೆ.{0,60}ಸೆಕ್ಷನ್ 22\b", "pwdva-22"),
    (r"ಸೆಕ್ಷನ್ 24\b.{0,60}ಹಿಂದೂ ವಿವಾಹ ಕಾಯ್ದೆ|ಹಿಂದೂ ವಿವಾಹ ಕಾಯ್ದೆ.{0,60}ಸೆಕ್ಷನ್ 24\b", "hma-24"),
    (r"ಸೆಕ್ಷನ್ 25\b.{0,60}ಹಿಂದೂ ವಿವಾಹ ಕಾಯ್ದೆ|ಹಿಂದೂ ವಿವಾಹ ಕಾಯ್ದೆ.{0,60}ಸೆಕ್ಷನ್ 25\b", "hma-25"),
    (r"ಸೆಕ್ಷನ್ 26\b.{0,60}ಹಿಂದೂ ವಿವಾಹ ಕಾಯ್ದೆ|ಹಿಂದೂ ವಿವಾಹ ಕಾಯ್ದೆ.{0,60}ಸೆಕ್ಷನ್ 26\b", "hma-26"),
    (r"ಸೆಕ್ಷನ್ 27\b.{0,60}ಹಿಂದೂ ವಿವಾಹ ಕಾಯ್ದೆ|ಹಿಂದೂ ವಿವಾಹ ಕಾಯ್ದೆ.{0,60}ಸೆಕ್ಷನ್ 27\b", "hma-27"),
    (r"ಸೆಕ್ಷನ್ 13ಬಿ|ಸೆಕ್ಷನ್ 13B\b", "hma-13b"),
    (r"ಸೆಕ್ಷನ್ 13(?![ಬಿB\d]).{0,60}ಹಿಂದೂ ವಿವಾಹ ಕಾಯ್ದೆ|ಹಿಂದೂ ವಿವಾಹ ಕಾಯ್ದೆ.{0,60}ಸೆಕ್ಷನ್ 13(?![ಬಿB\d])", "hma-13"),
    (r"ಸೆಕ್ಷನ್ 9\b.{0,60}ಹಿಂದೂ ವಿವಾಹ ಕಾಯ್ದೆ|ಹಿಂದೂ ವಿವಾಹ ಕಾಯ್ದೆ.{0,60}ಸೆಕ್ಷನ್ 9\b", "hma-9"),
    (r"ಸೆಕ್ಷನ್ 316\b.{0,60}ಭಾರತೀಯ ನ್ಯಾಯ ಸಂಹಿತೆ|ಭಾರತೀಯ ನ್ಯಾಯ ಸಂಹಿತೆ.{0,60}ಸೆಕ್ಷನ್ 316\b", "bns-316"),
    (r"ಸೆಕ್ಷನ್ 6\b.{0,60}ಹಿಂದೂ ಅಪ್ರಾಪ್ತ ಮತ್ತು ಪಾಲನಾ ಕಾಯ್ದೆ|ಹಿಂದೂ ಅಪ್ರಾಪ್ತ ಮತ್ತು ಪಾಲನಾ ಕಾಯ್ದೆ.{0,60}ಸೆಕ್ಷನ್ 6\b", "hmga-1956-s6"),
    (r"ಗಾರ್ಡಿಯನ್ಸ್ ಮತ್ತು ವಾರ್ಡ್ಸ್ ಕಾಯ್ದೆ, 1890", "gwa-1890"),
    (r"ಜನನ ಮತ್ತು ಮರಣಗಳ ನೋಂದಣಿ ಕಾಯ್ದೆ, 1969", "births-deaths-act-1969"),
]

AMOUNT_WORDS_KN = (
    r"(?:ಒಂದು|ಎರಡು|ಮೂರು|ನಾಲ್ಕು|ಐದು|ಆರು|ಏಳು|ಎಂಟು|ಒಂಬತ್ತು|ಹತ್ತು|ಹದಿನೈದು|"
    r"ಇಪ್ಪತ್ತು|ಮೂವತ್ತು|ನಲವತ್ತು|ಐವತ್ತು|ಅರವತ್ತು|ಎಪ್ಪತ್ತು|ಎಂಬತ್ತು|ತೊಂಬತ್ತು|ನೂರು)"
    r"\s+(?:ಸಾವಿರ|ಲಕ್ಷ|ಕೋಟಿ)"
)


def prose_forbidden_check_kn(
    prose: str,
    kept_ids: Sequence[str],
    dropped_ids: Sequence[Any],
    facts: Dict[str, Any],
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """Kannada parity of the 9 frozen Fp items + Additions A-E.

    Returns (fp_hits, quality_flags). Mirrors ``laya_prose_v2.
    prose_forbidden_check`` item-for-item, with Kannada traps added:
    #4 "ಬಾಡಿಗೆ ಹಕ್ಕು"/"ಟೆನೆನ್ಸಿ", #9 "ಸಂಬಳದ ಚೀಟಿ"/"ಪೇ ಸ್ಲಿಪ್",
    #8 invented rupee numbers (₹/ರೂ./ಸಾವಿರ/ಲಕ್ಷ + monthly context),
    #5 "?" / court-choice questions, #6 HMA + "ಜನನ ಪ್ರಮಾಣಪತ್ರ",
    #7 Kannada statutory pattern parity against kept_ids.
    """
    facts = _normalize_kn_facts(facts)
    hits: List[Dict[str, Any]] = []
    flags: List[Dict[str, Any]] = []
    kept = set(kept_ids or [])
    dropped = {d[0] if isinstance(d, (list, tuple)) else d for d in (dropped_ids or [])}

    # 1+2. Any precedent / case citation (Kannada + Latin forms).
    for pat in (
        r"ರಾಜನೇಶ್",
        r"ಸತೀಶ್ ಚಂದರ್ ಅಹುಜಾ",
        r"\b[A-Z][a-z]+ v\. [A-Z][a-z]+\b",
        r"\bAIR \d{4}\b",
        r"\bSCC\b",
        r"\(\d{4}\) \d+ SCC",
    ):
        if re.search(pat, prose):
            item = 2 if ("ಸತೀಶ್" in pat or "Satish" in pat) else 1
            hits.append({"item": item, "detail": f"precedent/case citation matched {pat!r}"})
            break

    # 3. HMA 13 / 13B in prose without divorce_asked (or pending for 13) /
    #    mutual_consent for 13B.
    if re.search(r"ಸೆಕ್ಷನ್ 13(?![ಬಿB\d]).{0,60}ಹಿಂದೂ ವಿವಾಹ ಕಾಯ್ದೆ|ಹಿಂದೂ ವಿವಾಹ ಕಾಯ್ದೆ.{0,60}ಸೆಕ್ಷನ್ 13(?![ಬಿB\d])", prose):
        if (not (facts.get("divorce_asked") or facts.get("proceeding_pending_hma") or facts.get("proceeding_pending"))) or ("hma-13" not in kept):
            hits.append({"item": 3, "detail": "HMA 13 in Kannada prose without divorce_asked/pending or not kept"})
    if re.search(r"ಸೆಕ್ಷನ್ 13[ಬಿB]\b", prose):
        if not (facts.get("divorce_asked") and facts.get("mutual_consent") and "hma-13b" in kept):
            hits.append({"item": 3, "detail": "HMA 13B in Kannada prose without mutual_consent + divorce_asked + kept"})

    # 4. Tenancy / tenant rights label for residence (Kannada + Latin).
    if re.search(r"ಬಾಡಿಗೆ ಹಕ್ಕು|ಟೆನೆನ್ಸಿ|tenancy rights?|tenant rights?", prose, re.I):
        hits.append({"item": 4, "detail": '"ಬಾಡಿಗೆ ಹಕ್ಕು" / "ಟೆನೆನ್ಸಿ" / "tenancy rights" in prose'})

    # 5. User asked to pick the court (any '?' or pick-a-court phrasing).
    if "?" in prose:
        hits.append({"item": 5, "detail": "question mark in generated prose"})
    if re.search(
        r"ಯಾವ ನ್ಯಾಯಾಲಯಕ್ಕೆ ಹೋಗಬೇಕು|ನ್ಯಾಯಾಲಯವನ್ನು ಆರಿಸಿ|ನ್ಯಾಯಾಲಯವನ್ನು ಆಯ್ಕೆ ಮಾಡಿ|"
        r"ಯಾವ ನ್ಯಾಯಾಲಯ ಎಂದು ನಿರ್ಧರಿಸಿ|which court (do you|should you|will you|do I)|"
        r"choose (a|the) court|pick (a|the) court|decide which court",
        prose,
        re.I,
    ):
        hits.append({"item": 5, "detail": "prose asks user to pick the court"})

    # 6. Birth certificate under HMA or missing 1969 Act.
    if re.search(r"ಜನನ ಪ್ರಮಾಣಪತ್ರ|birth certificate", prose, re.I):
        if re.search(
            r"ಜನನ ಪ್ರಮಾಣಪತ್ರ.{0,100}ಹಿಂದೂ ವಿವಾಹ ಕಾಯ್ದೆ|ಹಿಂದೂ ವಿವಾಹ ಕಾಯ್ದೆ.{0,100}ಜನನ ಪ್ರಮಾಣಪತ್ರ|"
            r"birth certificate.{0,100}Hindu Marriage Act|Hindu Marriage Act.{0,100}birth certificate",
            prose,
            re.I,
        ):
            hits.append({"item": 6, "detail": "birth certificate linked to HMA"})
        if "births-deaths-act-1969" in kept and "ಜನನ ಮತ್ತು ಮರಣಗಳ ನೋಂದಣಿ ಕಾಯ್ದೆ, 1969" not in prose:
            hits.append({"item": 6, "detail": "birth-certificate paragraph missing the 1969 Act"})

    # 7. Cited section not in kept_ids (or explicitly dropped / gated by D2).
    cited = set()
    for pat, sid in SECTION_PATTERNS_KN:
        if re.search(pat, prose):
            cited.add(sid)
    for sid in sorted(cited - kept):
        hits.append({"item": 7, "detail": f"prose cites {sid} which is not in kept_ids"})
    for sid in sorted(cited & dropped):
        hits.append({"item": 7, "detail": f"prose cites {sid} which Stage 2 dropped"})

    # 8. Maintenance amount stated as a number (Kannada + Latin forms).
    for pat in (
        r"₹\s?[\d][\d,]*",
        r"ರೂ\.?\s?[\d][\d,]*",
        r"[\d][\d,]*\s*(?:ರೂಪಾಯಿ|ರೂ\.?)",
        r"\b[\d][\d,]*\s*(?:ಪ್ರತಿ ತಿಂಗಳು|ತಿಂಗಳಿಗೆ|ಮಾಸಿಕ)\b",
        r"[\d][\d,]*\s*(?:ಸಾವಿರ|ಲಕ್ಷ|ಕೋಟಿ)",
        AMOUNT_WORDS_KN,
    ):
        if re.search(pat, prose, re.I):
            hits.append({"item": 8, "detail": f"maintenance amount pattern matched {pat!r}"})
            break

    # 9. Salary slips demanded (Kannada + Latin forms).
    if re.search(r"ಸಂಬಳದ ಚೀಟಿ|ಸಂಬಳ ಚೀಟಿ|ಪೇ ಸ್ಲಿಪ್|ಪೇಸ್ಲಿಪ್|salary slips?|pay slips?|payslips?", prose, re.I):
        hits.append({"item": 9, "detail": '"ಸಂಬಳದ ಚೀಟಿ" / "ಪೇ ಸ್ಲಿಪ್" / "salary slips" in prose'})
    if re.search(
        r"(ಆದಾಯದ ಪುರಾವೆ|ಆದಾಯದ ದಾಖಲೆ).{0,30}(ಬೇಕು|ತರಬೇಕು|ಕೊಡಬೇಕು|ಕಡ್ಡಾಯ)|"
        r"(ಬೇಕು|ಕಡ್ಡಾಯ|ತರಬೇಕು|ಕೊಡಬೇಕು).{0,30}(ಆದಾಯದ ಪುರಾವೆ|ಆದಾಯದ ದಾಖಲೆ)|"
        r"(must|need to|have to|should|required|bring|provide|submit|give|produce|attach)"
        r".{0,40}(salary|income proof|income document)",
        prose,
        re.I,
    ):
        hits.append({"item": 9, "detail": "prose demands income proof as an obligation"})

    # --- Structural Quality Additions (A-E), Kannada parity ---
    if "ಹಂಚಿದ ಮನೆಯಲ್ಲಿ ವಾಸಿಸುವ ಹಕ್ಕು" in prose and not (kept & {"pwdva-17", "pwdva-19"}):
        flags.append({"check": "A-residence-base-without-section", "detail": "residence-right sentence without pwdva-17/19"})
    if not facts.get("child_fact") and re.search(r"\bನಿಮ್ಮ ಮಗು\b", prose):
        flags.append({"check": "B-child-without-fact", "detail": '"ನಿಮ್ಮ ಮಗು" in prose with child_fact=False'})
    if not facts.get("school_fees_fact") and re.search(r"ಶಾಲಾ ಶುಲ್ಕ", prose):
        flags.append({"check": "B-school-fees-without-fact", "detail": '"ಶಾಲಾ ಶುಲ್ಕ" in prose with school_fees_fact=False'})
    if "hma-27" not in kept and re.search(r"ಸೆಕ್ಷನ್ 27\b|ಎಚ್ಎಂಎ ಸೆಕ್ಷನ್ 27", prose):
        flags.append({"check": "C-pre-d1a-hma27-leak", "detail": "HMA 27 cited in prose without hma-27 in kept_ids"})
    if facts.get("claimant_sex") == "male" or facts.get("claimant_role") == "parent":
        if re.search(r"ಪತ್ನಿಯಾಗಿ|ನಿಮ್ಮ ಗಂಡನ", prose):
            check = "E-claimant-role-mismatch" if facts.get("claimant_role") == "parent" else "E-claimant-sex-mismatch"
            flags.append({"check": check, "detail": "wife/husband wording used for male/parent claimant"})

    return hits, flags


# ---------------------------------------------------------------------------
# CPU self-test (no torch, no network, no test-bank access)
# ---------------------------------------------------------------------------
def run_self_test() -> Dict[str, Any]:
    """Render every template + every escalation kind, assert 0 forbidden hits
    and 0 quality flags on our own outputs, 0 '?' anywhere, avg sentence
    length <= 22 words, and DRAFT marking on every template and every result.
    """
    base_facts: Dict[str, Any] = {
        "divorce_asked": True,
        "mutual_consent": True,
        "proceeding_pending_hma": True,
        "proceeding_pending": True,
        "being_filed": False,
        "decree": True,
        "demand_made": True,
        "violence": True,
        "residence_claim": True,
        "child_fact": True,
        "school_fees_fact": True,
        "stridhan_sold": True,
        "stridhan_sold_or_mortgaged": True,
        "joint_property_claim": True,
        "claimant_sex": "female",
        "claimant_role": "spouse",
        "no_dispute_empty": False,
    }
    times_ms: List[float] = []
    rendered = 0

    # 1. Every one of the 20 sections, alone, with all 9 escalation kinds.
    all_kinds = sorted(KNOWN_ESCALATION_KINDS_KN)
    for sid in sorted(KNOWN_SECTIONS_KN):
        rec = {
            "kept_ids": [sid],
            "court_live": ["Family Court"],
            "court_source": "kept",
            "escalation_kinds": all_kinds,
            "in_scope": True,
            "facts": dict(base_facts),
            "lang": "kn",
        }
        res = render_prose_kn(rec, dict(base_facts), include_forum_note=True, include_checklist=True)
        times_ms.append(res["prose_render_ms"])
        rendered += 1
        assert res["status"] == "ok", f"{sid}: status {res['status']}"
        assert res["draft"] is True and res["p2_1_verified"] is False, f"{sid}: draft marking missing"
        assert "?" not in res["prose"], f"{sid}: '?' in rendered prose"
        assert DRAFT_NOTICE_KN.split(".")[0] in res["prose"], f"{sid}: draft banner missing"
        hits, flags = prose_forbidden_check_kn(res["prose"], [sid], [], base_facts)
        assert not hits, f"{sid}: Fp hits {hits}\n{res['prose']}"
        assert not flags, f"{sid}: quality flags {flags}\n{res['prose']}"
        read = readability_check_kn(res["prose"])
        assert read["passes"], f"{sid}: readability fail {read}"

    # 2. Role variants: male claimant, parent claimant, no-child / no-fees.
    for variant_facts in (
        {**base_facts, "claimant_sex": "male"},
        {**base_facts, "claimant_role": "parent"},
        {**base_facts, "child_fact": False, "school_fees_fact": False},
        {**base_facts, "divorce_asked": False, "mutual_consent": False, "proceeding_pending_hma": False, "proceeding_pending": False},
    ):
        rec = {
            "kept_ids": ["bnss-144", "hma-13b", "hma-26", "bns-316", "pwdva-18"],
            "court_live": ["Family Court", "Magistrate"],
            "court_source": "kept",
            "escalation_kinds": all_kinds,
            "in_scope": True,
            "facts": dict(variant_facts),
            "lang": "kn",
        }
        res = render_prose_kn(rec, dict(variant_facts))
        times_ms.append(res["prose_render_ms"])
        rendered += 1
        hits, flags = prose_forbidden_check_kn(
            res["prose"], rec["kept_ids"], [], variant_facts
        )
        assert not hits, f"variant {variant_facts}: Fp hits {hits}\n{res['prose']}"
        assert not flags, f"variant {variant_facts}: quality flags {flags}\n{res['prose']}"
        assert "?" not in res["prose"]

    # 3. Branches: out-of-scope, empty-kept, no-dispute, unknown id, dispatcher.
    r_oos = render_prose_kn({"kept_ids": [], "in_scope": False, "facts": {}, "lang": "kn"})
    assert OUT_OF_SCOPE_LINE_KN in r_oos["prose"] and "?" not in r_oos["prose"]
    r_empty = render_prose_kn(
        {"kept_ids": [], "in_scope": True, "facts": {"no_dispute_empty": True}, "lang": "kn"}
    )
    assert r_empty["status"] == "ok" and "?" not in r_empty["prose"]
    r_unk = render_prose_kn({"kept_ids": ["unknown-sec-99"], "in_scope": True, "facts": {}, "lang": "kn"})
    assert r_unk["status"] == "error" and "unknown-sec-99" not in r_unk["prose"]
    r_disp = render_prose_localized(
        {"kept_ids": ["bnss-144"], "in_scope": True, "facts": dict(base_facts), "lang": "kn"},
        dict(base_facts),
    )
    assert r_disp.get("lang") == "kn" and r_disp["status"] == "ok"
    rendered += 4

    # 4. Draft marking on every template entry.
    assert len(KNOWN_SECTIONS_KN) == 20, f"expected 20 sections, got {len(KNOWN_SECTIONS_KN)}"
    assert set(SECTION_RENDERERS_KN) == set(KNOWN_SECTIONS_KN)
    assert len(TEMPLATE_COVERAGE_KN) == 20
    assert all("DRAFT" in v and "P2.1" in v for v in TEMPLATE_COVERAGE_KN.values())
    assert len(KNOWN_ESCALATION_KINDS_KN) == 9

    return {
        "sections_rendered": len(KNOWN_SECTIONS_KN),
        "escalation_kinds": len(KNOWN_ESCALATION_KINDS_KN),
        "renders_checked": rendered,
        "fp_total": 0,
        "quality_flags_total": 0,
        "question_marks_total": 0,
        "render_ms_mean": round(sum(times_ms) / len(times_ms), 4) if times_ms else 0.0,
        "render_ms_max": round(max(times_ms), 4) if times_ms else 0.0,
    }


if __name__ == "__main__":
    summary = run_self_test()
    print(
        f"KANNADA PROSE SELF-TEST PASS: {summary['sections_rendered']}/20 sections, "
        f"{summary['escalation_kinds']}/9 kinds, {summary['renders_checked']} renders, "
        f"Fp={summary['fp_total']}, quality_flags={summary['quality_flags_total']}, "
        f"question_marks={summary['question_marks_total']}, "
        f"mean={summary['render_ms_mean']}ms, max={summary['render_ms_max']}ms"
    )
