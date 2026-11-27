# Backtest: Laya 421M + v2 two-stage graph vs generic LLM baseline
## Deep backtest lane — 2026-11-26

**Systems**
- **System A (ours):** Laya 421M + v2 two-stage graph — Stage 1 layman → legal terms → section, Stage 2 recheck of all relations inside the picked sections.
- **System B (baseline):** a generic LLaMA 8B instruct model with NO graph, NO decision tree, plain prompt only.

**Headline, honestly stated:** System A scores a perfect **16/16 exact section-set matches on this test set — but only as a deterministic graph walk, not as a live model run** — while the baseline is measured on **one question only (n = 1)**, the 2026-11-26 retest case, where it scores **0/10 sections correct and commits 6 forbidden mappings**. No held-out edge between A and B can be computed, because System B was never run on the held-out questions and cannot be run on this machine. Anyone quoting an "edge" from this report must quote it as **K0-only, n = 1**.

---

## 1. What was actually measured (read this before the numbers)

### System A — GRAPH WALK, not live Laya inference
No live Laya inference was run. The walk executes the v2 graph's own rules deterministically:
- **Stage 1** as the graph specifies it: **one Laya choice question per issue** (maintenance / custody / Stridhan / residence / violence / divorce / birth certificate), answered deterministically from the question text using the brief's own layman expressions ("my husband is not giving me money", "he took my gold", "they are throwing me out", "who will get my daughter", "he beats me", "I want a divorce"). Issue → section candidates come from the v1 test-report sets and the lane1 phrasebook (126 phrases, 7 issues).
- **Stage 2** as lane3 specifies it: divorce gate first, HMA 24 dropped with no proceeding pending, HMA 25 dropped with no decree, custody routed to exactly one primary (HMA 26 if a proceeding is pending, else Guardians and Wards Act 1890), Stridhan co-fire HMA 27 + BNS 316, residence completed as PWDVA 17+18+19, quantum always escalated, never invented.
- The walk script is `/tmp/backtest_walk2.py` (ephemeral scratch; the method above is the full specification). Ground-truth section sets were fixed **before** the walk ran.

**What the 16/16 does and does not prove.** The test questions deliberately use the brief's own layman phrasings, and the walk's Stage-1 cues are built from those same phrasings. A deterministic walk cannot fail on phrasings it was built from. The 16/16 is therefore a **ceiling measurement of the graph rules on in-distribution phrasings**, not proof that live Laya inference scores 16/16. What is unmeasured for System A: semantic matching on paraphrases, Kannada input, mixed/negated issues, and any live-model behaviour at all. See §6 for the counter-evidence (a phrase-level implementation of the same graph scores only 3/16 exact).

### System B — DOCUMENTED BASELINE, not a fresh LLaMA 8B run
No LLaMA 8B run was performed (see §2 for why it is infeasible here). System B's numbers come from the **already-measured generic system: the 2026-11-26 fresh English retest of Nivedh's chatbot**, rated **4/10 overall (English 8/10, legal accuracy 3/10, completeness 3/10, reasoning 2/10)**. That retest measured exactly **one** question — the known case K0. Its section output is reconstructed from the documented error record (see §4): it cited **HMA s.24 as the sole maintenance section** and listed **HMA ss.13/13B** although no divorce was asked; it cited Rajnesh v. Neha for Stridhan and Satish Chander Ahuja for custody; it put the birth certificate under HMA, called residence "tenancy rights", and asked the user to pick the court; it missed BNSS s.144, PWDVA s.20, HMA s.27, BNS s.316, HMA s.26, Guardians and Wards Act, HMGA s.6, and PWDVA ss.17–19; it demanded salary slips she said she does not have and never asked his income, the school-fee amount, or where he lives now.
- **Held-out questions (H1–H15): System B was NOT measured.** No per-question B numbers exist for them, and none are invented in this report. The B column for H1–H15 reads "not measured" throughout.

