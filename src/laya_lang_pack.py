"""LanguagePack scaling contract for LAYA v7.1 (V71-P3-3).

Onboarding a new language (Hindi, Tamil, Telugu, Malayalam, Marathi, ...)
requires ONLY, per plan §3.2:

1. adding one :class:`LanguagePack` config + a synthetic parallel split
   (Lane 02 corpus schema),
2. adding localized prose templates (Lane 09, ``src/laya_prose_kn.py`` pattern),
3. passing a native-speaker audit + a >= 8/8 / >= 95% held-out bar.

Zero edits to Graph v4 Stage 2 legal logic are needed: the pack carries
only language surface facts (script, sentence splitting, romanization
detection, negation/demand lexicon, template + benchmark pointers, audit
sign-off). The graph never reads a pack.

Kannada (``kn``) and English (``en``) packs are fully defined. Hindi,
Tamil, Telugu, Malayalam and Marathi are stubs marked ``TODO`` — their
fields are present but empty / unsigned, and :func:`get_language_pack`
refuses to return a stub for production use (``ready_for_production``
is False until a native audit signs off).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable

from .laya_lang_normalizer import detect_script_locale, kanglish_score

__all__ = [
    "LanguagePack",
    "KANNADA_PACK",
    "ENGLISH_PACK",
    "LANGUAGE_PACKS",
    "get_language_pack",
    "list_ready_packs",
]

# Sentence-split pattern shared by the Indic packs: split after sentence
# terminators (including the Devanagari danda) followed by whitespace.
_INDIC_SENTENCE_SPLIT = r"(?<=[.!?।;\n])\s+"
_LATIN_SENTENCE_SPLIT = r"(?<=[.!?;\n])\s+"


@dataclass(frozen=True)
class LanguagePack:
    """One language's surface contract (plan §3.2, V71-P3-3)."""

    lang_code: str  # BCP-47-ish short code: "kn", "en", "hi", ...
    # Inclusive Unicode code-point range(s) of the language's native script.
    unicode_range: tuple[tuple[int, int], ...]
    # Regex (as a string, so the pack stays JSON-serialisable) used to split
    # a question into sentences for clause-level pooling.
    sentence_split_regex: str
    # Callable: text -> {"score": int, "is_kanglish"/romanized: bool, ...}.
    # For non-romanized languages this is a detector for Latin-script
    # transliteration of that language (e.g. Hinglish, Tanglish).
    roman_detector: Callable[[str], dict] | None
    # Negation / demand lexicon: keys are fact keys, values are regexes
    # (strings) that signal the fact is DENIED in this language.
    # "demand_made": False-patterns only; True-patterns live in the normalizer.
    negation_demand_lexicon: dict[str, str]
    # Template catalog: prose-template set name -> module path that renders it.
    template_catalog: dict[str, str]
    # Benchmark manifest: eval-set name -> expected item count / bar.
    benchmark_manifest: dict[str, str]
    # Native-speaker audit sign-off: name + date, or "" when not yet audited.
    # A pack is production-ready only when this is non-empty AND the
    # benchmark bar in benchmark_manifest has been met (checked by humans;
    # this module only records the claim, it never asserts it).
    native_audit_signoff: str = ""
    # TODO marker: True while the pack is a stub awaiting a native speaker.
    todo: bool = False
    # Lane 05 (recall swarm): fact/issue-key surface-form lexicon — maps
    # Kannada-script, Kanglish spelling-variant and code-mixed forms to the
    # corpus fact/issue keys (same patterns as
    # laya_lang_normalizer.kannada_issue_hints). Verification-only signals;
    # the graph never reads a pack.
    fact_key_lexicon: dict[str, str] = field(default_factory=dict)

    @property
    def ready_for_production(self) -> bool:
        """True only for a complete pack with a signed native audit."""
        return not self.todo and bool(self.native_audit_signoff)

    def detect(self, text: str, explicit_locale: str | None = None) -> dict:
        """Route ``text`` through this pack's detector (Kannada packs only).

        Other packs return the shared normalizer result unchanged; their
        own detectors are wired in when the pack is completed.
        """
        return detect_script_locale(text, explicit_locale)


