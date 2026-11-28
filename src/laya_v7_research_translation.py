"""Opt-in Kannada translation for noncommercial v7 benchmark reproduction."""

from functools import lru_cache
import re

NLLB_MODEL_ID = "facebook/nllb-200-distilled-600M"
_SENT_SPLIT_RE = re.compile(r"(?<=[.!?।;\n])\s+")


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