### v2 status at walk time (2026-11-26 evening)
- Lane 1 phrasebook: present (`v2-lanes/lane1-phrasebook.json`, 126 phrases, 7 issues).
- Lane 2 Stage-1 mapping: **missing** — the walk substituted its own issue-level choice implementation; lane 2 may implement Stage 1 differently.
- Lane 3 Stage-2 recheck: present (`v2-lanes/lane3-stage2-recheck.json`) but covers only **5 sections** (BNSS 144, HMA 24, HMA 25, HMA 26, HMA 27); no rechecks exist for PWDVA ss.17–20, BNS 316, GWA 1890, HMGA s.6, HMA 13/13B, or the Births and Deaths Act.
- Lane 4 adversarial tests: **missing**. Lane 5 website content: present.
- v1 graph: `laya-crpc-bns-section-decision-tree.json` (29 sections, 38 nodes, 66 edges) — read, not edited.

---

## 2. Feasibility verdicts

### Real LLaMA 8B run: NOT FEASIBLE on this machine
- **RAM:** 7,934 MB total, **440 MB available** at check time. LLaMA 8B instruct is ~16 GB in FP16; even a 4-bit quantised copy (~5 GB) does not fit in 440 MB available. A real 8B CPU run is infeasible, not merely slow.
- **Weights:** Meta LLaMA weights are gated (Hugging Face token required). **No HF token is set on this VM** (no `HF_*` variable in the environment).
- **Toolchain:** neither `torch` nor `transformers` is installed.
- **Disk is not the blocker:** 143 GB free — the download would fit; RAM and gating block it.
- **What would be needed:** a machine with ≥16 GB RAM (≥32 GB recommended for CPU inference), a Hugging Face account with access to Meta's gated LLaMA weights, and a fresh ~16 GB download.

### Live Laya inference: NOT RUN (not attempted in this lane)
- Model **is** present: PIXMELT/laya English, 808 MB, `~/workspace/models/laya-english/model.safetensors`. Its `test.py` loads it with `import laya` (`HF_HUB_OFFLINE=1`).
- Blockers in this lane: `torch`, `transformers`, and the `laya` package are all **not installed**, and only 440 MB RAM was available against a 421M-parameter model (~1.7 GB FP32 weights plus runtime). Installing torch CPU and the laya package and loading the checkpoint was not attempted here; it may be possible after freeing RAM, but it was not done, so **no live Laya number exists**. All System A scores below are graph-walk scores.

---

## 3. Held-out test set (15 held-out + 1 known case)

Ground truth (GT) = the sections the v1 test report + lane3 recheck rules say are **kept** for the facts stated. HMA 24 counts only with a proceeding pending; HMA 25 only at/after a decree; HMA 26 only inside a pending HMA proceeding (else GWA 1890 is the custody route); HMA 13/13B only if divorce is asked; BNS 316 is kept for Stridhan even when no demand has been made yet (demand-first fallback: make a written demand, then re-evaluate — it is escalated, not dropped). "WELFARE" = the welfare-of-the-child principle.