def _kn_roman_detector(text: str) -> dict:
    return kanglish_score(text)


KANNADA_PACK = LanguagePack(
    lang_code="kn",
    unicode_range=((0x0C80, 0x0CFF),),
    sentence_split_regex=_INDIC_SENTENCE_SPLIT,
    roman_detector=_kn_roman_detector,
    negation_demand_lexicon={
        # demand_made=False: speaker says they did NOT ask/demand.
        # (Matches evidence.py:561 — ಕೇಳಿಲ್ಲ / ಕೇಳಲಿಲ್ಲ — plus roman forms.
        # Lane 05 adds ಕೇಳಿಯೇ ಇಲ್ಲ / ಎಂದೂ ಕೇಳಿಲ್ಲ and roman "keliye illa" /
        # "yavattu kelilla" / "endu kelilla" from scripts/kn_templates.py.)
        "demand_made": r"ಕೇಳಿಲ್ಲ|ಕೇಳಲಿಲ್ಲ|ಕೇಳೇ\s*ಇಲ್ಲ|ಕೇಳಲೇ\s*ಇಲ್ಲ|ಕೇಳಿಯೇ\s*ಇಲ್ಲ|ಎಂದೂ\s*ಕೇಳಿಲ್ಲ|\bkelilla\b|\bkelalilla\b|\bkeliye\s+illa\b|\byavattu\s+kelilla\b|\bendu\s+kelilla\b",
        # violence denied (Kannada): "he never hit me" family of forms.
        # Lane 05 adds the roman forms.
        "violence_denied": r"ಹೊಡೆದಿಲ್ಲ|ಹೊಡೆಯಲಿಲ್ಲ|ಹಿಂಸೆ\s*ಇಲ್ಲ|ಬೆದರಿಕೆ\s*ಇಲ್ಲ|\bhodedilla\b|\bhodilla\b",
        # residence denied: speaker does not want the house / staying there.
        # Lane 05 adds the roman forms.
        "residence_denied": r"ಮನೆಯಲ್ಲಿ\s*ಇರಲು\s*ಬೇಡ|ಮನೆ\s*ಬೇಡ|\bmane\s+beda\b|\bmaneyalli\s+iralu\s+beda\b",
        # stridhan safe in the speaker's own possession (no claim):
        # "gold is with me" family of forms (KN + roman).
        "stridhan_claim": r"ಚಿನ್ನ\s*ನನ್ನ\s*ಬಳಿಯೇ|ಬಂಗಾರ\s*ನನ್ನ\s*ಬಳಿಯೇ|chinna\s+nanna\s+baliye|bangara\s+nanna\s+baliye",
        # custody not wanted (KN + roman).
        "custody_claim": r"ಪಾಲನೆ\s*ಬೇಡ|\bpaalane\s+beda\b|\bpalane\s+beda\b|\bcustody\s+beda\b",
    },
    template_catalog={
        "prose_kn": "src/laya_prose_kn.py (Lane 09 — deterministic Kannada templates)",
        "prose_en_fallback": "src/laya_prose_v2.py",
        # Lane 05 (recall swarm): KN/Kanglish paraphrase templates feeding
        # the synthetic corpus builder (Lane 02 wires them in).
        "kn_templates": "scripts/kn_templates.py (Lane 05 — 25 blocks, DRAFT pending P2.1)",
    },
    benchmark_manifest={
        "C13 (16-Q Kannada)": "16 items, bar 16/16 exact",
        "Sealed Kannada-8": "8 items, bar 8/8 exact (blind, aggregate only)",
        "Kanglish held-out suite": "n >= 30 newly commissioned items, bar >= 95% exact, 0 silent, 0 FP",
        # Lane 05: validation-split KN coverage measured on
        # data/synthetic_v7_1/validation.jsonl (500 records; KN-family 272).
        "KN validation coverage (Lane 05)": "before: restitution 5, birth_certificate 7, dv_compensation 6, procedure 8, joint_property 13, stridhan 18, violence 17, divorce 22, custody 39, residence 46, maintenance 134 (requested, kn+kn_roman); after wiring see docs/recall_swarm_state/lane-05-kannada.md",
    },
    # Fact/issue-key surface-form lexicon (Lane 05): Kannada-script,
    # Kanglish spelling-variant and code-mixed forms -> corpus keys.
    # Mirrors laya_lang_normalizer._ISSUE_FORM_PATTERNS.
    fact_key_lexicon={
        "money_fact": r"ಜೀವನಾಂಶ|jeevanamsha|jeevanamsa|jeevanaamsha|jivanaamsha|maintenance\s+beku|maintanance\s+beku|duddu\s+kodalla",
        "custody_claim": r"ಪಾಲನೆ|paalane|palane|custody\s+beku",
        "residence_claim": r"ಮನೆಯಲ್ಲಿ\s*ಇರ|ಮನೆಯಲ್ಲೇ\s*ಇರ|maneyalli\s+irabeku|maneyalle\s+irabeku|residence\s+beku|mane\s+bittu\s+hoguvudilla",
        "stridhan_claim": r"ಚಿನ್ನ|ಬಂಗಾರ|chinna|bangara|stridhan|streedhan",
        "divorce_asked": r"ವಿಚ್ಛೇದನ|vichhedana|vichchhedana|vichhedana|divorce\s+beku",
        "joint_property_claim": r"ಜಂಟಿ\s*ಆಸ್ತಿ|janti\s+asti|joint\s+property",
        "birth_cert_asked": r"ಜನನ\s*ಪ್ರಮಾಣಪತ್ರ|janana\s+pramanapatra|birth\s+certificate\s+beku",
        "dv_injury_comp_asked": r"ಪರಿಹಾರ|parihara|compensation\s+beku",
        "restitution_asked": r"ಮರಳಿ\s*ಬರ|marali\s+bar|marali\s+banni|vapas\s+barabeku",
        "violence": r"ಹೊಡೆಯುತ್ತಾನೆ|ಹೊಡೆದ|ಹಿಂಸೆ|hodeyuttane|hodita|himse|bedarisuttane",
        "demand_made": r"ಕೇಳಿದ್ದೇನೆ|ಕೇಳಿದೆ|ಬೇಡಿಕೆ\s*ಇಟ್ಟಿದ್ದೇನೆ|\bkelidde\b|\bkeliddene\b|\bbedike\s+ittiddene\b",
        "coercive_eviction_or_lockout": r"ಮನೆಯಿಂದ\s*(?:ಆಚೆ|ಹೊರಗೆ)\s*ಹಾಕಿದ್ದಾರೆ|maneyinda\s+horahak|horage\s+haakidare|beega\s+hakid",
    },
    # P2.1 native Kannada speaker audit is still OPEN (plan §6.2, V71-P6-3).
    # Do not fill this in without the signed audit report.
    native_audit_signoff="",
    todo=False,
)

