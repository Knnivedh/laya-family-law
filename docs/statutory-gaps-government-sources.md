# Official Government Statute Verification & Legal Gap Registry

**Audit Date:** 2026-11-28  
**Sources Verified Against:** Official Indian legislation hosted via India Code (`indiacode.nic.in`), Gazette notifications (`egazette.gov.in`), Supreme Court of India (`api.sci.gov.in`), and CARA (`cara.wcd.gov.in`).  
**Scope:** Grounds LAYA's executable Graph `v4` / `v4.1` and chatbot API (`src/laya_chat_api.py`, `src/laya_v7_graph.py`, `src/laya_runtime.py`) strictly in statutory prerequisites, forum rules, temporal cutoffs, and uncovered legal regimes.

---

## 1. Verified Executable Provisions & Code Fixes Established

| Statute & Section | Official Verification Summary | Gap Found in Repo | Concrete Code Alignment |
|---|---|---|---|
| **PWDVA, 2005 §2(a) & §20(1)(d)** (`a2005-43.pdf`) | §2(a): "aggrieved person" means any woman who is/has been in a domestic relationship alleging domestic violence. §20(1)(d): monetary relief explicitly includes *"maintenance for the aggrieved person **as well as her children, if any**"*, alongside CrPC §125 / BNSS §144. | `src/laya_v7_graph.py:527` (`not child_only`) + `school_fees_only` (`src/laya_v7_evidence.py:818`) blocked `pwdva-20` for mothers asking child expenses or mentioning `"only"` (`stay only`, `earn only`), regressing Brutal `B-024`, `B-027`, `B-086`, `B-127`. | Restrict child-only `pwdva-20` exclusion to `sex == "male"` or `role == "child"`; tighten `school_fees_only` to explicit fees-exclusivity wording. |
| **BNSS, 2023 §§144, 146, 531** (`bnss,_2023.pdf`, commenced 1 Jul 2024, S.O. 848(E)) | §144 replaces CrPC §125 (wife, minor/disabled child, parent; 60-day interim target). §146 covers alteration/cancellation upon change in circumstances or civil decree. §531 saves pre-1 Jul 2024 pending applications under CrPC 1973. | `src/laya_family_evidence.py` lacked the prospective new-order guard (`"new/fresh maintenance order"` could confuse recovery/existing-order flow); Classifier `FACTS` (28) lacked direct `arrears_recovery_asked` / `maintenance_variation_asked`. | Guard prospective new maintenance orders cleanly in `src/laya_family_evidence.py`; bridge post-order split facts & BNSS §531 pre-July-2024 review triggers cleanly in `src/laya_integrated.py`. |
| **BNS, 2023 §§316, 358** (`a2023-45.pdf`, commenced 1 Jul 2024) | §316 consolidates IPC §§405–409 criminal breach of trust (entrusted Stridhan). §358 saves prior IPC proceedings/offences. | Pre-1 Jul 2024 entrustment/misappropriation requires IPC §406 savings review rather than silent retroactive BNS §316 substitution. | Documented transition date check + clarification/review flag for pre-July-2024 dates. |
| **HMA, 1955 §§10, 13A, 19, 24–27 & SMA, 1954 §§23, 31 & FCA, 1984 §§7–8** | HMA §10 judicial separation decree; §13A alternate relief in divorce proceeding; SMA §23 District Court / Family Court (§31 + FCA §7(1)); FCA §7(2) grants Family Court First-Class Magistrate maintenance jurisdiction where established. | HMA/SMA judicial separation only wired opt-in for `evidence` mode; classifier-only `run_question` lacked `judicial_separation_act` propagation & `B-075` child-return was misread as HMA §9 restitution! | Guard `_RESTITUTION_RE` against child-return custody phrasing (`B-075`); carry Act detection (`_declared_marriage_acts`) cleanly across both classifier and evidence paths. |
| **GWA, 1890 §§7, 9, 17 & HMGA, 1956 §§6, 13** | GWA §9 anchors person guardianship to District Court where the minor *ordinarily resides*; §17 requires welfare & minor's intelligent preference. HMGA §6 proviso places custody under age 5 *ordinarily with mother*; §13 overrides personal law for child welfare. | Brutal `statutory_primary` projects `hmga-1956-s6` and `welfare-principle` as companions, while territorial jurisdiction (`ordinarily resides`) is not collected before naming District/Family Court. | Preserve explicit `"confirm local jurisdiction"` qualification + targeted forum clarification for GWA custody. |

---

## 2. Statutory Regimes NOT Yet Executable (`needs_review` / Phase 2–4 Expansion Target)