| ID | Kind | Question (layman, as asked) | Ground-truth kept sections |
|----|------|-----------------------------|----------------------------|
| K0 | **known** (2026-11-26 retest, rephrased) | My husband left us two years ago and gives no money. I earn forty thousand a month, it is not enough for me and my eight year old daughter. My gold worth five lakh and two lakh cash my parents gave me is with my husband's family and they will not return it. They are throwing me out of the house which is in my husband's name. Who will get my daughter, how do I get my gold back, and which court do I go to? | BNSS 144, PWDVA 20, GWA 1890, HMGA s.6, WELFARE, HMA 27, BNS 316, PWDVA 17, PWDVA 18, PWDVA 19 (10) |
| H1 | held-out, single-issue maintenance | My husband has not given me any money for three months. I earn fifteen thousand a month and I have two small children and no case filed anywhere. | BNSS 144, PWDVA 20 |
| H2 | held-out, single-issue custody, no proceeding | Who will get my six year old son? My husband says as the father he will take him away from me. | GWA 1890, HMGA s.6, WELFARE |
| H3 | held-out, single-issue Stridhan, **demand not yet made** | My mother gave me gold at my wedding and my in-laws kept it. I have never asked them to return it. | HMA 27, BNS 316 |
| H4 | held-out, single-issue residence | They changed the lock and I cannot enter my house. The house is in my husband's name. | PWDVA 17, PWDVA 18, PWDVA 19 |
| H5 | held-out, multi-issue, **divorce asked** | I want a divorce from my husband. He beats me, I need money every month and I want my daughter to stay with me. | HMA 13, BNSS 144, PWDVA 20, PWDVA 18, GWA 1890, HMGA s.6, WELFARE |
| H6 | held-out, **divorce NOT asked** (explicit) | I do not want a divorce. I just want money every month from my husband and to stay in the house with my daughter. | BNSS 144, PWDVA 20, PWDVA 17, PWDVA 18, PWDVA 19 |
| H7 | held-out, **birth certificate** | How do I get my daughter's birth certificate? The hospital did not give us one. | Births and Deaths Act 1969 |
| H8 | held-out, **salary slips missing, income unknown** | I need maintenance but I do not have my husband's salary slips and I do not know what he earns. | BNSS 144, PWDVA 20 |
| H9 | held-out, **income unknown, quantum asked** | How much money can I get every month from my husband? | BNSS 144, PWDVA 20 |
| H10 | held-out, **demand not yet made** + maintenance | My husband has my gold and I have not asked for it back yet, and he gives no money for me and my child. | HMA 27, BNS 316, BNSS 144, PWDVA 20 |
| H11 | held-out, **no proceeding pending**, interim money asked | I need money while my case is going on, but I have not filed any case yet. | BNSS 144, PWDVA 20 |
| H12 | held-out, **out of scope** | My brother and I are fighting over our father's ancestral house. Who owns it and can I stop him selling it? | (none — no family-law section applies) |
| H13 | held-out, multi-issue violence + residence + school fees | He beats me, throws me out of the house and gives no money for my son's school fees. | PWDVA 18, PWDVA 17, PWDVA 19, PWDVA 20, BNSS 144 |
| H14 | held-out, **proceeding pending** (divorce case on in Family Court) | My divorce case is already going on in the Family Court. I want my son to stay with me and money for his school fees while the case goes on. | HMA 13, HMA 26, HMGA s.6, WELFARE, HMA 24, BNSS 144, PWDVA 20 |
| H15 | held-out, Stridhan sold | He sold my gold without asking me. The gold was given to me by my parents at my wedding. | BNS 316, HMA 27 |

Coverage required by the brief, all present: single-issue (H1–H4, H7–H9, H15), multi-issue (H5, H10, H13, H14, K0), divorce-NOT-asked (H6, K0), birth-certificate (H7), salary-slips-missing (H8), income-unknown (H8, H9), demand-not-yet-made (H3, H10), no-proceeding-pending (H1, H2, H11), out-of-scope (H12).

Two GT judgement calls, documented so the numbers can be re-derived: (1) **H14 includes HMA 13** — the divorce case is already pending, so the pending petition is under HMA 13; the reliefs sought are custody + interim maintenance, but citing the governing section of the pending case is not an error. HMA 13B is excluded (no mutual consent stated). (2) **H4 excludes PWDVA 20** — no money or rent is claimed; PWDVA 20 is monetary relief, and the residence set's s.20 fires only when money/rent is in play.

---

## 4. Per-question results

### System A — Laya + v2 graph (deterministic graph walk)

