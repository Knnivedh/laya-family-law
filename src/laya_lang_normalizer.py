"""Kannada / Kanglish language normalizer for LAYA v7.1 (V71-P3-2).

Pure Python, no torch, no network. Upgrades the v7
``detect_script_locale()`` (``src/laya_v7_extractor.py:68-73``), which only
checked for Kannada Unicode or a ``kn`` locale prefix, so Romanized
Kannada ("Kanglish") routed as English and failed the English extractors
completely.

Public API
----------
``detect_script_locale(raw_text, explicit_locale=None)`` -> dict with keys::

    {"lang": "en" | "kn" | "kn_roman",
     "script": "latin" | "kannada" | "mixed",
     "code_mix_ratio": float}          # 0.0 = single script, (0, 0.5] = mixed

``kannada_fact_hints(text)`` -> verification-only factual span hints
(demand_made / violence / eviction). These are *signals* for Stage 0/1
verification, never a decision on their own.

``kannada_issue_hints(text)`` -> verification-only issue/fact-key hints:
maps Kannada-script, Kanglish spelling-variant and code-mixed surface
forms ("jeevanamsa", "maintenance beku", "paalane", "stridhan vapas
beku", ...) to the same corpus issue/fact keys as the formal forms.

``split_script_segments(text)`` -> [{"script": ..., "text": ...}, ...]
splits mixed-script input cleanly without stripping English tokens.

Zero-false-positive rule (plan §3.2): standard Indian English legal words
(stridhan, streedhan, mangalsutra, panchayat, taluk, ...) must NEVER count
toward a Kanglish score, even when they share a letter pattern with a
Kannada suffix. They are removed before scoring, and a Kanglish verdict
additionally requires >= 1 strong (whole-word) marker or >= 2 distinct
suffix hits, so a single English word ending in "-illa" (vanilla, gorilla)
can never flip the verdict.
"""

from __future__ import annotations

import re

__all__ = [
    "detect_script_locale",
    "kannada_fact_hints",
    "kannada_issue_hints",
    "split_script_segments",
    "is_kanglish",
    "kanglish_score",
    "KANNADA_RANGE",
    "EXEMPT_INDIAN_ENGLISH_WORDS",
]

# Kannada Unicode block (U+0C80–U+0CFF), as in the v7 extractor.
KANNADA_RANGE: tuple[int, int] = (0x0C80, 0x0CFF)
_KANNADA_RE = re.compile(r"[\u0c80-\u0cff]")
_LATIN_LETTER_RE = re.compile(r"[A-Za-z]")
_TOKEN_RE = re.compile(r"[A-Za-z]+")

# ---------------------------------------------------------------------------
# Zero-false-positive exemptions (plan §3.2, verbatim list + close variants).
# These tokens are stripped before ANY Kanglish scoring.
# ---------------------------------------------------------------------------
EXEMPT_INDIAN_ENGLISH_WORDS: frozenset[str] = frozenset(
    {
        "stridhan",
        "streedhan",
        "mangalsutra",
        "panchayat",
        "taluk",
        "taluka",
        "tehsil",
        "zilla",
        "gram",
        "panchayath",
        "sarpanch",
        "patwari",
        "tahsildar",
        "dowry",
        "meher",
        "mehr",
        "nikah",
        "talaq",
        "khula",
        "wakf",
        "waqf",
    }
)

# English words that happen to end in a Kannada-looking suffix. Never scored.
_EXEMPT_ENGLISH_SUFFIX_WORDS: frozenset[str] = frozenset(
    {
        "vanilla",
        "gorilla",
        "villa",
        "armadillo",
        "chinchilla",
        "tortilla",
        "illa",  # bare "illa" alone is not evidence; needs a Kanglish context word
        "manilla",
        "priscilla",
    }
)

