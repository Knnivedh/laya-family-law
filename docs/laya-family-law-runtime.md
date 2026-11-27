# LAYA family-law runtime

The first end-to-end release area is maintenance under Indian family law. An
English layperson's question enters a local text extractor. It suggests
facts, and the decision rules return potential provisions, their requirements,
qualified forum information, and the next fact needed. The user can correct a
model suggestion using information from their papers or situation.

## Run the intake

From the repository root, using the environment that has `laya` and the
cached checkpoints:

```powershell
python -m src.laya_family --interactive
```

On a CUDA GPU with at least 5 GiB free and a complete local Qwen snapshot,
the default command uses the structured extractor. Use `--extractor structured`
to select it explicitly or `--extractor laya` for the smaller legacy extractor.
JSON output identifies which extractor ran. The structured extractor runs
offline once its pinned checkpoint is cached.

Describe the maintenance issue in plain English. The program asks about
unresolved facts and shows the possible provisions, why they were selected,
what evidence or eligibility facts matter, and a qualified forum with official
sources. Press Enter to leave a fact unresolved.

## Runtime contract

- `python -m src.laya_family --question "your question"` prints JSON. If
  `--question` is omitted, the command reads one question from standard input.
- Repeat `--confirm field=yes` or `--confirm field=no` to answer a clarification.
  The rules receive supported, denied, or unresolved facts and know whether the
  model or the user supplied each decisive fact. Scores are model suggestions.
- The adapter loads a pinned local LAYA model. The deterministic engine also
  accepts explicitly authored evidence for isolated rule tests.
- Keep the question and source evidence local. The runtime consumes no
  benchmark labels or annotations.

## First routes

- BNSS §144 for a new wife, minor-child or parent claim. Explain the proof
  needed for eligibility, the financial facts, the applicable forum check and
  prior-order disclosure. Do not estimate a maintenance amount.
- HMA §24 for interim maintenance or expenses in an identified active HMA case,
  and HMA §25 for permanent maintenance at or after an identified HMA decree.
  The statute, proceeding type and stage need to be supported independently of
  whether the user wants financial relief. The intake asks users to verify the
  pending proceeding, decree or order statute from their papers when the
  question does not establish it. An explicit statement about the user's own
  case can provide that evidence directly. Cite only the law tied to the
  actual order or proceeding.
- BNSS §144(3) for recovery under an identified BNSS order and §146 for variation
  of that order. For an unclear or older order, collect its governing law and
  route to review before applying the BNSS provisions.
- Other family-law remedies remain unresolved in this runtime. The legacy
  research notebook is separate.

## Raw-text regression

The [accuracy plan](laya-maintenance-accuracy-plan.md) records the frozen
development and verification method. Run the development suite on the new
extractor from the repository root:

```powershell
python -B -m tests.laya_maintenance_backtest --split development --extractor structured --strict
```

Use `--split verification` for the diagnosed regression bank, `--split
challenge` for further adversarial cases, and `--split final_check` for the
later frozen engineering check. The reports include exact provision sets,
extra provisions, required clarifications, structural source audits, runtime
errors and outcome hashes. The authored banks include unsupported-script
cases to exercise the language boundary.

## Historical guided smoke evidence

Run `python -m unittest discover -s tests -p test_laya_family.py` for
deterministic tests. With the model installed, run the authored live cases
from the repository root.

```powershell
$env:LAYA_CUDA_AMP = 'fp16'
python -B -m tests.live_family_smoke --device cuda
```

On 27 November 2026 the guided scenario run matched the expected provision
set on 12/12 cases, including the 7 that expected a provision. Answers to
follow-ups were scripted from the scenario facts. With only the initial
text, exact match was 7/12 overall and 2/7 for cases expecting a provision.
No extra provisions were emitted in that run. These cases are a local
regression check for maintenance. Independent reviewers and a fresh test
bank are needed to establish broader legal accuracy.

## Primary authorities

- [BNSS commencement notification S.O. 848(E)](https://www.mha.gov.in/files/whats_new_documents/BharatiyaNagarikSurakshaSanhita_24022024.pdf)


- [Bharatiya Nagarik Suraksha Sanhita, 2023](https://www.indiacode.nic.in/bitstream/123456789/20340/1/bnss%2C_2023.pdf)
- [Hindu Marriage Act, 1955](https://www.indiacode.nic.in/bitstream/123456789/1560/1/A1955-25Eng.pdf)
- [Family Courts Act, 1984](https://www.indiacode.nic.in/bitstream/123456789/1844/1/A1984__66.pdf)
- [Rajnesh v. Neha, Supreme Court, 4 November 2020](https://api.sci.gov.in/supremecourt/2018/37875/37875_2018_39_1501_24602_Judgement_04-Nov-2020.pdf)