| ID | Precision | Recall | Exact set match | Forbidden mappings | Court correct | Escalates correctly |
|----|-----------|--------|-----------------|--------------------|---------------|---------------------|
| K0 | 1.000 (10/10) | 1.000 (10/10) | Yes | 0 | Yes | Yes |
| H1 | 1.000 (2/2) | 1.000 (2/2) | Yes | 0 | Yes | Yes |
| H2 | 1.000 (3/3) | 1.000 (3/3) | Yes | 0 | Yes | Yes |
| H3 | 1.000 (2/2) | 1.000 (2/2) | Yes | 0 | Yes | Yes |
| H4 | 1.000 (3/3) | 1.000 (3/3) | Yes | 0 | Yes | Yes |
| H5 | 1.000 (7/7) | 1.000 (7/7) | Yes | 0 | Yes | Yes |
| H6 | 1.000 (5/5) | 1.000 (5/5) | Yes | 0 | Yes | Yes |
| H7 | 1.000 (1/1) | 1.000 (1/1) | Yes | 0 | Yes (Registrar, not a court) | Yes |
| H8 | 1.000 (2/2) | 1.000 (2/2) | Yes | 0 | Yes | Yes |
| H9 | 1.000 (2/2) | 1.000 (2/2) | Yes | 0 | Yes | Yes |
| H10 | 1.000 (4/4) | 1.000 (4/4) | Yes | 0 | Yes | Yes |
| H11 | 1.000 (2/2) | 1.000 (2/2) | Yes | 0 | Yes | Yes |
| H12 | 1.000 (0/0) | 1.000 (0/0) | Yes | 0 | Yes (out of scope) | Yes (declines, does not escalate) |
| H13 | 1.000 (5/5) | 1.000 (5/5) | Yes | 0 | Yes | Yes |
| H14 | 1.000 (7/7) | 1.000 (7/7) | Yes | 0 | Yes | Yes |
| H15 | 1.000 (2/2) | 1.000 (2/2) | Yes | 0 | Yes | Yes |

Stage-2 drops the walk actually exercised (proof the recheck does work, not just the picks): HMA 13 dropped in K0/H6 (divorce not asked); HMA 24 dropped in K0, H1, H5, H6, H8, H9, H10, H11, H13 (no proceeding pending) and **kept** in H14 (proceeding pending); HMA 25 dropped everywhere (no decree — future route only); HMA 26 dropped in K0, H2, H5 (no proceeding — GWA 1890 route) and **kept** in H14. Escalations produced on every question that needed them: quantum always escalated, never an amount; husband's income / school fees / whereabouts asked, salary slips never demanded; written demand first for Stridhan where none was made (H3, H10); residence preference asked (H4, K0, H6, H13).

### System B — generic LLM baseline (documented 2026-11-26 retest)

| ID | Precision | Recall | Exact set match | Forbidden mappings | Court correct | Escalates correctly |
|----|-----------|--------|-----------------|--------------------|---------------|---------------------|
| K0 | **0.000 (0/3)** — cited {HMA 24, HMA 13, HMA 13B}, none of which is in the kept set for these facts | **0.000 (0/10)** | No | **6** (see below) | No (asked user to pick the court) | No (demanded salary slips; never asked income, school fees, or whereabouts) |
| H1–H15 | **not measured** — no LLaMA 8B run exists and none was possible on this machine | not measured | not measured | not measured | not measured | not measured |

The 6 forbidden mappings on K0: (1) Rajnesh v. Neha cited for Stridhan return; (2) Satish Chander Ahuja cited for custody; (3) HMA ss.13/13B listed although divorce was not asked; (4) residence called "tenancy rights"; (5) user asked to pick the court; (6) birth certificate said to be under HMA. Sections missed entirely: BNSS s.144, PWDVA s.20, HMA s.27, BNS s.316, HMA s.26, Guardians and Wards Act, HMGA s.6, PWDVA ss.17–19.

Fairness note on B's 0.000: the strict section-set metric counts **kept** sections only. B did identify maintenance as an issue in prose and cited HMA 24, a real maintenance section — but the wrong route for these facts (no HMA proceeding pending), and as the sole maintenance section. The 0 means "no section in the kept set", not "said nothing relevant". Its overall retest rating (4/10; legal accuracy 3/10) reflects the same picture at prose level.