# ---------------------------------------------------------------------------
# Kanglish markers (plan §3.2).
# Strong markers: whole-word Kannada roots / pronouns / stopwords.
# Suffix markers: agglutinative verb/noun endings on a Latin token.
# ---------------------------------------------------------------------------
_KANGLISH_STRONG_WORDS: frozenset[str] = frozenset(
    {
        # pronouns / possessives
        "nanna",
        "ninna",
        "namma",
        "avanu",
        "avalu",
        "avaru",
        "naanu",
        "neenu",
        "idu",
        "adu",
        # family / household (plan list)
        "ganda",
        "hendati",
        "magu",
        "magalu",
        "maga",
        "mane",
        "chinna",
        "amma",
        "appa",
        "atte",
        "maava",
        "tavaru",
        # money / verbs / auxiliaries
        "hana",
        "duddu",
        "hodeyu",
        "beku",
        "beda",
        "beka",
        "illa",
        "yenu",
        "yeke",
        "yaake",
        "hege",
        "yelli",
        "illi",
        "alli",
        "inda",
        "akke",
        "koduttilla",
        "kelilla",
        "kodalla",
        "kodilla",
        "madalla",
        # Lane 05 (recall swarm): vocabulary of scripts/kn_templates.py so
        # the new KN/Kanglish paraphrase forms score as Kanglish too.
        # Legal nouns / spelling variants (whole-word Kannada, not English).
        "jeevanamsha",
        "jeevanamsa",
        "jeevanaamsha",
        "jivanaamsha",
        "vichhedana",
        "vichchhedana",
        "vichhedana",
        "paalane",
        "palane",
        "bangara",
        "chinna",
        "parihara",
        "janti",
        "ottu",
        "baki",
        "teerpu",
        "hakku",
        "bedike",
        "pramanapatra",
        "janana",
        "nyayanga",
        "berpadike",
        "madhyantara",
        "shala",
        "shulka",
        "surakshitavagilla",
        "rakshane",
        "bembala",
        "apaya",
        "hodeyu",
        "hodita",
        "bedarike",
        # possessive / inflected family words used in the templates
        "maguvina",
        "gandana",
        "hendatiya",
        # verb forms used in the templates
        "kelidde",
        "keliddene",
        "kelalilla",
        "maridare",
        "adavittare",
        "adavittiddare",
        "horahakidare",
        "horahakidaru",
    }
)

# Suffix -> weight. Applied only to tokens NOT in the exemption sets.
# A token scores at most once (longest matching suffix wins).
_KANGLISH_SUFFIXES: tuple[tuple[str, int], ...] = (
    ("uttiddare", 2),
    ("uttilla", 2),
    ("uttane", 2),
    ("uttale", 2),
    ("uttare", 2),
    ("uttidde", 2),
    ("abeku", 2),
    ("beku", 1),
    ("illa", 1),
    ("inda", 1),
    ("akke", 1),
    ("annu", 1),
    ("alli", 1),
    ("ige", 1),
    ("annu", 1),
    # Lane 05 (recall swarm): plural-past / 1st-person / modal endings
    # attested in scripts/kn_templates.py ("horahakidare", "keluttiddene",
    # "kelabahude", "itukondiddare", "surakshitavagide").
    ("uttiddaru", 2),
    ("iddare", 2),
    ("iddaru", 2),
    ("kondiddare", 2),
    ("kondidaru", 2),
    ("abahude", 2),
    ("bekendu", 1),
    ("iddene", 1),
    ("agide", 1),
)

