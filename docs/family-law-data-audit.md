# Indian family-law corpus audit

## What the current data can teach

- The 7,500 training rows contain 3,573 English, 1,931 Kannada and 1,996 Romanized Kannada questions. The Kannada script and Romanized Kannada accuracy gap persists despite substantial representation by row count.
- Maintenance is requested in 2,986 rows, compared with 247 for restitution, 265 for domestic-violence compensation and 307 for birth registration. The claimant labels include 6,308 female claimants, 337 male claimants and 855 unknown. The claimant role is spouse in 6,506 rows, parent in 103 and child in 82.
- About 85% of issue slots are uncertain and 87% of fact slots are unknown. Violence, procedure and birth registration have zero explicitly denied issue examples. Eleven of 28 fact heads have no explicit denials. Only 10.2% of supported fact labels and 3.7% of denied fact labels carry an annotated span.
- The frozen validation set has 500 rows. Every validation row has the same recorded block signature as a training row. Every row also has a training match in another language on a block-and-label proxy. The source lacks translation-sibling and scenario-family identifiers, so these are overlap signals rather than proof of exact translations.
- The 28 Kaanoon questions are all labeled English. Their section targets were derived from the graph. The set helps test extraction on public lay wording, and a separate legally adjudicated dataset is still needed to test which provisions should apply.

## Isolate the cause of a routing miss

Substituting the dataset's annotated facts while keeping the evidence extractor's predicted issues changed agreement with the synthetic graph-derived targets from **261/500 to 500/500**. On Kaanoon it changed agreement from **14/28 to 27/28**. Substituting the issues alone gave **272/500** and **15/28**, respectively. These are component diagnostics. They test agreement with existing graph-derived labels and leave questions of substantive legal correctness to independent annotation.

On 500 texts per language, MuRIL's median token count per Kannada word was 1.694, compared with 4.654 for mmBERT and 2.000 for XLM-R. None of the three truncated a sampled text or dropped an annotated span at 320 tokens, so this sample does not establish a truncation explanation. Compare end-to-end section recall and precision before choosing a backbone. [MuRIL](https://huggingface.co/google/muril-base-cased) · [mmBERT](https://huggingface.co/jhu-clsp/mmBERT-base) · [XLM-R](https://huggingface.co/FacebookAI/xlm-roberta-base)

## Reproduce the grouped development split

```powershell
python scripts/audit_family_corpus.py --out ../family-corpus-audit.json
python scripts/build_grouped_family_split.py --output-dir ../family-grouped-dev
python scripts/train_v71_classifier.py --train-file ../family-grouped-dev/grouped_train.jsonl --val-file ../family-grouped-dev/grouped_dev.jsonl --check-data-only
```

The grouped split uses the existing training file as its only input. The reproducible default produced 7,002 training rows and 498 development rows, with zero shared recorded blocks, normalized exact texts or IDs. All 11 requested issue labels have examples in each language in both partitions. The trainer accepted every row. The development set is still synthetic and shares upstream generation methods. Its English, Kannada and Romanized Kannada CPU evidence agreement was 222/239, 50/131 and 42/128, respectively. Compare candidates on the same partition.

## Collect the evidence that is missing

1. **Use official statutes and judgments for legal labels.** Record the Act, section, applicable time period, jurisdiction facts, procedural posture, decision rationale and evidence needed to establish each predicate. Store the primary source URL and review status. [Statutory coverage roadmap](family-law-coverage-roadmap.md)
2. **Collect separately authored lay questions in each target language.** Prioritize current gaps in child and parent maintenance, restitution, civil registration, economic abuse and distinct marriage regimes. Include matching examples where names are replaced, parties are swapped, harm is expressly denied, or an old order replaces a new one. Capture native Kannada and Romanized Kannada as independently authored examples where possible.
3. **Label fact states and literal evidence.** Separate affirmative, denied, unclear and conflicting facts. Annotate whose claim it is, which marriage or order it concerns, when it occurred, and the text span. Keep quoted or hypothetical facts apart from asserted facts, and identify legally material missing information with a follow-up question.
4. **Assign scenario IDs before creating variants.** Keep every paraphrase, translation, minimal pair and multi-turn continuation of a scenario in one partition. Reserve independent evaluation cases with primary-source-backed section and forum labels. Use development failures for iteration and release cases for a frozen confirmation run.

## Balanced grouped corpus & MuRIL training update (2026-11-28)

To address the zero-denial / zero-conflict / minority-role gaps and validate neural generalization without validation template leakage, [`scripts/build_balanced_grouped_corpus.py`](../scripts/build_balanced_grouped_corpus.py) constructs `data/synthetic_v7_1_balanced/` over the disjoint grouped split (`7,002` train, `498` untouched `grouped_dev`):

- Appends `1,082` span-annotated multilingual training blocks (`378` EN, `350` KN, `354` `kn_roman`; zero overlap with `grouped_dev` by block, normalized text, or row ID; `check_ngram_leakage.py --strict` exit `0`, `0` 8-gram overlap).
- Fixes raw `[CLS]` representation collapse (`std=0.00075` on `google/muril-base-cased`) in [`src/laya_v7_classifier.py`](../src/laya_v7_classifier.py) via `pool_mode="mean_ln"` (`LayerNorm` over masked mean token pooling), per-slot class weights, and weighted enum losses in [`scripts/train_v71_classifier.py`](../scripts/train_v71_classifier.py).
- **Disjoint `grouped_dev` (`n=498`) results:** Epoch-4 MuRIL label micro-F1 reached **`0.9748`** (`issue`, macro `0.9237`), **`0.9814`** (`fact`), **`90.76%`** `claimant_sex`, **`93.17%`** `claimant_role`, **`98.80%`** `modality_time`, and **`100%`** `in_scope` denied recall (`30/30`). End-to-end section exact match climbed from **`314/498` (`63.05%`)** CPU evidence -> **`374/498` (`75.1%`; KN `77.1%`, `kn_roman` `78.9%`)** MuRIL alone -> **`418/498` (`83.94%`; EN `90.0%`, KN `77.9%`, `kn_roman` `78.9%`)** hybrid `mode="auto"`. See [the official statute gap registry](statutory-gaps-government-sources.md) and [the integrated backtest summary](../results/v71-muril-10x-report.md).