---

## 5. Aggregate metrics and the edge

### System A (graph walk)

| Metric | Overall (n = 16) | Held-out only (n = 15) | Known case (n = 1) |
|--------|------------------|------------------------|---------------------|
| Exact section-set match | **16/16 (100%)** | 15/15 (100%) | 1/1 |
| Mean per-section precision | 1.000 | 1.000 | 1.000 |
| Mean per-section recall | 1.000 | 1.000 | 1.000 |
| Micro precision / recall (TP 57, FP 0, FN 0 overall; TP 47, FP 0, FN 0 held-out) | 1.000 / 1.000 | 1.000 / 1.000 | 1.000 / 1.000 |
| Forbidden mappings (total) | 0 | 0 | 0 |
| Court correct | 16/16 | 15/15 | 1/1 |
| Escalates correctly when facts missing | 16/16 | 15/15 | 1/1 |

### System B (documented baseline)

| Metric | Known case (n = 1) | Held-out (n = 15) |
|--------|--------------------|--------------------|
| Exact section-set match | 0/1 | not measured |
| Per-section precision / recall | 0.000 / 0.000 | not measured |
| Forbidden mappings | 6 | not measured |
| Court correct | 0/1 | not measured |
| Escalates correctly | 0/1 | not measured |
| Overall rating (retest) | 4/10 overall, legal accuracy 3/10 | — |

### The edge (A minus B) — computable ONLY on the known case, n = 1

| Metric | A (K0) | B (K0) | Edge (A − B) | Sample size |
|--------|--------|--------|--------------|-------------|
| Exact section-set match | 1 | 0 | **+1** | n = 1 |
| Per-section precision | 1.000 | 0.000 | **+1.000** | n = 1 |
| Per-section recall | 1.000 | 0.000 | **+1.000** | n = 1 |
| Forbidden mappings | 0 | 6 | **−6** | n = 1 |
| Court correct | 1 | 0 | **+1** | n = 1 |
| Escalates correctly | 1 | 0 | **+1** | n = 1 |

**There is no held-out edge.** A held-out edge would require B numbers on H1–H15, which do not exist. Do not quote "+1.000 precision" as a general result; it is a one-question comparison against a system that scored zero on that question.

---

## 6. Sensitivity check — why the 16/16 must not be over-read

Before settling on the issue-level Stage-1 implementation, the walk was first run as **phrase-level bag-of-words matching** over the same 126-phrase phrasebook (any phrase sharing ≥2 content words fires its candidates). That version scored **overall exact 3/16, mean precision 0.526, mean recall 0.938** (held-out exact 2/15, mean precision 0.494). It over-fired everywhere: e.g. H4 (pure residence) picked up Stridhan, custody and maintenance sections from shared generic words ("house", "husband", "my gold"), and H12 (out of scope) fired the residence set. The graph's rules are sound; the **matching layer is the fragile part**. The 16/16 belongs to the issue-level choice design (one binary choice per issue, as the brief specifies), not to phrase matching. If lane 2 implements Stage 1 as naive phrase matching, expect precision near 0.5, not 1.0. Live Laya semantic matching is the untested middle ground between these two proxies — it could land anywhere between them on paraphrased input.

---

## 7. Verdict — how much better is our classification model, in plain language

**On the one question both systems have actually been measured on, ours is decisively better: it gets every section right where the generic system got none, makes zero forbidden errors where the generic system made six, picks the court where the generic system asked the user to pick it, and asks for the missing facts where the generic system demanded documents the woman said she does not have.** On the 15 held-out questions, our graph walk is perfect (15/15 exact) — but that is a walk of our own rules on questions written in our own phrasings, and the generic system has no score there at all, so the honest held-out claim is "our graph behaves correctly on 15 new questions" and not "we beat LLaMA 8B by X".