# ---------------------------------------------------------------------------
# Lane 05 additions: "ಕೇಳಿಯೇ ಇಲ್ಲ" / "ಎಂದೂ ಕೇಳಿಲ್ಲ" (KN) and
# "keliye illa" / "yavattu kelilla" / "endu kelilla" (roman) — the
# demand-never-made forms used in scripts/kn_templates.py.
_DEMAND_FALSE_KN_RE = re.compile(
    r"ಕೇಳಿಲ್ಲ|ಕೇಳಲಿಲ್ಲ|ಕೇಳೇ\s*ಇಲ್ಲ|ಕೇಳಲೇ\s*ಇಲ್ಲ|ಕೇಳಿಯೇ\s*ಇಲ್ಲ|ಎಂದೂ\s*ಕೇಳಿಲ್ಲ"
)
_DEMAND_FALSE_ROMAN_RE = re.compile(
    r"\bkelilla\b|\bkelalilla\b|\bkele\s+illa\b|\bkeliye\s+illa\b|"
    r"\byavattu\s+kelilla\b|\bendu\s+kelilla\b",
    re.I,
)
_DEMAND_TRUE_KN_RE = re.compile(r"ಕೇಳಿದ್ದೇನೆ|ಕೇಳಿದೆ|ಕೇಳಿದ್ದೆ|ಬೇಡಿಕೆ\s*ಇಟ್ಟಿದ್ದೇನೆ")
_DEMAND_TRUE_ROMAN_RE = re.compile(
    r"\bkelidde\b|\bkeliddene\b|\bbedike\s+ittiddene\b", re.I
)

_VIOLENCE_KN_RE = re.compile(
    r"ಹೊಡೆಯುತ್ತಾನೆ|ಹೊಡೆಯುತ್ತಾಳೆ|ಹೊಡೆದ|ಹೊಡೆಯು|ಹೊಡೀತಾನೆ|ಬೆದರಿಸುತ್ತಾನೆ|"
    r"ಬೆದರಿಕೆ|ಹಿಂಸೆ|ಹೊಡೆತ|ಕೈ\s*ಮಾಡುತ್ತಾನೆ|ಹೊಡೆದರು|ಹೊಡೆಯುತ್ತಿದ್ದಾರೆ|"
    r"ಹೊಡೀತಾರೆ|ಬೆದರಿಕೆ\s*ಹಾಕುತ್ತಾನೆ"
)
_VIOLENCE_ROMAN_RE = re.compile(
    r"\bhodiyuttane\b|\bhodiyuttale\b|\bhodedu\b|\bhodita\b|\bhodithane\b|"
    r"\bbedarisuttane\b|\bhimse\b|\bhodeyu\b|\bhodeyuttare\b|"
    r"\bhodeyuttiddare\b|\bhodidaru\b|\bbedarike\b|\bbedarisuttare\b",
    re.I,
)
_EVICTION_KN_RE = re.compile(
    r"ಮನೆಯಿಂದ\s*(?:ಆಚೆ|ಹೊರಗೆ|ಹೊರಕ್ಕೆ)\s*ಹಾಕಿದ್ದಾರೆ|ಮನೆಯಿಂದ\s*ಹೊರ\s*ಹಾಕಿದ್ದಾರೆ|"
    r"ಮನೆಯಿಂದ\s*ಆಚೆ\s*ಹಾಕಿದರು|ಬಾಗಿಲು\s*ಹಾಕಿದ್ದಾರೆ|ಮನೆ\s*ಬಿಟ್ಟು\s*ಹೋಗು|"
    r"ಮನೆಯಿಂದ\s*ಹೊರ\s*ಹಾಕಿದರು|ಮನೆ\s*ಬಿಟ್ಟು\s*ಹೋಗುವಂತೆ"
)
_EVICTION_ROMAN_RE = re.compile(
    r"\bmaneyinda\b.{0,20}\b(?:horahakuttiddare|horage\s+haakidare|horage\s+hakidare|ache\s+hakidare)\b|"
    r"\bhorahakuttiddare\b|\bhorage\s+haakidare\b|\bhorahakidare\b|"
    r"\bhorahakidaru\b|\bache\s+hakidare\b|\bache\s+hakidaru\b|"
    r"\bbeega\s+hakidaru\b",
    re.I,
)