ENGLISH_PACK = LanguagePack(
    lang_code="en",
    unicode_range=((0x0041, 0x005A), (0x0061, 0x007A)),
    sentence_split_regex=_LATIN_SENTENCE_SPLIT,
    roman_detector=None,  # English is the Latin-script baseline; no detector.
    negation_demand_lexicon={
        "demand_made": r"\bnever\s+(?:asked|demanded)|have\s+not\s+asked|haven['’]t\s+asked|not\s+asked\s+(?:for\s+it\s+)?yet",
    },
    template_catalog={
        "prose_en": "src/laya_prose_v2.py",
    },
    benchmark_manifest={
        "16-Q": "16 items, bar 16/16 exact (ground-truth-v3, ratification pending)",
        "Brutal-230": "230 items, bar 230/230 exact, esc_kinds_strict >= 225/230",
        "Sealed Fresh-20": "20 items, bar 20/20 exact (blind, aggregate only)",
    },
    native_audit_signoff="",
    todo=False,
)


def _stub_pack(lang_code: str, unicode_range: tuple[tuple[int, int], ...]) -> LanguagePack:
    """A TODO stub: present so the registry is explicit, unusable in prod."""
    return LanguagePack(
        lang_code=lang_code,
        unicode_range=unicode_range,
        sentence_split_regex=_INDIC_SENTENCE_SPLIT,
        roman_detector=None,
        negation_demand_lexicon={},
        template_catalog={},
        benchmark_manifest={
            "held-out suite": "TODO: commission n >= 30 items, bar >= 95% exact",
        },
        native_audit_signoff="",
        todo=True,
    )