These regimes were verified against India Code & Supreme Court decisions and **must never be routed by analogy to HMA**:

1. **Personal Marriage / Divorce Statutes (Governing-Law Gate):**
   - **Dissolution of Muslim Marriages Act, 1939**, **Muslim Women (Protection of Rights on Divorce) Act, 1986 §3** (*Danial Latifi* lifetime-adequate provision inside *iddat*), **Muslim Women (Protection of Rights on Marriage) Act, 2019 §§5–6** (*Mohd. Abdul Samad v. State of Telangana*, 2024 SC confirming independent CrPC §125/BNSS §144 right alongside 1986 Act).
   - **Divorce Act, 1869** (Christian marriages), **Parsi Marriage and Divorce Act, 1936**, **Foreign Marriage Act, 1969** (cross-border marriages), **HAMA, 1956 §§18–22**.
   - **Parents and Senior Citizens Act, 2007 §12:** Prohibits simultaneous double recovery under this Act and BNSS §144 — requires explicit election clarification when a parent mentions a Senior Citizens Tribunal order.
2. **Adoption, Child Marriage & Civil Registration Granularity:**
   - **Juvenile Justice (Care and Protection of Children) Act, 2015 §61 (as amended 2021)** & **CARA Adoption Regulations 2022:** Adoption order jurisdiction shifted from Civil Court to the **District Magistrate** (*in camera*, 2-month statutory target) — do **not** route JJ Act adoption to Family Court!
   - **Prohibition of Child Marriage Act, 2006:** Child marriage voidability + minor safety protections + penalty provisions.
   - **Registration of Births and Deaths Act, 1969 §§13 & 15:** Currently grouped as single Act-level ID (`births-deaths-act-1969`); needs separate routing between §13 delayed registration (>1 year requires Magistrate order) vs §15 clerical/fraudulent correction.
3. **Unverified Judicial Precedents Registry (`legal/verified_authorities.json`):**
   - Only **1 of 9** listed case authorities (*Sukhdev Singh v. Sukhbir Kaur*, `[2025] 2 SCR 1569`, `2025 INSC 197`) is `verified_primary`; 8 remain `unverified` pending primary judgment reading (`P2.4`/`P2.5`). Consumer prose in `src/laya_prose_v2.py` keeps **zero unverified case-name emissions (`Fp=0`)**.

---

## 3. Data Imbalance Diagnostic & Balanced Remediation Plan

Audited directly from `data/synthetic_v7_1/manifest.json` (`8,000` rows) & `docs/family-law-data-audit.md`:
1. **Leakage in frozen `validation.jsonl`:** `500/500` validation rows share template block signatures with `train.jsonl`. We keep `validation.jsonl` untouched (`SHA 7640d067...`) as legacy regression, and evaluate true generalization strictly on the **block-disjoint `grouped_dev.jsonl` (`498` rows)** + real **`Kaanoon-28`** + **`Brutal-230`** + **`16-Q`**.
2. **Severe Label/Polarity/Role Skew inside `train.jsonl`:**
   - `0` `issues_denied` in `violence`, `birth_certificate`, `procedure`.
   - `0` `facts_denied` in **11/28** fact heads (`judicial_separation_only`, `lump_sum_settlement`, `interim_asked`, `child_fact`, `minor_child`, `child_maintenance_only`, `school_fees_fact`, `child_safety_risk`, `explicit_residence_order_only`, `stridhan_sold_or_mortgaged`, `birth_cert_asked`).
   - `0` `facts_conflicting` in **23/28** fact heads.
   - Only **`10.2%`** supported fact labels & **`3.7%`** denied fact labels carry span annotations (`spans`).
   - Demographics & issues skewed (`95.5%` known sex female vs `4.5%` male; `1.3%` parent / `1.1%` child roles; `maintenance: 3,171` vs `restitution: 267`, `dv_compensation: 282`, `birth_certificate: 333`, `procedure: 319`).
3. **Remediation (`scripts/build_balanced_grouped_corpus.py`):**
   - Outputs `data/synthetic_v7_1_balanced/{grouped_train,grouped_dev,balanced_train}.jsonl`.
   - Keeps `grouped_dev.jsonl` (`498` rows) **100% unmodified** and disjoint from all new balanced training blocks.
   - Injects balanced EN / Kannada (`kn`) / Kanglish (`kn_roman`) blocks with `[[key:phrase]]` span tags across every rare issue, denied issue, denied fact, conflicting fact, prospective vs existing maintenance order minimal pair, and male/parent/child role.