# ---------------------------------------------------------------------------
# Lane 05: Kannada / Kanglish surface-form -> issue/fact-key mapping.
# Same fact keys as the corpus schema (scripts/build_synthetic_corpus.py
# FACTS / ISSUES). Verification-only signals, like kannada_fact_hints():
# a matched form corroborates a Stage 0/1 prediction; absence is never a
# denial and a match never sets a fact on its own. Forms cover the
# scripts/kn_templates.py vocabulary: spelling variants (jeevanamsa,
# vichhedana, paalane/palane, streedhan) and code-mixed forms
# ("maintenance beku", "divorce beku", "custody beku", "residence beku",
# "stridhan vapas beku", "lump sum beku", "birth certificate beku").
# ---------------------------------------------------------------------------
_ISSUE_FORM_PATTERNS: tuple[tuple[str, str, str], ...] = (
    # (issue key, fact key or "", regex)
    ("maintenance", "money_fact",
     r"ಜೀವನಾಂಶ|jeevanamsha|jeevanamsa|jeevanaamsha|jivanaamsha|"
     r"maintenance\s+beku|maintanance\s+beku|duddu\s+kodalla"),
    ("custody", "custody_claim",
     r"ಪಾಲನೆ|paalane|palane|custody\s+beku"),
    ("residence", "residence_claim",
     r"ಮನೆಯಲ್ಲಿ\s*ಇರ|ಮನೆಯಲ್ಲೇ\s*ಇರ|maneyalli\s+irabeku|maneyalle\s+irabeku|"
     r"residence\s+beku|mane\s+bittu\s+hoguvudilla"),
    ("stridhan", "stridhan_claim",
     r"ಚಿನ್ನ|ಬಂಗಾರ|chinna|bangara|stridhan|streedhan"),
    ("divorce", "divorce_asked",
     r"ವಿಚ್ಛೇದನ|vichhedana|vichchhedana|vichhedana|divorce\s+beku"),
    ("joint_property", "joint_property_claim",
     r"ಜಂಟಿ\s*ಆಸ್ತಿ|janti\s+asti|joint\s+property"),
    ("birth_certificate", "birth_cert_asked",
     r"ಜನನ\s*ಪ್ರಮಾಣಪತ್ರ|janana\s+pramanapatra|birth\s+certificate\s+beku"),
    ("dv_compensation", "dv_injury_comp_asked",
     r"ಪರಿಹಾರ|parihara|compensation\s+beku"),
    ("restitution", "restitution_asked",
     r"ಮರಳಿ\s*ಬರ|marali\s+bar|marali\s+banni|vapas\s+barabeku"),
    ("violence", "violence",
     r"ಹೊಡೆಯುತ್ತಾನೆ|ಹೊಡೆದ|ಹಿಂಸೆ|hodeyuttane|hodita|himse|bedarisuttane"),
    ("procedure", "",
     r"ಯಾವ\s*ಕೋರ್ಟ್|yava\s+court|case\s+hege\s+hakuvudu|procedure\s+enu"),
)
_ISSUE_FORM_RES: tuple[tuple[str, str, "re.Pattern[str]"], ...] = tuple(
    (issue, fact, re.compile(pat, re.I)) for issue, fact, pat in _ISSUE_FORM_PATTERNS
)


def _latin_tokens(text: str) -> list[str]:
    """Lower-cased Latin tokens, minus zero-FP exemption words."""
    out: list[str] = []
    for tok in _TOKEN_RE.findall(text):
        low = tok.lower()
        if low in EXEMPT_INDIAN_ENGLISH_WORDS or low in _EXEMPT_ENGLISH_SUFFIX_WORDS:
            continue
        out.append(low)
    return out


