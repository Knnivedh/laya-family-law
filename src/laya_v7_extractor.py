"""Stage 0/1 bilingual, PIXMELT/laya, Qwen3-1.7B, and grounded extractor for LAYA v7.

Backends:
  - 'evidence': zero-model deterministic grounded evidence extractor (<1ms/Q).
  - 'laya': batched PIXMELT/laya (421M ModernBERT-large) clause-max semantic
    scoring + NLLB-200 Kannada->English + grounded evidence & applicability guards.
  - 'structured': grammar-constrained Qwen/Qwen3-1.7B decoding + NLLB-200 + grounded.
  - 'auto': prefers 'laya' on CUDA if PIXMELT/laya is cached, else 'structured', else 'evidence'.
"""

from __future__ import annotations

from functools import lru_cache
import re
from typing import Any

from .laya_v7_evidence import extract_grounded_v7
from .laya_v7_schema import FactEvidence, IssueEvidence, proved_true

QWEN_MODEL_ID = "Qwen/Qwen3-1.7B"
QWEN_REVISION = "70d244cc86ccca08cf5af4e1e306ecf908b1ad5e"
LAYA_MODEL_ID = "PIXMELT/laya"
LAYA_REVISION = "29a1a48862bf4a92935c5a7162e1f88a05fc7440"
NLLB_MODEL_ID = "facebook/nllb-200-distilled-600M"

_KANNADA_RE = re.compile(r"[\u0c80-\u0cff]")
_SENT_SPLIT_RE = re.compile(r"(?<=[.!?।;\n])\s+")
_GENERIC_TAIL_RE = re.compile(
    r"^(?:what|how|which|where|please|can|should)\b.{0,45}[?.!]*$",
    re.I,
)

# Calibrated general family-law Laya semantic noul probes (verified against dev + Brutal ROC)
LAYA_NOUL_PROMPTS: dict[str, dict[str, str]] = {
    "maint_a": {"type": "noul", "instructions": "Does this question ask for monthly money or maintenance for the wife or a child?"},
    "maint_p": {"type": "noul", "instructions": "Does the person ask for money, maintenance, alimony, school fees, household expenses, or financial support from their spouse, parent, or child?"},
    "cust_p": {"type": "noul", "instructions": "Does a parent ask for child custody, guardianship, visitation, or for a child, baby, son, or daughter to live or stay with them or return to them?"},
    "strid_p": {"type": "noul", "instructions": "Does the wife ask to get back gold, jewellery, ornaments, cash, or stridhan kept, refused, or sold by her husband or in-laws?"},
    "res_a": {"type": "noul", "instructions": "Does this question ask about staying in, or being thrown out of, the shared house or home?"},
    "vio_a": {"type": "noul", "instructions": "Does this question say the husband beats, threatens or harasses the wife?"},
    "div_p": {"type": "noul", "instructions": "Does the speaker want to get a divorce or end the marriage (not merely stating a divorce case is already pending)?"},
    "jp_p": {"type": "noul", "instructions": "Do the spouses jointly own a house, flat, plot, shop, or car that the speaker wants divided or shared?"},
    "bc_p": {"type": "noul", "instructions": "Is this question about getting, registering late, or correcting a child's birth certificate?"},
}

CONSTRAINED_SLOTS: tuple[tuple[str, tuple[str, ...], str], ...] = (
    ("sc", ("Y", "N"), "scope: Indian family-law dispute? N=landlord/employer/insurer/sibling-property/exam only"),
    ("sx", ("F", "M", "U"), "claimant sex: F=wife/mother/woman, M=husband/father/man, U=unknown"),
    ("rl", ("S", "P", "C", "U"), "claimant role: S=spouse/ex-spouse, P=aged parent seeking own support, C=parent asking child support only, U=unknown"),
    ("mn", ("Y", "N"), "actually requesting financial maintenance/support/alimony/expenses?"),
    ("ls", ("Y", "N"), "specifically requesting lump-sum or one-time settlement?"),
    ("eo", ("Y", "N"), "enforcing arrears or varying/reducing/cancelling an existing court support order?"),
    ("dv", ("Y", "N"), "expressly asking to get a divorce?"),
    ("mc", ("Y", "N"), "both spouses agree / mutual-consent divorce?"),
    ("ph", ("Y", "N"), "actual HMA / Family Court matrimonial case currently pending?"),
    ("bf", ("Y", "N"), "user definitely states they ARE filing / WILL file an HMA petition?"),
    ("dc", ("Y", "N"), "divorce or JS decree ALREADY passed/granted?"),
    ("cs", ("Y", "N"), "asking child custody, guardianship, visitation, or who keeps child?"),
    ("rs", ("Y", "N"), "claiming right to stay in shared house, thrown/locked out, or separate residence?"),
    ("vo", ("Y", "N"), "physical violence, threats, harassment, intimidation, or domestic cruelty?"),
    ("st", ("Y", "N"), "wife claiming wedding gold/stridhan withheld/refused/sold by husband/in-laws?"),
    ("jp", ("Y", "N"), "claiming share/division of jointly owned flat/house/plot/shop/car?"),
    ("bc", ("Y", "N"), "child birth certificate issuance, late registration, or correction?"),
    ("of", ("Y", "N"), "material open fact changing remedy/proof/entitlement?"),
)