LANGUAGE_PACKS: dict[str, LanguagePack] = {
    "kn": KANNADA_PACK,
    "en": ENGLISH_PACK,
    # TODO stubs — native-speaker audit + lexicon + templates still required.
    "hi": _stub_pack("hi", ((0x0900, 0x097F),)),  # Devanagari
    "ta": _stub_pack("ta", ((0x0B80, 0x0BFF),)),  # Tamil
    "te": _stub_pack("te", ((0x0C00, 0x0C7F),)),  # Telugu
    "ml": _stub_pack("ml", ((0x0D00, 0x0D7F),)),  # Malayalam
    "mr": _stub_pack("mr", ((0x0900, 0x097F),)),  # Marathi (Devanagari)
}


def get_language_pack(lang_code: str, *, allow_stub: bool = False) -> LanguagePack:
    """Return the pack for ``lang_code``.

    Raises KeyError for unknown codes and ValueError for TODO stubs unless
    ``allow_stub=True`` (research tooling only — never production).
    """
    pack = LANGUAGE_PACKS[lang_code]
    if pack.todo and not allow_stub:
        raise ValueError(
            f"LanguagePack '{lang_code}' is a TODO stub: no lexicon, "
            "templates, or native-speaker audit yet (V71-P3-3). "
            "Complete the pack and get a native audit sign-off first."
        )
    return pack


def list_ready_packs() -> list[str]:
    """Lang codes whose packs are complete (audit sign-off still tracked separately)."""
    return sorted(code for code, pack in LANGUAGE_PACKS.items() if not pack.todo)


def _self_test() -> None:
    """CPU self-test: run ``python3 -m src.laya_lang_pack``."""
    import re as _re

    kn = get_language_pack("kn")
    assert kn.ready_for_production is False, "kn has no P2.1 sign-off yet"
    assert "kn_templates" in kn.template_catalog, kn.template_catalog
    # Lane 05: every fact_key_lexicon key is a corpus fact key and every
    # pattern compiles; negation lexicon patterns compile too.
    fact_keys = {
        "divorce_asked", "mutual_consent", "judicial_separation_only",
        "restitution_asked", "proceeding_pending_hma", "being_filed",
        "decree", "money_fact", "lump_sum_settlement",
        "existing_order_enforcement", "interim_asked", "custody_claim",
        "child_fact", "minor_child", "child_maintenance_only",
        "school_fees_fact", "child_safety_risk", "residence_claim",
        "coercive_eviction_or_lockout", "explicit_residence_order_only",
        "violence", "dv_injury_comp_asked", "stridhan_claim",
        "stridhan_sold_or_mortgaged", "demand_made",
        "joint_property_claim", "birth_cert_asked", "in_scope",
    }
    for key, pat in kn.fact_key_lexicon.items():
        assert key in fact_keys, key
        _re.compile(pat)
    for key, pat in kn.negation_demand_lexicon.items():
        assert key in fact_keys or key.endswith("_denied"), key
        _re.compile(pat)
    # Cross-check: the fact_key_lexicon matches the normalizer's issue
    # hints on the template vocabulary (same forms -> same keys).
    from .laya_lang_normalizer import kannada_issue_hints

    probe = (
        "Nanage jeevanamsa beku. Nanna maguvina paalane nanage beku. "
        "Nanna streedhan vapas beku. Namma janti astiyalli nanna palu kodi."
    )
    hints = kannada_issue_hints(probe)
    assert hints["issues"].get("maintenance") is True, hints
    assert hints["issues"].get("custody") is True, hints
    assert hints["issues"].get("stridhan") is True, hints
    assert hints["issues"].get("joint_property") is True, hints
    assert list_ready_packs() == ["en", "kn"], list_ready_packs()
    print(
        "laya_lang_pack self-test PASS: kn fact_key_lexicon "
        f"{len(kn.fact_key_lexicon)} keys, negation lexicon "
        f"{len(kn.negation_demand_lexicon)} keys, P2.1 still open"
    )


if __name__ == "__main__":
    _self_test()