def kanglish_score(text: str) -> dict[str, object]:
    """Score Latin-script text for Romanized Kannada (Kanglish).

    Returns {"score": int, "strong_hits": [...], "suffix_hits": [...],
    "is_kanglish": bool}. Scoring: strong whole-word marker = 2 points,
    suffix match = its weight (1–2). Verdict requires score >= 3 AND
    (>= 1 strong hit OR >= 2 distinct suffix-hit tokens), so one stray
    English word can never trigger it.
    """
    tokens = _latin_tokens(text)
    strong_hits: list[str] = []
    suffix_hits: list[str] = []
    score = 0
    for tok in tokens:
        if tok in _KANGLISH_STRONG_WORDS:
            strong_hits.append(tok)
            score += 2
            continue
        # Longest suffix first; at most one suffix hit per token.
        for suffix, weight in _KANGLISH_SUFFIXES:
            if len(tok) > len(suffix) + 1 and tok.endswith(suffix):
                suffix_hits.append(tok)
                score += weight
                break
    is_kanglish = bool(score >= 3 and (strong_hits or len(set(suffix_hits)) >= 2))
    return {
        "score": score,
        "strong_hits": sorted(set(strong_hits)),
        "suffix_hits": sorted(set(suffix_hits)),
        "is_kanglish": is_kanglish,
    }


def is_kanglish(text: str) -> bool:
    """True when Latin-script text is Romanized Kannada (see kanglish_score)."""
    return bool(kanglish_score(text)["is_kanglish"])


def split_script_segments(text: str) -> list[dict[str, str]]:
    """Split text into maximal same-script runs without dropping any token.

    Segment ``script`` is "kannada", "latin", or "other" (digits / punctuation
    / whitespace attach to the preceding segment, or stand alone at the start).
    English tokens inside mixed input are preserved verbatim.
    """
    segments: list[dict[str, str]] = []
    current_script: str | None = None
    current_chars: list[str] = []

    def _script_of(ch: str) -> str:
        cp = ord(ch)
        if KANNADA_RANGE[0] <= cp <= KANNADA_RANGE[1]:
            return "kannada"
        if ch.isalpha():
            return "latin"
        return "other"

    for ch in text:
        s = _script_of(ch)
        if s == "other":
            # Attach punctuation/digits/space to the current segment if any.
            if current_chars:
                current_chars.append(ch)
            else:
                segments.append({"script": "other", "text": ch})
            continue
        if current_script is None:
            current_script, current_chars = s, [ch]
        elif s == current_script:
            current_chars.append(ch)
        else:
            segments.append({"script": current_script, "text": "".join(current_chars)})
            current_script, current_chars = s, [ch]
    if current_chars and current_script is not None:
        segments.append({"script": current_script, "text": "".join(current_chars)})
    # Merge a trailing "other"-only segment into the previous one is NOT done:
    # callers keep every character; merge only consecutive same-script runs.
    merged: list[dict[str, str]] = []
    for seg in segments:
        if merged and merged[-1]["script"] == seg["script"]:
            merged[-1]["text"] += seg["text"]
        else:
            merged.append(dict(seg))
    return merged


def detect_script_locale(
    raw_text: str, explicit_locale: str | None = None
) -> dict[str, object]:
    """Detect language/script of a user question.

    Superset of the v7 return value (``{"lang", "script"}``) with the added
    ``code_mix_ratio`` key, so existing callers keep working.

    - explicit ``kn`` locale, or any Kannada-script characters -> "kn".
    - Kannada script + Latin letters -> script "mixed"; lang stays "kn"
      unless the Latin share dominates a Kanglish-free text, in which case
      the text is still "kn" (English legal insertions like "maintenance",
      "divorce", "school fees" are expected in mixed input, plan §3.2).
    - Latin-only text scoring as Kanglish -> lang "kn_roman", script "latin".
    - Otherwise -> lang "en", script "latin".

    ``code_mix_ratio`` is min(kn_chars, latin_chars) / (kn_chars + latin_chars)
    over letter characters only: 0.0 = single script, up to 0.5 = evenly mixed.
    """
    if raw_text is None:
        raw_text = ""
    text = str(raw_text)
    if explicit_locale and str(explicit_locale).lower().startswith("kn"):
        kn_chars = sum(1 for ch in text if _KANNADA_RE.match(ch))
        latin_chars = sum(1 for ch in text if _LATIN_LETTER_RE.match(ch))
        total = kn_chars + latin_chars
        ratio = (min(kn_chars, latin_chars) / total) if total else 0.0
        script = "mixed" if kn_chars and latin_chars else ("kannada" if kn_chars else "latin")
        return {"lang": "kn", "script": script, "code_mix_ratio": round(ratio, 4)}

    kn_chars = sum(1 for ch in text if _KANNADA_RE.match(ch))
    latin_chars = sum(1 for ch in text if _LATIN_LETTER_RE.match(ch))
    total = kn_chars + latin_chars
    ratio = (min(kn_chars, latin_chars) / total) if total else 0.0

    if kn_chars:
        script = "mixed" if latin_chars else "kannada"
        return {"lang": "kn", "script": script, "code_mix_ratio": round(ratio, 4)}
    if latin_chars and is_kanglish(text):
        return {"lang": "kn_roman", "script": "latin", "code_mix_ratio": 0.0}
    return {"lang": "en", "script": "latin", "code_mix_ratio": 0.0}