def detect_script_locale(raw_text: str, explicit_locale: str | None = None) -> dict[str, str]:
    if explicit_locale and explicit_locale.lower().startswith("kn"):
        return {"lang": "kn", "script": "kannada"}
    if _KANNADA_RE.search(raw_text):
        return {"lang": "kn", "script": "kannada"}
    return {"lang": "en", "script": "latin"}


def laya_available(min_free_gb: float = 2.0) -> bool:
    try:
        from huggingface_hub import snapshot_download
        import torch
        snapshot_download(LAYA_MODEL_ID, revision=LAYA_REVISION, local_files_only=True)
        if not torch.cuda.is_available():
            return False
        free_bytes, _ = torch.cuda.mem_get_info()
        return free_bytes >= int(min_free_gb * (1024 ** 3))
    except Exception:
        return False


def available_on_cuda(min_free_gb: float = 4.2) -> bool:
    try:
        import torch
        if not torch.cuda.is_available():
            return False
        free_bytes, _ = torch.cuda.mem_get_info()
        return free_bytes >= int(min_free_gb * (1024 ** 3))
    except Exception:
        return False


@lru_cache(maxsize=2)
def _load_laya_agent(device: str = "cuda"):
    from huggingface_hub import snapshot_download
    import laya
    import torch

    snap = snapshot_download(LAYA_MODEL_ID, revision=LAYA_REVISION, local_files_only=True)
    agent = laya.Agent(snap, device=device, vegaml=False)
    if device == "cuda":
        # Ensure ModernBERT sits cleanly in bf16 for fast RTX Tensor Core throughput
        try:
            agent.model = agent.model.to(dtype=torch.bfloat16)
        except Exception:
            pass
    return agent


@lru_cache(maxsize=2)
def _load_qwen(device: str = "cuda"):
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer

    dtype = torch.bfloat16 if device == "cuda" else torch.float32
    tok = AutoTokenizer.from_pretrained(QWEN_MODEL_ID, revision=QWEN_REVISION, local_files_only=True)
    tok.padding_side = "left"
    if tok.pad_token_id is None:
        tok.pad_token_id = tok.eos_token_id
    model = AutoModelForCausalLM.from_pretrained(
        QWEN_MODEL_ID,
        revision=QWEN_REVISION,
        dtype=dtype,
        local_files_only=True,
    )
    if device == "cuda":
        model = model.to("cuda")
    model.eval()
    return tok, model


@lru_cache(maxsize=2)
def _load_nllb(device: str = "cuda"):
    import torch
    from transformers import AutoModelForSeq2SeqLM, AutoTokenizer

    dtype = torch.float16 if device == "cuda" else torch.float32
    tok = AutoTokenizer.from_pretrained(NLLB_MODEL_ID, local_files_only=True)
    model = AutoModelForSeq2SeqLM.from_pretrained(NLLB_MODEL_ID, dtype=dtype, local_files_only=True)
    if device == "cuda":
        model = model.to("cuda")
    model.eval()
    return tok, model


