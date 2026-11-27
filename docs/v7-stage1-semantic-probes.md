# Stage 1 Semantic Signals & Prompting Probes (v7 Design Study)

**Hardware:** Local NVIDIA RTX 5050 Laptop GPU (`cuda:0`, `PIXMELT/laya` 421M ModernBERT-large, `laya==0.5.5`, `bf16`)  
**Scope:** Strictly public regression (`16-Q`) + `brutal-bank-v1-frozen.json` English items (`C1–C12, C14`); zero sealed wording read or used for threshold fitting.

---

## 1. Empirical Root Cause Proven by v6-brutal (`60` English Silent Questions)

In [`results/live-laya-colab-results-v6-brutal-final.json`](../results/live-laya-colab-results-v6-brutal-final.json):
- Out of **`60` English questions that went completely silent (`kept=[]`)**, **`35/60` (`58.3%`)** already had `PIXMELT/laya` full-text `stage1_raw` above threshold before v5's English regex gates zeroed them:
  - `_CUSTODY_PATTERNS` + `_RESIDENCE_COLOC_RE` killed `37` of `41` `gwa-1890` misses (`"remain with me"`, `"remain in my care"`, `"Who gets the kids?"`, `"stay in the house with me"` — scoring `0/20` on `C5`).
  - `money_fact` regex killed `17` `bnss-144` & `16` `pwdva-20` misses (`"books and uniforms"`, `"15,000 rupees... ask for an increase"` where Laya scored `0.569 > 0.10`).
  - `gold_fact` regex killed all `8` `hma-27` joint flat/house/car claims (`C6`).
  - `residence_claim` regex killed `13` `pwdva-17`/`pwdva-19` claims.

---

## 2. Live GPU Probe Summary (`v1`–`v4`, `102`–`121` Challenging Questions)

Four progressive GPU probe rounds replaced regex hard-vetoes with zero-shot Laya semantic `noul` and `choice` prompts evaluated across `121` hard English cases (`v3+v4`) and `102` common overlap cases (`v1+v2+v3+v4`):

| Issue / Signal | Best Semantic Probe Result (`102-Q` Common Set, `TP / FP / FN` -> `F1`) | `121-Q` (`V3+V4` Only) `F1` | Key Takeaway |
|---|---:|---:|---|
| **`birth_certificate`** | `4 / 0 / 0` → **`1.000`** | `4 / 0 / 0` → **`1.000`** | `is_birth_cert_v4` cleanly resolves all missed school/late registration paraphrases |
| **`joint_property` (`hma-27`)** | `7 / 0 / 0` → **`1.000`** | `7 / 0 / 2` → **`0.875`** | `noul_joint_prop_v3 >= 0.65` + `hma_pending / being_filed` achieves perfect recall on joint flat/property |
| **`custody`** | `25 / 6 / 0` → **`0.893`** | `26 / 9 / 0` → **`0.852`** | `100%` recall (`FN=0`), fixing `C5` collapse; needs `child_maint_only` disambiguation to trim `FP=6` |
| **`divorce` (`hma-13/13b`)** | `11 / 0 / 4` → **`0.846`** | — | `noul_mutual_divorce_v3` cleanly separates `B-017` (`0.955`) & `B-154` (`0.850`) |
| **`stridhan` (`bns-316`)** | `13 / 4 / 2` → **`0.812`** | `9 / 7 / 10` → **`0.514`** | Combining `v1` prompt + `is_stridhan_held_v4` + `gold_safe_or_spent` suppression recovers wedding gold paraphrases (`0.514 -> 0.812`) |
| **`maintenance`** | `42 / 23 / 3` → **`0.764`** | `52 / 29 / 4` → **`0.759`** | Recall jumped from `54%` to **`93%`**, but zero-shot Laya over-fires on non-money disputes (`FP=23`) |
| **`violence` (`pwdva-18`)** | `15 / 10 / 4` → **`0.682`** | `15 / 8 / 4` → **`0.714`** | Recovers coercive control (`B-016`: `0.80`), still confuses workplace/male disputes without strict speaker/domain gates |
| **`residence` (`pwdva-17/19`)** | `8 / 10 / 2` → **`0.571`** | `11 / 6 / 2` → **`0.733`** | Confuses custody-in-home & violence-only queries unless separated by Graph v4 sub-checks |
| **Micro Total (`102-Q`)** | **`125 / 53 / 15` (`P=0.702, R=0.893, F1=0.786`)** | `Silent: 4/106` | **`Silent` plunged from `60/214` to `1/94`** on English hard cases |

### Speaker / Role Extraction Probes (`C8` & `B-037`/`B-047`)

- **Aged parents (`BNSS 144` only):** `is_elder_parent_v4` cleanly isolated `B-037` (`0.661`) and `B-047` (`0.798`), matching `v3` `elder_parent` (`0.93` and `0.91`).
- **Male claimants (`sp_has_wife` vs `sp_has_husband`):** Cleanly separated ALL 7 male `C8` cases (`B-143, 144, 146, 148, 150, 153, 154`: `has_wife = 0.51–0.89` vs `has_husb = 0.17–0.22`), with two false flags on female long-narratives (`B-023`, `B-226`) requiring explicit speaker-subject framing (`"I am the husband"` vs `"wife"`).

---

## 3. Why Stage 0/1 Supervised Heads Are Required to Cross `>= 0.95` Micro-F1 (`10/10` Gate)

The `V1–V4` GPU probes empirically establish both the ceiling and the exact next build requirement:
1. **Zero-shot `PIXMELT/laya` recovers the signal** once English regex vetoes are removed (`89.3%` recall, `1/94` silent).
2. **Zero-shot `noul` prompting plateaus around `0.786` micro-F1** (`P=0.702`, `FP=53`) because zero-shot ModernBERT assigns `0.25–0.75` probability to incidental mentions (`H3` stridhan firing maintenance, `B-181` workplace colleague firing DV, `B-069` undisputed gold firing `stridhan`).
3. **Required v7 Next Build (per `README.md §9` `P1.2`):** Train lightweight multi-label Stage 0/1 classification & atomic-fact heads (10–14 facts + 11 issue heads, 3-state `supported / negated / unknown`) on top of the frozen `421M` ModernBERT encoder using `200–400` **fresh synthetic scenario-family examples** (explicitly checked `0` 8-gram overlap against `16-Q`, `Brutal-230`, and `Sealed-28`) — preserving `0.3–0.4s/Q` GPU batched speed while raising precision from `0.70` to `>=0.95`.