def kannada_fact_hints(text: str) -> dict[str, object]:
    """Verification-only factual span hints from Kannada / Kanglish text.

    - ``demand_made``: False when the speaker says they did NOT ask/demand
      (ಕೇಳಿಲ್ಲ / ಕೇಳಲಿಲ್ಲ / kelilla, plan §3.2 + evidence.py:561), True when
      they say they did ask, else None (unknown — not evidence either way).
    - ``violence_hint`` / ``eviction_hint``: True when a violence or
      coercive-eviction stem matches; False means "no stem found", NOT
      "no violence/eviction" — absence is never a denial.
    - ``matched_spans``: the literal substrings that fired, for audit.

    These hints corroborate (or challenge) neural logits; they never set a
    fact on their own.
    """
    if text is None:
        text = ""
    text = str(text)
    spans: list[str] = []

    demand_made: bool | None = None
    m = _DEMAND_FALSE_KN_RE.search(text) or _DEMAND_FALSE_ROMAN_RE.search(text)
    if m:
        demand_made = False
        spans.append(m.group(0))
    else:
        m2 = _DEMAND_TRUE_KN_RE.search(text) or _DEMAND_TRUE_ROMAN_RE.search(text)
        if m2:
            demand_made = True
            spans.append(m2.group(0))

    violence_hint = False
    mv = _VIOLENCE_KN_RE.search(text) or _VIOLENCE_ROMAN_RE.search(text)
    if mv:
        violence_hint = True
        spans.append(mv.group(0))

    eviction_hint = False
    me = _EVICTION_KN_RE.search(text) or _EVICTION_ROMAN_RE.search(text)
    if me:
        eviction_hint = True
        spans.append(me.group(0))

    return {
        "demand_made": demand_made,
        "violence_hint": violence_hint,
        "eviction_hint": eviction_hint,
        "matched_spans": spans,
    }


def kannada_issue_hints(text: str) -> dict[str, object]:
    """Verification-only issue/fact-key hints from Kannada / Kanglish text.

    Maps the surface forms of ``scripts/kn_templates.py`` to the corpus
    schema keys — spelling variants (jeevanamsha / jeevanamsa /
    jeevanaamsha / jivanaamsha, vichhedana / vichchhedana, paalane /
    palane, stridhan / streedhan) and code-mixed forms ("maintenance
    beku", "divorce beku", "custody beku", "residence beku", "stridhan
    vapas beku", "lump sum beku", "birth certificate beku") all resolve
    to the same issue/fact key as the formal Kannada form.

    Returns {"issues": {issue: True, ...}, "facts": {fact: True, ...},
    "matched_spans": [...]}. A key present means "a surface form for
    this key was seen"; a key absent means "no form seen", NOT "the
    issue/fact is denied". These hints corroborate Stage 0/1 predictions;
    they never set an issue or fact on their own.
    """
    if text is None:
        text = ""
    text = str(text)
    issues: dict[str, bool] = {}
    facts: dict[str, bool] = {}
    spans: list[str] = []
    for issue, fact, pat in _ISSUE_FORM_RES:
        m = pat.search(text)
        if m:
            issues[issue] = True
            if fact:
                facts[fact] = True
            spans.append(m.group(0))
    return {"issues": issues, "facts": facts, "matched_spans": spans}