def translate_kannada_batch(texts: list[str], device: str = "cuda") -> list[str]:
    """Sentence-split batched NLLB-200 Kannada -> English translation."""
    import torch

    if not texts:
        return []
    tok, model = _load_nllb(device)
    tok.src_lang = "kan_Knda"
    bos_id = tok.convert_tokens_to_ids("eng_Latn")
    all_sents: list[str] = []
    spans: list[tuple[int, int]] = []
    for raw in texts:
        sents = [s.strip() for s in _SENT_SPLIT_RE.split(raw.strip()) if s.strip()]
        start = len(all_sents)
        all_sents.extend(sents)
        spans.append((start, len(all_sents)))
    if not all_sents:
        return list(texts)
    decoded_all: list[str] = []
    bs = 16
    for i in range(0, len(all_sents), bs):
        chunk = all_sents[i : i + bs]
        inputs = tok(chunk, return_tensors="pt", padding=True, truncation=True, max_length=256)
        if device == "cuda":
            inputs = {k: v.to("cuda") for k, v in inputs.items()}
        with torch.inference_mode():
            gen = model.generate(**inputs, forced_bos_token_id=bos_id, num_beams=4, max_new_tokens=160)
        decoded_all.extend(s.strip() for s in tok.batch_decode(gen, skip_special_tokens=True))
    return [" ".join(s for s in decoded_all[a:b] if s) or texts[idx] for idx, (a, b) in enumerate(spans)]


def translate_kannada_to_english(raw_text: str, device: str = "cuda") -> str:
    return translate_kannada_batch([raw_text], device=device)[0]


def _split_clauses_for_laya(text: str) -> list[str]:
    """Full question plus clean complete sentences (zero noisy comma-fragment splits)."""
    full = text.strip()
    out = [full]
    for s in _SENT_SPLIT_RE.split(full):
        c = s.strip()
        words = c.split()
        if len(words) < 4 or c == full or _GENERIC_TAIL_RE.match(c):
            continue
        out.append(c)
    return out


def extract_laya_probs_batch(questions: list[str], device: str = "cuda", batch_size: int = 32) -> list[dict[str, float]]:
    """Run batched PIXMELT/laya semantic noul probes over full-text + informative clauses."""
    if not questions:
        return []
    agent = _load_laya_agent(device)
    flat_states: list[str] = []
    q_slices: list[tuple[int, int]] = []
    for q in questions:
        parts = _split_clauses_for_laya(q)
        a = len(flat_states)
        flat_states.extend(parts)
        q_slices.append((a, len(flat_states)))

    preds = agent.predict_batch(
        flat_states,
        LAYA_NOUL_PROMPTS,
        batch_size=batch_size,
        sort_by_length=True,
    )
    out: list[dict[str, float]] = []
    for a, b in q_slices:
        pooled: dict[str, float] = {}
        full_ans = preds[a].get("answers", {})
        for k in LAYA_NOUL_PROMPTS:
            full_p = float(full_ans.get(k, {}).get("noul", 0.0) or 0.0)
            cmax_p = max(
                (float(preds[idx].get("answers", {}).get(k, {}).get("noul", 0.0) or 0.0) for idx in range(a, b)),
                default=full_p,
            )
            pooled[k] = round(cmax_p, 4)
            pooled[f"full_{k}"] = round(full_p, 4)
        out.append(pooled)
    return out


def _build_dfa(tokenizer) -> tuple[dict[int, dict[int, int]], int]:
    states: dict[int, dict[int, int]] = {}
    next_state = 1

    def _add_seq(start_st: int, text: str) -> int:
        nonlocal next_state
        ids = tokenizer.encode(text, add_special_tokens=False)
        cur = start_st
        for tid in ids:
            nxt = states.setdefault(cur, {}).get(tid)
            if nxt is None:
                nxt = next_state
                next_state += 1
                states[cur][tid] = nxt
            cur = nxt
        return cur

    cur_frontier = [0]
    for idx, (slot, choices, _) in enumerate(CONSTRAINED_SLOTS):
        prefix = f"{slot}=" if idx == 0 else f" {slot}="
        merge_state = next_state
        next_state += 1
        for st in cur_frontier:
            after_eq = _add_seq(st, prefix)
            for ch in choices:
                ch_ids = tokenizer.encode(ch, add_special_tokens=False)
                assert len(ch_ids) == 1
                states.setdefault(after_eq, {})[ch_ids[0]] = merge_state
        cur_frontier = [merge_state]

    eos_id = tokenizer.eos_token_id
    for st in cur_frontier:
        states.setdefault(st, {})[eos_id] = -1
    return states, eos_id


@lru_cache(maxsize=2)
def _get_dfa_for_device(device: str):
    tok, _ = _load_qwen(device)
    return _build_dfa(tok)