The real, durable advantage the backtest demonstrates is not a model-size effect — it is the **graph**: the generic system fails in exactly the ways a graph prevents (wrong precedent attached to the wrong issue, divorce sections when divorce was never asked, a single maintenance route instead of the set, the court question pushed back to the user, salary slips demanded). Every one of those failures is structurally impossible in the walk, because Stage 2 drops the section instead of keeping it. That is the edge, and it is worth building on — but it is an edge of **rules over free text**, and it stands or falls on Stage 1 matching real user phrasing, which is precisely the part that has never yet been run through a live model.

## 8. Where System A still fails / open gaps

1. **No live model run exists.** Nothing here measures Laya's semantic choices on unseen phrasing, Kannada input, typos, or mixed/negated issues. The 16/16 is a walk, and the walk's Stage-1 cues were written from the same phrasings as the test questions (circularity risk, stated plainly).
2. **Phrase-level matching collapses precision (0.494 in the sensitivity run).** Lane 2 must implement Stage 1 at issue level (one choice per issue), not as phrase bag-of-words, or the live system will over-fire like the first walk attempt.
3. **Two latent phrasebook defects found during the walk** (lane1, to fix before relying on phrase-level matching):
   - Phrase "they are throwing me out of the house and my daughter has school here" lists **HMA 26** as a section candidate — it drags custody into a residence question (caused false custody sections in the phrase-level run). Fix: remove HMA 26 from that phrase, or make it conditional on a custody cue.
   - Phrase "should I divorce my husband" maps to **HMA 13 + HMA 13B** — 13B is mutual-consent divorce, and an advice question states no mutual consent. Fix: 13B must require a mutual-consent fact.
4. **Stage 2 is incomplete.** Lane 3 has rechecks for only 5 sections (BNSS 144, HMA 24, HMA 25, HMA 26, HMA 27). There is **no recheck for HMA 13/13B** (so nothing in Stage 2 would stop a 13B misfire), none for PWDVA ss.17–20, BNS 316, GWA 1890, HMGA s.6, or the Births and Deaths Act.
5. **Birth-certificate coverage gap.** Lane 1 has no birth-certificate phrases and no such issue; H7 was handled in the walk by a special rule, not by the phrasebook. A user asking only about a birth certificate has no Stage-1 path.
6. **Lane 2 missing.** The Stage-1 mapping lane was not present at walk time; this backtest substituted its own implementation. The numbers must be re-run once lane 2 lands, against this same test set, to check lane 2 agrees.
7. **BNS 316 demand-first fallback is untested as an answer**, not just as a rule: the walk keeps BNS 316 with an escalation to make a written demand first (H3, H10). Whether a live answer presents it as live vs conditional has not been checked.
8. **Small, single-rater test set (n = 16).** Ground truth was written by one rater (this lane), and the H14 HMA 13 inclusion is a judgement call (§3). An independent rater and paraphrase variants (especially Kannada) are needed before claiming robustness.
9. **Not scored:** documents checklist, timeline, and answer prose quality — the walk scores section selection, court, and escalation only. The baseline's reasoning score (2/10) has no System A counterpart here.

## 9. Recommended next steps (for the coordinator)

1. Re-run this exact test set (K0 + H1–H15, same GT) once lane 2 lands, and again once live Laya inference runs — report all three numbers side by side; do not replace the walk numbers silently.
2. Fix the two lane1 defects (§8.3) and add lane3 rechecks for HMA 13/13B (mutual-consent condition for 13B), PWDVA 17–20, BNS 316, and GWA/HMGA.
3. Add a birth-certificate issue to lane 1.
4. Build a paraphrase/Kannada variant set (same 16 questions, reworded) — that is the test that will actually discriminate the walk from live Laya.
5. For a real LLaMA 8B baseline, use a machine with ≥16 GB RAM and a Hugging Face account with Meta gated-weight access; do not attempt it on this VM.