def _self_test() -> None:
    """CPU self-test: run ``python3 -m src.laya_lang_normalizer``."""
    cases = [
        # (text, expected lang, expected script)
        ("My husband beats me and threw me out of the house.", "en", "latin"),
        ("ನನ್ನ ಗಂಡ ನನ್ನನ್ನು ಹೊಡೆಯುತ್ತಾನೆ.", "kn", "kannada"),
        # Mixed script: Kannada + English legal insertions stay "kn"/"mixed".
        ("ನನ್ನ ಗಂಡ maintenance ಕೊಡುತ್ತಿಲ್ಲ, divorce ಬೇಕು.", "kn", "mixed"),
        # Kanglish (plan §3.2 example, paraphrased): Romanized Kannada.
        ("Nanna ganda hana koduttilla, nannannu maneyinda horahakuttiddare", "kn_roman", "latin"),
        ("Nanna husband nannannu maneyinda horage haakidare, I need maintenance and residence.", "kn_roman", "latin"),
        # Zero-FP: standard Indian English legal words must NOT flip to Kanglish.
        ("My stridhan gold and mangalsutra are with my mother-in-law; the panchayat in my taluk advised me.", "en", "latin"),
        ("I want my stridhan back from my husband.", "en", "latin"),
        ("Vanilla gorilla villa.", "en", "latin"),
        ("", "en", "latin"),
    ]
    for text, lang, script in cases:
        got = detect_script_locale(text)
        assert got["lang"] == lang, (text, got, lang)
        assert got["script"] == script, (text, got, script)
        assert 0.0 <= float(got["code_mix_ratio"]) <= 0.5, got

    mixed = detect_script_locale("ನನ್ನ ಗಂಡ maintenance ಕೊಡುತ್ತಿಲ್ಲ.")
    assert mixed["code_mix_ratio"] > 0.0, mixed

    # Factual span hints.
    h = kannada_fact_hints("ನಾನು ಕೇಳಿಲ್ಲ, ಅವನು ಹಣ ಕೊಟ್ಟಿಲ್ಲ.")
    assert h["demand_made"] is False, h
    h2 = kannada_fact_hints("Nanna ganda hana kelilla.")
    assert h2["demand_made"] is False, h2
    h3 = kannada_fact_hints("My husband beats me every day.")
    assert h3["violence_hint"] is False, h3  # English-only: no Kannada stem
    h4 = kannada_fact_hints("ನನ್ನ ಗಂಡ ನನ್ನನ್ನು ಹೊಡೆಯುತ್ತಾನೆ.")
    assert h4["violence_hint"] is True, h4
    h5 = kannada_fact_hints("ಅವರು ನನ್ನನ್ನು ಮನೆಯಿಂದ ಆಚೆ ಹಾಕಿದ್ದಾರೆ.")
    assert h5["eviction_hint"] is True, h5
    h6 = kannada_fact_hints("I never asked for anything.")
    assert h6["demand_made"] is None, h6  # English negation is NOT a Kannada hint

    # Mixed-script split preserves every character, English tokens intact.
    segs = split_script_segments("ನನ್ನ ಗಂಡ maintenance ಕೊಡುತ್ತಿಲ್ಲ.")
    assert "".join(s["text"] for s in segs) == "ನನ್ನ ಗಂಡ maintenance ಕೊಡುತ್ತಿಲ್ಲ.", segs
    assert any(s["script"] == "latin" and "maintenance" in s["text"] for s in segs), segs

    # Kanglish scoring: exemptions never contribute.
    s = kanglish_score("stridhan mangalsutra panchayat taluk")
    assert s["is_kanglish"] is False and s["score"] == 0, s

    # Lane 05: new template vocabulary scores as Kanglish (spelling
    # variants + code-mixed forms from scripts/kn_templates.py).
    for t in (
        "Nanage jeevanamsa beku, ganda hana koduttilla.",
        "Nanage jeevanaamsha beku.",
        "Nanage jivanaamsha beku, maintenance beku.",
        "Nanna bangaravannu atte-mava itkondiddare, vapas beku.",
        "Nanna maguvina paalane nanage beku, magu nanna jothe irabeku.",
        "Nanage nyayanga berpadike matra beku, vichhedana beda.",
        "Nanna ganda nannannu maneyinda horahakidare, maneyalle irabeku.",
        "Nanu chinna vapas keliye illa, ega kelabahude?",
        "Nanna ganda duddu kodalla, nanage maintenance beku.",
    ):
        got = detect_script_locale(t)
        assert got["lang"] == "kn_roman", (t, got)
    # ...while plain English stays English (zero-FP still holds).
    assert detect_script_locale(
        "I want maintenance from my husband. He gives me nothing."
    )["lang"] == "en"
    assert detect_script_locale(
        "My husband sold my gold without asking me."
    )["lang"] == "en"

    # Lane 05: extended factual hints.
    h7 = kannada_fact_hints("Nanu chinna vapas keliye illa.")
    assert h7["demand_made"] is False, h7
    h8 = kannada_fact_hints("Nanna chinna avara baliye ide, nanu yavattu kelilla.")
    assert h8["demand_made"] is False, h8
    h9 = kannada_fact_hints("Nanu chinna kelidde, avaru kodalu nirakarisiddare.")
    assert h9["demand_made"] is True, h9
    h10 = kannada_fact_hints("Nanna ganda nannannu maneyinda horahakidare.")
    assert h10["eviction_hint"] is True, h10
    h11 = kannada_fact_hints("Ganda hodita, nanage rakshane beku.")
    assert h11["violence_hint"] is True, h11

    # Lane 05: issue hints — variants and code-mixed forms map to the
    # same keys as the formal Kannada forms.
    ih = kannada_issue_hints("Nanage jeevanamsa beku, ganda hana koduttilla.")
    assert ih["issues"].get("maintenance") is True, ih
    assert ih["facts"].get("money_fact") is True, ih
    ih2 = kannada_issue_hints("ನನ್ನ ಗಂಡ ಹಣ ಕೊಡುತ್ತಿಲ್ಲ. ನನಗೆ ಜೀವನಾಂಶ ಬೇಕು.")
    assert ih2["issues"].get("maintenance") is True, ih2
    ih3 = kannada_issue_hints("Nanna maguvina paalane nanage beku.")
    assert ih3["issues"].get("custody") is True, ih3
    assert ih3["facts"].get("custody_claim") is True, ih3
    ih4 = kannada_issue_hints("Nanna streedhan vapas beku.")
    assert ih4["issues"].get("stridhan") is True, ih4
    ih5 = kannada_issue_hints("Nanage nyayanga berpadike matra beku, vichhedana beda.")
    assert ih5["issues"].get("divorce") is True, ih5
    ih6 = kannada_issue_hints("Namma janti astiyalli nanna palu kodi.")
    assert ih6["issues"].get("joint_property") is True, ih6
    ih7 = kannada_issue_hints("Nanna maguvina janana pramanapatra beku.")
    assert ih7["issues"].get("birth_certificate") is True, ih7
    ih8 = kannada_issue_hints("Gayagalige parihara beku.")
    assert ih8["issues"].get("dv_compensation") is True, ih8
    ih9 = kannada_issue_hints("I want maintenance from my husband.")
    assert ih9["issues"] == {}, ih9  # English-only: no Kannada hint
    print("laya_lang_normalizer self-test: all checks passed")


if __name__ == "__main__":
    _self_test()