def _format_prompt(question: str) -> str:
    schema_lines = "\n".join(f"- {k} ({'/'.join(vals)}): {desc}" for k, vals, desc in CONSTRAINED_SLOTS)
    return (
        "Classify the Indian family-law question strictly from stated facts.\n"
        f"Output exact key=value sequence.\nFields:\n{schema_lines}\n\n"
        f"Question: {question}\nOutput:"
    )


def _decode_slots(text: str) -> dict[str, str]:
    out: dict[str, str] = {}
    for tok in text.strip().split():
        if "=" in tok:
            k, v = tok.split("=", 1)
            out[k] = v
    return out


def extract_model_slots_qwen_batch(questions: list[str], device: str = "cuda", batch_size: int = 16) -> list[dict[str, str]]:
    import torch

    if not questions:
        return []
    tok, model = _load_qwen(device)
    dfa, eos_id = _get_dfa_for_device(device)
    results: list[dict[str, str]] = []
    for i in range(0, len(questions), batch_size):
        chunk = questions[i : i + batch_size]
        prompt_strs = [
            tok.apply_chat_template(
                [
                    {"role": "system", "content": "Output only the exact constrained slot string."},
                    {"role": "user", "content": _format_prompt(q)},
                ],
                tokenize=False,
                add_generation_prompt=True,
                enable_thinking=False,
            )
            for q in chunk
        ]
        inputs = tok(prompt_strs, return_tensors="pt", padding=True)
        prompt_len = inputs["input_ids"].shape[1]
        if device == "cuda":
            inputs = {k: v.to("cuda") for k, v in inputs.items()}

        def allowed_tokens_fn(batch_id: int, input_ids) -> list[int]:
            gen = input_ids[prompt_len:].tolist()
            st = 0
            for tid in gen:
                st = dfa.get(st, {}).get(int(tid), -1)
                if st == -1:
                    return [eos_id]
            opts = list(dfa.get(st, {}).keys())
            return opts or [eos_id]

        with torch.inference_mode():
            out_ids = model.generate(
                **inputs,
                max_new_tokens=72,
                do_sample=False,
                prefix_allowed_tokens_fn=allowed_tokens_fn,
                pad_token_id=eos_id,
            )
        for row in out_ids:
            results.append(_decode_slots(tok.decode(row[prompt_len:], skip_special_tokens=True)))
    return results


def _merge_laya_and_grounded(
    facts: dict[str, Any],
    issues: dict[str, IssueEvidence],
    negated: set[str],
    probs: dict[str, float],
    *,
    is_kannada: bool = False,
) -> None:
    """Fuse calibrated PIXMELT/laya semantic probabilities with grounded span/negation guards."""
    if not proved_true(facts, "in_scope", default=True):
        return
    if proved_true(facts, "no_dispute_empty"):
        return

    raw_txt = facts.get("_raw_analysis", "")
    role_val = getattr(facts.get("claimant_role"), "value", "unknown")

    maint_full_a = probs.get("full_maint_a", 0.0)
    maint_full_p = probs.get("full_maint_p", 0.0)
    maint_smax = max(probs.get("maint_a", 0.0), probs.get("maint_p", 0.0))
    # Calibrated against task-866 / task-882 ROC: full_maint_a>=0.33 (99% P) or full_maint_p>=0.50 (100% P)
    maint_hit = (
        maint_full_a >= 0.33
        or maint_full_p >= 0.50
        or (is_kannada and (maint_full_a >= 0.28 or maint_full_p >= 0.48))
        or (maint_smax >= 0.68 and not re.search(r"\b(?:bank|repayment|lender|tenant|landlord|locks?\s+me\s+in|gold|jewellery|sale\s+money|money\s+for\s+it)\b", raw_txt, re.I))
    )
    maint_p = max(maint_full_a, maint_full_p, maint_smax) if maint_hit else 0.0

    vio_full = probs.get("full_vio_a", 0.0)
    vio_smax = probs.get("vio_a", 0.0)
    vio_p = vio_full if vio_full >= 0.42 else (vio_smax if vio_smax >= 0.45 else 0.0)

    has_strid_anchor = bool(
        re.search(r"\b(?:stridhan|streedhan|gold|jewellery|jewelry|ornaments?|bangles?|necklace|earrings?|chain|ring|mangalsutra|wedding\s+gifts?|things\s+back)\b", raw_txt, re.I)
    )
    strid_p = probs.get("full_strid_p", 0.0) if has_strid_anchor else 0.0

    has_res_anchor = bool(
        re.search(r"\b(?:house|home|flat|household|residence|evict|vacate|lock|enter|place\s+to\s+stay|accommodation)\b", raw_txt, re.I)
    )
    confinement_only = bool(
        re.search(r"\blocks?\s+me\s+in\s+(?:the\s+|a\s+)?(?:house|home|room)\b", raw_txt, re.I)
        and not re.search(r"\b(?:out|entry|vacate|evict|separate\s+place|afraid\s+to\s+stay)\b", raw_txt, re.I)
    )
    res_full = probs.get("full_res_a", 0.0) if (has_res_anchor and not confinement_only) else 0.0
    cust_p = probs.get("cust_p", 0.0)
    div_full = probs.get("full_div_p", 0.0)
    jp_full = probs.get("full_jp_p", 0.0)
    bc_full = probs.get("full_bc_p", 0.0)

    def _boost(fkey: str, ikey: str, score: float, thr: float) -> None:
        if ikey in negated or score < thr or proved_true(facts, fkey):
            return
        facts[fkey] = FactEvidence(key=fkey, status="supported", value=True, source="model", confidence=score)
        if issues.get(ikey) and issues[ikey].intent == "uncertain":
            issues[ikey] = IssueEvidence(issue=ikey, intent="requested", source="model", confidence=score)

    if strid_p >= 0.36 and "stridhan" not in negated:
        _boost("stridhan_claim", "stridhan", strid_p, 0.36)
        if proved_true(facts, "stridhan_claim"):
            facts["stridhan_held_or_disposed"] = FactEvidence(key="stridhan_held_or_disposed", status="supported", value=True, source="model", confidence=strid_p)

    # Custody boost only when minor child exists (never elderly-parent role!), not adult, not house co-location, not maint-only
    minor_denied = facts.get("minor_child") and getattr(facts["minor_child"], "status", "") == "denied"
    has_child = proved_true(facts, "child_fact")
    res_coloc = bool(re.search(r"\b(?:stay|live|remain)\s+in\s+(?:the|our|my)\s+(?:house|home)\s+(?:with|alongside)\b", raw_txt, re.I))
    maint_only_for_child = bool(
        re.search(r"\b(?:maintenance|money|support|school\s+fees)\s+(?:only\s+)?for\s+(?:the\s+|my\s+|our\s+)?(?:\d+-?year-?old\s+)?(?:child|children|kids|son|daughter)\b", raw_txt, re.I)
        and not re.search(r"\b(?:custody|stay|live|keep|visitation|see\s+my|who\s+(?:will|gets))\b", raw_txt, re.I)
    )
    if role_val != "parent" and has_child and not minor_denied and not res_coloc and not maint_only_for_child and not proved_true(facts, "child_maintenance_only") and not proved_true(facts, "residence_claim"):
        _boost("custody_claim", "custody", cust_p, 0.55 if not is_kannada else 0.35)

    if "maintenance" not in negated and maint_p > 0.0:
        _boost("money_fact", "maintenance", maint_p, 0.24)

    if not res_coloc and not re.search(r"\b(?:do\s+not|don['’]t)\s+(?:want|need)\b.{0,25}\b(?:house|stay)\b", raw_txt, re.I):
        _boost("residence_claim", "residence", res_full, 0.55 if not is_kannada else 0.48)

    if vio_p > 0.0:
        _boost("violence", "violence", vio_p, 0.35)

    if jp_full >= 0.45 and not re.search(r"\b(?:divided\s+later|in-?laws['’]?\s+property|solely\s+in)\b", raw_txt, re.I):
        _boost("joint_property_claim", "joint_property", jp_full, 0.45)

    _boost("birth_cert_asked", "birth_certificate", bc_full, 0.22)

    has_div_anchor = bool(re.search(r"\b(?:divorce|divorcing|end\s+(?:the|our|this|my)\s+marriage|dissolve|separate\s+from)\b", raw_txt, re.I))
    div_context_only = (
        proved_true(facts, "proceeding_pending_hma")
        or proved_true(facts, "decree")
        or bool(re.search(r"\b(?:after\s+(?:our|the|a)\s+divorce|while\s+(?:the\s+|my\s+)?divorce|divorce\s+(?:case|petition|matter)|not\s+decided|while\s+i\s+decide)\b", raw_txt, re.I))
    )
    if has_div_anchor and not proved_true(facts, "judicial_separation_only") and not div_context_only:
        _boost("divorce_asked", "divorce", div_full, 0.84)


def extract_v7_batch(
    raw_texts: list[str],
    *,
    locales: list[str | None] | None = None,
    mode: str = "auto",
    device: str = "cuda",
    kannada_strategy: str = "nllb_then_en",
    batch_size: int = 32,
) -> list[dict[str, Any]]:
    """Batched Stage 0/1 extraction preserving strict per-question isolation."""
    use_mode = mode
    if use_mode == "auto":
        if device != "cpu" and laya_available(1.8):
            use_mode = "laya"
        elif device != "cpu" and available_on_cuda(3.8):
            use_mode = "structured"
        else:
            use_mode = "evidence"

    locs = [detect_script_locale(t, locales[idx] if locales else None) for idx, t in enumerate(raw_texts)]
    translations: list[str | None] = [None] * len(raw_texts)
    if use_mode in {"laya", "structured"} and kannada_strategy == "nllb_then_en":
        kn_indices = [idx for idx, loc in enumerate(locs) if loc["lang"] == "kn"]
        if kn_indices:
            kn_trans = translate_kannada_batch([raw_texts[i] for i in kn_indices], device=device)
            for idx, tr in zip(kn_indices, kn_trans):
                translations[idx] = tr

    analysis_texts = [translations[i] if translations[i] is not None else raw_texts[i] for i in range(len(raw_texts))]

    laya_probs_list: list[dict[str, float]] = [{} for _ in raw_texts]
    model_slots_list: list[dict[str, str]] = [{} for _ in raw_texts]
    if use_mode == "laya":
        laya_probs_list = extract_laya_probs_batch(analysis_texts, device=device, batch_size=batch_size)
    elif use_mode == "structured":
        model_slots_list = extract_model_slots_qwen_batch(analysis_texts, device=device, batch_size=min(batch_size, 16))

    outputs: list[dict[str, Any]] = []
    for idx, raw_text in enumerate(raw_texts):
        loc = locs[idx]
        is_kn = loc["lang"] == "kn"
        translated = translations[idx]
        analysis_text = analysis_texts[idx]
        grounded = extract_grounded_v7(
            raw_text,
            translated_text=translated,
            is_kannada_orig=is_kn,
            raw_kannada=raw_text if is_kn else "",
        )
        facts: dict[str, Any] = dict(grounded["facts"])
        facts["_raw_analysis"] = analysis_text
        issues: dict[str, IssueEvidence] = dict(grounded["issues"])
        negated = set(grounded["negated_issues"])

        if use_mode == "laya":
            _merge_laya_and_grounded(facts, issues, negated, laya_probs_list[idx], is_kannada=is_kn)
        elif use_mode == "structured":
            # Retain structured Qwen fallback mode cleanly
            from .laya_v7_schema import FactEvidence as _FE
            slots = model_slots_list[idx]
            if slots.get("cs") == "Y" and "custody" not in negated and not proved_true(facts, "custody_claim"):
                facts["custody_claim"] = _FE(key="custody_claim", status="supported", value=True, source="model", confidence=0.7)
        facts.pop("_raw_analysis", None)
        facts["negated_issues"] = negated
        facts["open_fact_markers"] = set(grounded.get("open_fact_markers", set()))
        outputs.append({
            "lang": loc["lang"],
            "script": loc["script"],
            "translated_text": translated,
            "analysis_text": analysis_text,
            "extractor_mode": use_mode,
            "model_slots": laya_probs_list[idx] if use_mode == "laya" else model_slots_list[idx],
            "facts": facts,
            "issues": issues,
            "negated_issues": negated,
        })
    return outputs


def extract_v7(
    raw_text: str,
    *,
    locale: str | None = None,
    mode: str = "auto",
    device: str = "cuda",
    kannada_strategy: str = "nllb_then_en",
) -> dict[str, Any]:
    return extract_v7_batch(
        [raw_text],
        locales=[locale],
        mode=mode,
        device=device,
        kannada_strategy=kannada_strategy,
        batch_size=1,
    )[0]
