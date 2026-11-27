#!/usr/bin/env python3
"""Build the Colab bundle and the Colab-ready notebook for the LIVE Laya
inference test (Laya 421M + v2 two-stage decision graph).

Bundle (laya-graph/colab_bundle/):
  laya-crpc-bns-section-decision-tree-v2.json  (419 KB, 32 sections)
  README.md -- file list + upload instructions

Notebook (live-laya-colab-test.ipynb):
  - Cell 0 (markdown): header -- purpose, local blockers, Colab free
    tier RAM ~12-13 GB / optional T4 GPU, model fits easily, no
    credentials needed.
  - Cell 1 (code): environment check -- RAM / GPU / Python, no install.
  - Cell 2 (code): pip install torch transformers safetensors
    huggingface_hub laya==0.5.5. Running this cell installs and runs
    upstream laya code, so the user must approve it in Colab first.
  - Cell 3 (code): inspect the laya API (version, load / Agent /
    Router) -- no model load yet.
  - Cell 4 (code): download the PIXMELT/laya snapshot, load the CLASSIC
    encoder checkpoint only (never the Vega engine), print loader,
    dtype, load time, RAM at load.
  - Cell 5 (code): files.upload() the v2 graph JSON, verify 32 sections
    / 46 nodes / 77 edges.
  - Cell 6 (code): the 16-question test set + ground truth, embedded
    verbatim from the local backtest file section 3 / section 6.
  - Cell 7 (code): LIVE Stage 1 (one Laya typed decision per issue,
    chosen option + probabilities recorded, never a rule walk) then
    deterministic Stage 2 recheck from the backtest rules.
  - Cell 8 (code): score exact / precision / recall / forbidden /
    court / escalates, print per-question table + aggregates, save
    live-laya-colab-results.json + .md and offer files.download().

The notebook never embeds the 804 MB weights. The v2 graph JSON is
uploaded separately by the user (bundle). The test set is embedded
because it is the test specification, not data to be uploaded.

Local live test was BLOCKED 2026-11-26 ~22:00 IST (see
live-laya-inference-test.md): 0/16 attempted. Blockers: (1) installing /
running the laya package locally needs an explicit user go-ahead, not
given for a local run; (2) laya 0.5.5 loads a new Vega engine by
default, classic checkpoints need explicit naming; (3) this VM has
only 323-538 MB RAM available, the 421M model needs ~1.7 GB FP32 /
~842 MB FP16. Colab free tier (~12-13 GB RAM, optional T4 GPU)
removes blocker (3); running the notebook in Colab is the user
running the install himself, which is his own go-ahead for the
Colab run. Nothing in this builder installs or runs laya locally.
"""
import json
import os
import shutil

HERE = os.path.dirname(os.path.abspath(__file__))
FILES_DIR = os.path.dirname(HERE)
GRAPH_SRC = os.path.join(
    FILES_DIR, "laya-crpc-bns-section-decision-tree-v2.json")
BUNDLE = os.path.join(HERE, "colab_bundle")
NB_PATH = os.path.join(HERE, "live-laya-colab-test.ipynb")

# ---------------------------------------------------------------- test set
# Copied EXACTLY from the local backtest file section 3 (questions and
# ground-truth kept sections) and section 6 (test plan). Do not re-derive.
# Labels use the backtest's display names; IDS are the v2 graph section ids.
# "facts" are the question's stated facts, as annotated in the backtest
# ground-truth notes (proceeding pending, decree, divorce asked, demand
# made, violence stated). They are fixed before the run, never inferred
# from keywords at run time.
# court_expected: components the correct court answer must contain.
# escalate_expected: True unless the question is out of scope (H12), where
# the correct behaviour is to decline, not escalate. Quantum is unknown in
# every test question, so a correct system always escalates quantum
# instead of inventing an amount (backtest section 4: escalates correctly
# on all 16, H12 declines).
TEST_SET = [
    {"id": "K0", "kind": "known (2026-11-26 retest, rephrased)",
     "question": "My husband left us two years ago and gives no money. I earn forty thousand a month, it is not enough for me and my eight year old daughter. My gold worth five lakh and two lakh cash my parents gave me is with my husband's family and they will not return it. They are throwing me out of the house which is in my husband's name. Who will get my daughter, how do I get my gold back, and which court do I go to?",
     "gt_labels": ["BNSS 144", "PWDVA 20", "GWA 1890", "HMGA s.6", "WELFARE", "HMA 27", "BNS 316", "PWDVA 17", "PWDVA 18", "PWDVA 19"],
     "gt_ids": ["bnss-144", "pwdva-20", "gwa-1890", "hmga-1956-s6", "welfare-principle", "hma-27", "bns-316", "pwdva-17", "pwdva-18", "pwdva-19"],
     "facts": {"divorce_asked": False, "proceeding_pending": False, "decree": False, "demand_made": True, "violence": False},
     "court_expected": ["Family Court", "Magistrate"], "escalate_expected": True},
    {"id": "H1", "kind": "held-out, single-issue maintenance",
     "question": "My husband has not given me any money for three months. I earn fifteen thousand a month and I have two small children and no case filed anywhere.",
     "gt_labels": ["BNSS 144", "PWDVA 20"],
     "gt_ids": ["bnss-144", "pwdva-20"],
     "facts": {"divorce_asked": False, "proceeding_pending": False, "decree": False, "demand_made": None, "violence": False},
     "court_expected": ["Magistrate"], "escalate_expected": True},
    {"id": "H2", "kind": "held-out, single-issue custody, no proceeding",
     "question": "Who will get my six year old son? My husband says as the father he will take him away from me.",
     "gt_labels": ["GWA 1890", "HMGA s.6", "WELFARE"],
     "gt_ids": ["gwa-1890", "hmga-1956-s6", "welfare-principle"],
     "facts": {"divorce_asked": False, "proceeding_pending": False, "decree": False, "demand_made": None, "violence": False},
     "court_expected": ["Family Court"], "escalate_expected": True},
    {"id": "H3", "kind": "held-out, single-issue Stridhan, demand not yet made",
     "question": "My mother gave me gold at my wedding and my in-laws kept it. I have never asked them to return it.",
     "gt_labels": ["HMA 27", "BNS 316"],
     "gt_ids": ["hma-27", "bns-316"],
     "facts": {"divorce_asked": False, "proceeding_pending": False, "decree": False, "demand_made": False, "violence": False},
     "court_expected": ["Family Court", "Magistrate"], "escalate_expected": True},
    {"id": "H4", "kind": "held-out, single-issue residence",
     "question": "They changed the lock and I cannot enter my house. The house is in my husband's name.",
     "gt_labels": ["PWDVA 17", "PWDVA 18", "PWDVA 19"],
     "gt_ids": ["pwdva-17", "pwdva-18", "pwdva-19"],
     "facts": {"divorce_asked": False, "proceeding_pending": False, "decree": False, "demand_made": None, "violence": False},
     "court_expected": ["Magistrate"], "escalate_expected": True},
    {"id": "H5", "kind": "held-out, multi-issue, divorce asked",
     "question": "I want a divorce from my husband. He beats me, I need money every month and I want my daughter to stay with me.",
     "gt_labels": ["HMA 13", "BNSS 144", "PWDVA 20", "PWDVA 18", "GWA 1890", "HMGA s.6", "WELFARE"],
     "gt_ids": ["hma-13", "bnss-144", "pwdva-20", "pwdva-18", "gwa-1890", "hmga-1956-s6", "welfare-principle"],
     "facts": {"divorce_asked": True, "proceeding_pending": False, "decree": False, "demand_made": None, "violence": True},
     "court_expected": ["Family Court", "Magistrate"], "escalate_expected": True},
    {"id": "H6", "kind": "held-out, divorce NOT asked (explicit)",
     "question": "I do not want a divorce. I just want money every month from my husband and to stay in the house with my daughter.",
     "gt_labels": ["BNSS 144", "PWDVA 20", "PWDVA 17", "PWDVA 18", "PWDVA 19"],
     "gt_ids": ["bnss-144", "pwdva-20", "pwdva-17", "pwdva-18", "pwdva-19"],
     "facts": {"divorce_asked": False, "proceeding_pending": False, "decree": False, "demand_made": None, "violence": False},
     "court_expected": ["Magistrate"], "escalate_expected": True},
    {"id": "H7", "kind": "held-out, birth certificate",
     "question": "How do I get my daughter's birth certificate? The hospital did not give us one.",
     "gt_labels": ["Births and Deaths Act 1969"],
     "gt_ids": ["births-deaths-act-1969"],
     "facts": {"divorce_asked": False, "proceeding_pending": False, "decree": False, "demand_made": None, "violence": False},
     "court_expected": ["Registrar"], "escalate_expected": True},
    {"id": "H8", "kind": "held-out, salary slips missing, income unknown",
     "question": "I need maintenance but I do not have my husband's salary slips and I do not know what he earns.",
     "gt_labels": ["BNSS 144", "PWDVA 20"],
     "gt_ids": ["bnss-144", "pwdva-20"],
     "facts": {"divorce_asked": False, "proceeding_pending": False, "decree": False, "demand_made": None, "violence": False},
     "court_expected": ["Magistrate"], "escalate_expected": True},
    {"id": "H9", "kind": "held-out, income unknown, quantum asked",
     "question": "How much money can I get every month from my husband?",
     "gt_labels": ["BNSS 144", "PWDVA 20"],
     "gt_ids": ["bnss-144", "pwdva-20"],
     "facts": {"divorce_asked": False, "proceeding_pending": False, "decree": False, "demand_made": None, "violence": False},
     "court_expected": ["Magistrate"], "escalate_expected": True},
    {"id": "H10", "kind": "held-out, demand not yet made + maintenance",
     "question": "My husband has my gold and I have not asked for it back yet, and he gives no money for me and my child.",
     "gt_labels": ["HMA 27", "BNS 316", "BNSS 144", "PWDVA 20"],
     "gt_ids": ["hma-27", "bns-316", "bnss-144", "pwdva-20"],
     "facts": {"divorce_asked": False, "proceeding_pending": False, "decree": False, "demand_made": False, "violence": False},
     "court_expected": ["Family Court", "Magistrate"], "escalate_expected": True},
    {"id": "H11", "kind": "held-out, no proceeding pending, interim money asked",
     "question": "I need money while my case is going on, but I have not filed any case yet.",
     "gt_labels": ["BNSS 144", "PWDVA 20"],
     "gt_ids": ["bnss-144", "pwdva-20"],
     "facts": {"divorce_asked": False, "proceeding_pending": False, "decree": False, "demand_made": None, "violence": False},
     "court_expected": ["Magistrate"], "escalate_expected": True},
    {"id": "H12", "kind": "held-out, out of scope",
     "question": "My brother and I are fighting over our father's ancestral house. Who owns it and can I stop him selling it?",
     "gt_labels": [],
     "gt_ids": [],
     "facts": {"divorce_asked": False, "proceeding_pending": False, "decree": False, "demand_made": None, "violence": False},
     "court_expected": [], "escalate_expected": False},
    {"id": "H13", "kind": "held-out, multi-issue violence + residence + school fees",
     "question": "He beats me, throws me out of the house and gives no money for my son's school fees.",
     "gt_labels": ["PWDVA 18", "PWDVA 17", "PWDVA 19", "PWDVA 20", "BNSS 144"],
     "gt_ids": ["pwdva-18", "pwdva-17", "pwdva-19", "pwdva-20", "bnss-144"],
     "facts": {"divorce_asked": False, "proceeding_pending": False, "decree": False, "demand_made": None, "violence": True},
     "court_expected": ["Magistrate"], "escalate_expected": True},
    {"id": "H14", "kind": "held-out, proceeding pending (divorce case on in Family Court)",
     "question": "My divorce case is already going on in the Family Court. I want my son to stay with me and money for his school fees while the case goes on.",
     "gt_labels": ["HMA 13", "HMA 26", "HMGA s.6", "WELFARE", "HMA 24", "BNSS 144", "PWDVA 20"],
     "gt_ids": ["hma-13", "hma-26", "hmga-1956-s6", "welfare-principle", "hma-24", "bnss-144", "pwdva-20"],
     "facts": {"divorce_asked": True, "proceeding_pending": True, "decree": False, "demand_made": None, "violence": False},
     "court_expected": ["Family Court", "Magistrate"], "escalate_expected": True},
    {"id": "H15", "kind": "held-out, Stridhan sold",
     "question": "He sold my gold without asking me. The gold was given to me by my parents at my wedding.",
     "gt_labels": ["BNS 316", "HMA 27"],
     "gt_ids": ["bns-316", "hma-27"],
     "facts": {"divorce_asked": False, "proceeding_pending": False, "decree": False, "demand_made": True, "violence": False},
     "court_expected": ["Family Court", "Magistrate"], "escalate_expected": True},
]

# Display label for each v2 section id (backtest display names).
LABEL_BY_ID = {
    "bnss-144": "BNSS 144", "hma-24": "HMA 24", "hma-25": "HMA 25",
    "pwdva-20": "PWDVA 20", "hma-26": "HMA 26", "gwa-1890": "GWA 1890",
    "hmga-1956-s6": "HMGA s.6", "welfare-principle": "WELFARE",
    "hma-27": "HMA 27", "bns-316": "BNS 316", "pwdva-17": "PWDVA 17",
    "pwdva-18": "PWDVA 18", "pwdva-19": "PWDVA 19", "hma-13": "HMA 13",
    "hma-13b": "HMA 13B",
    "births-deaths-act-1969": "Births and Deaths Act 1969",
}


def build_bundle():
    os.makedirs(BUNDLE, exist_ok=True)
    shutil.copy2(GRAPH_SRC, os.path.join(
        BUNDLE, "laya-crpc-bns-section-decision-tree-v2.json"))
    with open(os.path.join(BUNDLE, "README.md"), "w") as f:
        f.write(README_TEXT)
    print("bundle built at", BUNDLE)
    for root, _, files in os.walk(BUNDLE):
        for fn in sorted(files):
            p = os.path.join(root, fn)
            print("  ", os.path.relpath(p, BUNDLE),
                  os.path.getsize(p), "bytes")


README_TEXT = """# Live Laya inference test — Colab bundle

Upload the contents of this folder into the Colab session (same folder as
`live-laya-colab-test.ipynb`). The notebook asks you to upload the graph
file itself with `files.upload()` in its graph cell, so keep this file
handy:

- `laya-crpc-bns-section-decision-tree-v2.json` — v2 decision graph,
  419 KB, 32 sections, 46 nodes, 77 edges (two-stage: Stage 1 layman to
  section, Stage 2 recheck inside the section, drop on failure)

The 804 MB model weights are NOT in this bundle and must NOT be
uploaded: the notebook downloads the PIXMELT/laya snapshot itself
inside Colab. The 16-question test set is embedded in the notebook.

Then run the notebook top to bottom (Runtime > Run all). No
credentials are needed. Running the install cell installs and runs
upstream `laya` code in Colab — run it only if you approve that.
Paper only — no live legal advice is produced; this scores section
classification only.
"""


def _cell_md(text):
    return {"cell_type": "markdown", "metadata": {},
            "source": text.splitlines(True)}


def _cell_code(text):
    return {"cell_type": "code", "metadata": {}, "execution_count": None,
            "outputs": [], "source": text.splitlines(True)}


def build_notebook():
    header_md = """# LIVE Laya inference test — Laya 421M + v2 two-stage decision graph

**What this is:** a LIVE run of the Laya classification model through the
v2 family-law decision graph, on the same 16 layman questions used in the
local backtest (1 known case K0 + 15 held-out H1–H15). Stage 1 is one
Laya typed decision per issue (maintenance / custody / Stridhan /
residence / violence / divorce / birth certificate), recorded with the
model's actual chosen option and probabilities. Stage 2 is the graph
recheck (divorce gate first, HMA 24 dropped with no proceeding pending,
HMA 25 dropped with no decree, custody to exactly one primary route,
Stridhan co-fire HMA 27 + BNS 316, residence PWDVA 17+18+19, quantum
always escalated, never invented). Scoring: exact section-set match,
per-section precision / recall, forbidden mappings, court correct,
escalates correctly.

**Why Colab:** the local live test was BLOCKED 2026-11-26 ~22:00 IST
(0/16 attempted, no live scores). This VM has only 323–538 MB RAM
available; the 421M model needs ~1.7 GB in FP32 / ~842 MB in FP16.
Colab free tier gives ~12–13 GB RAM, and an optional T4 GPU gives
15 GB VRAM — the model fits easily either way. Colab free tier is
enough; no paid tier is needed.

**What the local graph-walk numbers are NOT:** the backtest's 16/16
exact and the v2 adversarial 33/34 (97.1%) were a deterministic walk
through the graph's own rules on its own phrasings — a ceiling, not a
live result. A phrase-level matching version of the same graph scored
only 3/16 exact (precision 0.53). Live Laya semantic matching is the
untested middle ground. This notebook measures the live number. Do not
quote the walk numbers as live results.

**No credentials needed.** The model snapshot is public. The v2 graph
file is uploaded by you from the bundle. No other model is tested here.

**How to run:** upload this notebook to Google Drive (account used
before: nivedhbhat15@gmail.com), open it in Colab, upload
`laya-crpc-bns-section-decision-tree-v2.json` from `colab_bundle/`
when the graph cell asks, then Runtime > Run all. When it finishes,
download `live-laya-colab-results.json` and `.md` from the notebook.
"""

    env_code = """# Cell 1 — environment check (no install yet).
import os, platform, sys
print('python:', sys.version.split()[0], '| platform:', platform.machine())
try:
    import psutil
    vm = psutil.virtual_memory()
    print(f'RAM total: {vm.total/1e9:.1f} GB, available: {vm.available/1e9:.1f} GB')
except Exception as e:
    print('psutil not available:', e)
    with open('/proc/meminfo') as f:
        print([l for l in f if 'MemTotal' in l or 'MemAvailable' in l])
try:
    import torch
    print('torch:', torch.__version__, '| cuda available:', torch.cuda.is_available())
    if torch.cuda.is_available():
        print('GPU:', torch.cuda.get_device_name(0),
              f'| VRAM: {torch.cuda.get_device_properties(0).total/1e9:.1f} GB')
except Exception as e:
    print('torch not importable yet (install cell will add it):', e)
print()
print('Colab free tier is ~12-13 GB RAM; the 421M model needs ~1.7 GB FP32 / ~0.84 GB FP16,')
print('so it fits easily on CPU RAM and on a T4 GPU. Runtime > Change runtime type > T4 GPU is')
print('optional but faster; CPU-only also works.')
"""

    install_code = """# Cell 2 — install dependencies.
# *** APPROVAL REQUIRED: running this cell installs and runs upstream code
# (the `laya` package and its dependencies) inside this Colab session.
# Run it only if you approve installing/running upstream laya code here
# in Colab. This does NOT install anything on the local VM.
# laya is pinned to 0.5.5 because that is the version whose metadata was
# inspected locally on 2026-11-26 (the version the local blockers were
# found against). Do not unpin it without re-checking the load API.
!pip install -q "laya==0.5.5" torch transformers safetensors huggingface_hub
import importlib
for pkg in ['torch', 'transformers', 'safetensors', 'huggingface_hub', 'laya']:
    try:
        m = importlib.import_module(pkg)
        print(pkg, '->', getattr(m, '__version__', 'installed (no __version__)'))
    except Exception as e:
        print(pkg, 'NOT importable:', e)
"""

    inspect_code = """# Cell 3 — inspect the laya API BEFORE loading any model.
# The snapshot's test.py uses the old entry point laya.load('.'), but
# laya 0.5.5 loads a new Vega engine by default via laya.Agent(), and
# classic checkpoints need explicit naming. This cell finds out which
# entry points actually exist in the installed version, so the load
# cell below does not silently test the wrong model.
import inspect
import laya
print('laya version:', getattr(laya, '__version__', 'unknown'))
print('has laya.load:', hasattr(laya, 'load'))
print('has laya.Agent:', hasattr(laya, 'Agent'))
print('has laya.Router:', hasattr(laya, 'Router'))
for name in ['load', 'Agent', 'Router']:
    obj = getattr(laya, name, None)
    if obj is not None:
        try:
            print(f'--- {name} signature ---')
            print(inspect.signature(obj))
        except Exception as e:
            print(f'{name}: signature not available:', e)
        print(f'{name} doc (first 500 chars):', (obj.__doc__ or '')[:500])
"""

    load_code = """# Cell 4 — download the model snapshot and load the CLASSIC encoder
# checkpoint ONLY. Never load the Vega engine (the 0.8B reader that
# laya.Agent() loads by default) — that would test a different model.
# Order of attempts: (1) laya.load(local snapshot dir) if it exists,
# (2) laya.Agent(local dir, vegaml=False), (3) laya.Agent(
# 'convaiinnovations/laya', vegaml=False). The first loader that returns
# a classic checkpoint (architectures LayaTypedDecisions / ModernBERT
# encoder) wins; every failure is printed, none is hidden.
import os, time, json
os.environ['HF_HUB_OFFLINE'] = '0'  # download ON for this cell only
from huggingface_hub import snapshot_download

t0 = time.perf_counter()
model_dir = None
try:
    model_dir = snapshot_download(repo_id='PIXMELT/laya')
    print('downloaded PIXMELT/laya ->', model_dir)
except Exception as e:
    print('PIXMELT/laya snapshot_download FAILED:', repr(e))
    print('Will try the named upstream checkpoint via laya.Agent instead.')
    model_dir = None

if model_dir:
    print('snapshot contents:', sorted(os.listdir(model_dir)))
    import glob
    w = glob.glob(os.path.join(model_dir, '**', 'model.safetensors'), recursive=True)
    print('model.safetensors found:', w,
          [os.path.getsize(p) for p in w] if w else '')
    cfg = os.path.join(model_dir, 'config.json')
    if os.path.exists(cfg):
        print('config.json:', open(cfg).read()[:400])

import laya
agent = None
loader_used = None
errors = {}
if model_dir and hasattr(laya, 'load'):
    try:
        agent = laya.load(model_dir)
        loader_used = 'laya.load(local PIXMELT snapshot dir)'
        print('LOADED via', loader_used)
    except Exception as e:
        errors['laya.load'] = repr(e)
        print('laya.load FAILED:', repr(e))
if agent is None and model_dir and hasattr(laya, 'Agent'):
    for kwargs in ({'vegaml': False}, {}):
        try:
            agent = laya.Agent(model_dir, **kwargs)
            loader_used = f'laya.Agent(local dir, {kwargs})'
            print('LOADED via', loader_used)
            break
        except Exception as e:
            errors[f'laya.Agent(local, {kwargs})'] = repr(e)
            print(f'laya.Agent(local dir, {kwargs}) FAILED:', repr(e))
if agent is None and hasattr(laya, 'Agent'):
    for kwargs in ({'vegaml': False}, {}):
        try:
            agent = laya.Agent('convaiinnovations/laya', **kwargs)
            loader_used = f'laya.Agent(convaiinnovations/laya, {kwargs})'
            print('LOADED via', loader_used, '(upstream named checkpoint)')
            break
        except Exception as e:
            errors[f'laya.Agent(upstream, {kwargs})'] = repr(e)
            print(f'laya.Agent(convaiinnovations/laya, {kwargs}) FAILED:', repr(e))
if agent is None:
    raise RuntimeError(
        'NO classic Laya checkpoint could be loaded. Failures: ' + json.dumps(errors, indent=1)
        + '\\nDo NOT continue: running the test without a loaded classic checkpoint would '
          'produce fake scores. Fix the loader (pin an older laya version matching the '
          'snapshot, or load DecisionModel directly from the snapshot rl_common.py) and re-run.')

print()
print('agent object:', type(agent))
print('loader used:', loader_used)
# Guard: refuse a Vega-engine load. The classic checkpoint is ModernBERT
# (architectures LayaTypedDecisions). If the loaded agent reports a Vega
# reader, stop here — that is a different model.
agent_repr = repr(agent) + str(getattr(agent, 'cfg', '')) + str(getattr(agent, 'config', ''))
if 'vega' in agent_repr.lower() and 'LayaTypedDecisions' not in agent_repr:
    raise RuntimeError('Loaded agent looks like the Vega engine, not the classic '
                       'ModernBERT checkpoint. Stopping — wrong model.')
print('classic-checkpoint guard: passed (no Vega-only load detected)')
try:
    import torch
    print('torch cuda available:', torch.cuda.is_available())
    if torch.cuda.is_available():
        print('device: GPU', torch.cuda.get_device_name(0))
    else:
        print('device: CPU')
except Exception as e:
    print('device check failed:', e)
load_secs = time.perf_counter() - t0
print(f'load time: {load_secs:.1f} s')
try:
    import psutil
    vm = psutil.virtual_memory()
    print(f'RAM at load: total {vm.total/1e9:.1f} GB, available {vm.available/1e9:.1f} GB, used {vm.used/1e9:.1f} GB')
except Exception:
    pass
LOAD_INFO = {'loader_used': loader_used, 'load_seconds': round(load_secs, 1),
             'errors_before_success': errors}
print('LOAD_INFO =', LOAD_INFO)
"""

    graph_code = """# Cell 5 — upload the v2 decision graph and verify it.
# Upload laya-crpc-bns-section-decision-tree-v2.json from colab_bundle/
# when the file picker appears. The graph is the source of truth for
# section ids, node questions/options and the root issue->section map.
from google.colab import files
import json
print('Upload laya-crpc-bns-section-decision-tree-v2.json now (file picker).')
uploaded = files.upload()
print('uploaded:', list(uploaded.keys()))
GRAPH_FILE = 'laya-crpc-bns-section-decision-tree-v2.json'
assert GRAPH_FILE in uploaded, f'{GRAPH_FILE} was not uploaded — upload it and re-run this cell.'
GRAPH = json.loads(uploaded[GRAPH_FILE].decode('utf-8'))
n_sections = len(GRAPH['sections'])
n_nodes = len(GRAPH['nodes'])
n_edges = len(GRAPH['edges'])
print(f'verified: {n_sections} sections, {n_nodes} nodes, {n_edges} edges')
assert (n_sections, n_nodes, n_edges) == (32, 46, 77), (
    f'Graph counts do not match v2 (expected 32/46/77, got {n_sections}/{n_nodes}/{n_edges}). '
    'You may have uploaded the v1 graph — upload the v2 file and re-run.')
NODES = {n['node_id']: n for n in GRAPH['nodes']}
SECTION_IDS = {s['id'] for s in GRAPH['sections']}
print('graph OK — 32 sections / 46 nodes / 77 edges. Root node:',
      NODES['root:issue-classification']['question'][:80], '...')
"""

    testset_code = """# Cell 6 — the 16-question test set + ground truth.
# Copied EXACTLY from the local backtest file section 3 (questions and
# ground-truth kept sections) and section 6 (test plan). Ground truth was
# fixed BEFORE any run. "facts" are the question's stated facts as
# annotated in the backtest (proceeding pending, decree, divorce asked,
# demand made, violence stated) — fixed annotations, never inferred
# from keywords at run time.
TEST_SET = """ + json.dumps(TEST_SET, indent=1) + """

LABEL_BY_ID = """ + json.dumps(LABEL_BY_ID, indent=1) + """

print(f'test set loaded: {len(TEST_SET)} questions')
for t in TEST_SET:
    print(f"  {t['id']:3s} [{t['kind']}] GT={t['gt_labels']}")
assert [t['id'] for t in TEST_SET] == ['K0'] + [f'H{i}' for i in range(1, 16)], 'test set IDs are not K0 + H1-H15'
assert all(set(t['gt_ids']) <= set(LABEL_BY_ID) for t in TEST_SET), 'GT id with no label'
print('test set OK: 16 questions (K0 + H1-H15), ground truth fixed before the run.')
"""

    run_code = """# Cell 7 — LIVE Stage 1 (Laya typed decisions) + Stage 2 (graph recheck).
# HARD RULES for this cell:
#  - Every issue pick comes from agent.predict(). If a predict call
#    raises, the question is recorded as an ERROR and scored as a miss.
#    There is NO fallback to keyword / phrase / rule matching — a
#    fallback would be a graph walk, not a live test, and would fake
#    the score.
#  - Stage 1 = one `noul` question per issue (7 issues). A `noul`
#    answer is a probability; >= 0.50 means the issue fired.
#  - Sub-choices (choice questions) run ONLY for issues that fired,
#    using the option lists straight from the uploaded v2 graph nodes.
#  - Stage 2 is deterministic and applies ONLY to the live Stage 1
#    picks: divorce gate first, HMA 24 dropped with no proceeding,
#    HMA 25 dropped with no decree, custody to exactly one primary,
#    Stridhan co-fire HMA 27 + BNS 316, residence from the sub-choice,
#    quantum always escalated, never invented. A section failing its
#    recheck is DROPPED with a reason, not kept.
import time

ISSUES = [
    ('maintenance', 'Does this question ask for monthly money or maintenance for the wife or a child?'),
    ('custody', 'Does this question ask who will get or look after the child, or about guardianship or custody?'),
    ('stridhan', 'Does this question ask about gold, cash or gifts given to the wife at marriage that are held by the husband or his family?'),
    ('residence', 'Does this question ask about staying in, or being thrown out of, the shared house, or about protection from threats or violence at home?'),
    ('violence', 'Does this question say the husband beats, threatens or harasses the wife?'),
    ('divorce', 'Does this question ask for a divorce, or for ending the marriage?'),
    ('birth_certificate', "Does this question ask how to get a child's birth certificate?"),
]
ISSUE_NODE = {
    'maintenance': 'maintenance:maintenance-root',
    'custody': 'custody:custody_sub_issue_choice',
    'stridhan': 'stridhan:stridhan-subissue',
    'residence': 'residence:residence_sub_issue',
    'divorce': 'procedure:divorce-gate',
}
ISSUE_EXTRA_NODE = {
    'stridhan': 'stridhan:civil-vs-criminal',
    'residence': 'residence:protection_vs_residence',
}


def _parse(answer, qtype):
    # Laya returns result['answers'][name][type]. Be liberal in what we
    # accept (str / float / dict) but record the RAW answer too, so any
    # parsing surprise is visible in the results file.
    if isinstance(answer, dict):
        for k in ('choice', 'value', 'option', 'answer', 'probability', 'score'):
            if k in answer:
                return answer[k]
        return str(answer)
    return answer


def _ask(payload, body):
    # One forward pass for every question in the payload.
    res = agent.predict({'body': body}, payload)
    return res['answers']


def stage2(fired, sub, facts):
    kept = set()
    dropped = []
    esc = []
    if 'maintenance' in fired:
        kept |= {'bnss-144', 'pwdva-20'}
        ans = sub.get('maintenance:maintenance-root', '')
        if 'interim maintenance during a pending HMA proceeding' in ans:
            kept.add('hma-24')
        if 'permanent alimony at/after an HMA decree' in ans:
            kept.add('hma-25')
    if 'custody' in fired:
        kept |= {'gwa-1890', 'hmga-1956-s6', 'welfare-principle'}
        if facts['proceeding_pending']:
            kept.add('hma-26')
    if 'stridhan' in fired:
        kept |= {'hma-27', 'bns-316'}
        if facts['demand_made'] is False:
            esc.append('Stridhan: make a written demand for return first, then re-evaluate BNS s.316')
    if 'residence' in fired:
        r = sub.get('residence:residence_sub_issue', '')
        p = sub.get('residence:protection_vs_residence', '')
        res = set()
        if 'Already thrown out' in r or 'Combination' in r:
            res |= {'pwdva-17', 'pwdva-18', 'pwdva-19'}
        elif 'Threatened with eviction' in r:
            res |= {'pwdva-17', 'pwdva-19'}
        elif 'Violence, threats' in r:
            res |= {'pwdva-18'}
        elif 'Money cut off' in r:
            res |= {'pwdva-20'}
        if 'Both' in p:
            res |= {'pwdva-17', 'pwdva-18', 'pwdva-19'}
        elif 'Stop the violence' in p:
            res |= {'pwdva-18'}
        elif 'Secure the right to stay' in p:
            res |= {'pwdva-17', 'pwdva-19'}
        elif 'Money only' in p:
            res |= {'pwdva-20'}
        if not res:
            dropped.append(('residence sections', 'residence fired but the sub-choice gave no section set — recorded as a miss, not guessed'))
        kept |= res
    if 'violence' in fired and 'residence' not in fired:
        kept.add('pwdva-18')
    if 'divorce' in fired:
        gate = sub.get('procedure:divorce-gate', '')
        if facts['divorce_asked'] and 'open gate' in gate:
            kept.add('hma-13')
        elif facts['divorce_asked']:
            dropped.append(('hma-13', 'divorce issue fired but the divorce-gate choice did not open the gate'))
        # HMA 13B (mutual consent) is never added: no test question states mutual consent.
    if 'birth_certificate' in fired:
        kept.add('births-deaths-act-1969')
    # --- recheck / drops (backtest rules) ---
    if not facts['divorce_asked']:
        for s in ('hma-13', 'hma-13b'):
            if s in kept:
                kept.remove(s)
                dropped.append((s, 'divorce gate: divorce not asked'))
    if not facts['proceeding_pending'] and 'hma-24' in kept:
        kept.remove('hma-24')
        dropped.append(('hma-24', 'no HMA proceeding pending'))
    if not facts['decree'] and 'hma-25' in kept:
        kept.remove('hma-25')
        dropped.append(('hma-25', 'no decree'))
    if not facts['proceeding_pending'] and 'hma-26' in kept:
        kept.remove('hma-26')
        dropped.append(('hma-26', 'no HMA proceeding pending — GWA 1890 route'))
    if kept:
        esc.append("Quantum: husband's income / school fees unknown — escalate the amount, never invent it")
        esc.append("Ask husband's income (estimate/range), school-fee amount, where husband lives now; never demand salary slips")
    return kept, dropped, esc


def court_for(kept_ids):
    courts = set()
    if kept_ids & {'hma-24', 'hma-25', 'hma-26', 'hma-27', 'hma-13', 'hma-13b'}:
        courts.add('Family Court')
    if kept_ids & {'gwa-1890', 'hmga-1956-s6', 'welfare-principle'}:
        courts.add('Family Court')
    if kept_ids & {'bnss-144', 'pwdva-17', 'pwdva-18', 'pwdva-19', 'pwdva-20', 'bns-316'}:
        courts.add('Magistrate')
    if kept_ids == {'births-deaths-act-1969'}:
        courts.add('Registrar')
    return courts


RESULTS = []
for t in TEST_SET:
    q = t['question']
    facts = t['facts']
    t0 = time.perf_counter()
    rec = {'id': t['id'], 'question': q, 'gt_ids': t['gt_ids'],
           'gt_labels': t['gt_labels'], 'facts': facts,
           'stage1_raw': {}, 'stage1_probs': {}, 'fired_issues': [],
           'sub_choices': {}, 'candidates_before_stage2': [],
           'kept_ids': [], 'dropped': [], 'escalations': [],
           'court_live': [], 'error': None, 'latency_s': None}
    try:
        payload = {}
        for name, instr in ISSUES:
            payload[f'issue_{name}'] = {'type': 'noul', 'instructions': instr}
        ans = _ask(payload, q)
        for name, _ in ISSUES:
            raw = _parse(ans[f'issue_{name}']['noul'], 'noul')
            rec['stage1_raw'][name] = raw
            try:
                p = float(raw)
            except Exception:
                p = None
            rec['stage1_probs'][name] = p
            if p is not None and p >= 0.50:
                rec['fired_issues'].append(name)
        # Sub-choices, only for fired issues, options from the graph.
        sub_payload = {}
        sub_nodes = []
        for iss in rec['fired_issues']:
            for node_id in [ISSUE_NODE.get(iss), ISSUE_EXTRA_NODE.get(iss)]:
                if node_id and node_id in NODES:
                    node = NODES[node_id]
                    opts = node.get('options')
                    if isinstance(opts, list) and opts and all(isinstance(o, str) for o in opts):
                        sub_payload[node_id] = {
                            'type': 'choice',
                            'instructions': node.get('question', node_id),
                            'criteria': {f'opt{i}': o for i, o in enumerate(opts)},
                        }
                        sub_nodes.append((node_id, opts))
        if sub_payload:
            ans2 = _ask(sub_payload, q)
            for node_id, opts in sub_nodes:
                raw = _parse(ans2[node_id]['choice'], 'choice')
                # criteria keys are opt0..; map back to the option text.
                if isinstance(raw, str) and raw.startswith('opt') and raw[3:].isdigit():
                    raw = opts[int(raw[3:])]
                rec['sub_choices'][node_id] = raw
        kept, dropped, esc = stage2(set(rec['fired_issues']), rec['sub_choices'], facts)
        rec['kept_ids'] = sorted(kept)
        rec['candidates_before_stage2'] = sorted(kept | {d[0] for d in dropped if d[0] in SECTION_IDS})
        rec['dropped'] = [[a, b] for a, b in dropped]
        rec['escalations'] = esc
        rec['court_live'] = sorted(court_for(kept))
    except Exception as e:
        rec['error'] = repr(e)
        print(f"{t['id']}: LIVE ERROR — {e!r} (scored as a miss, no fallback)")
    rec['latency_s'] = round(time.perf_counter() - t0, 2)
    RESULTS.append(rec)
    print(f"{t['id']}: fired={rec['fired_issues']} kept={[LABEL_BY_ID.get(s, s) for s in rec['kept_ids']]} "
          f"GT={t['gt_labels']} latency={rec['latency_s']}s error={rec['error']}")
print()
print(f'Live run complete: {len(RESULTS)} questions, '
      f"{sum(1 for r in RESULTS if r['error'] is None)}/16 with no model error.")
"""

    score_code = """# Cell 8 — score, save, download.
# Scoring is exactly the backtest's: exact section-set match,
# per-section precision / recall, forbidden mappings, court correct,
# escalates correctly. Two forbidden counts are reported:
#  - forbidden_before_recheck: forbidden sections in the candidate set
#    BEFORE Stage 2 drops them (the meaningful live number — it shows
#    what Stage 1 actually picked wrong).
#  - forbidden_after_recheck: forbidden sections left AFTER Stage 2.
#    This is 0 by construction whenever Stage 2 ran, because Stage 2
#    drops exactly those sections; do NOT quote it as model accuracy.
# Prose-level forbidden errors (Rajnesh cited for Stridhan, Satish
# cited for custody, residence called 'tenancy rights') CANNOT be
# measured from section sets — this test classifies sections, it does
# not generate answer prose. They are reported as NOT MEASURED, not as 0.
import json

FORBIDDEN_RULES = [
    ('hma-13', 'HMA 13/13B with no divorce asked', lambda f: not f['divorce_asked']),
    ('hma-13b', 'HMA 13/13B with no divorce asked', lambda f: not f['divorce_asked']),
    ('hma-24', 'HMA 24 with no proceeding pending', lambda f: not f['proceeding_pending']),
    ('hma-25', 'HMA 25 with no decree', lambda f: not f['decree']),
    ('hma-26', 'HMA 26 with no proceeding pending', lambda f: not f['proceeding_pending']),
]


def _pr(pred, gt):
    pred, gt = set(pred), set(gt)
    tp = len(pred & gt)
    prec = tp / len(pred) if pred else (1.0 if not gt else 0.0)
    rec = tp / len(gt) if gt else (1.0 if not pred else 0.0)
    return tp, len(pred) - tp, len(gt) - tp, prec, rec


rows = []
tot_tp = tot_fp = tot_fn = 0
for t, r in zip(TEST_SET, RESULTS):
    pred, gt = r['kept_ids'], t['gt_ids']
    tp, fp, fn, prec, rec = _pr(pred, gt)
    tot_tp += tp; tot_fp += fp; tot_fn += fn
    fb = [rule for s, rule, cond in FORBIDDEN_RULES
          if s in r['candidates_before_stage2'] and cond(t['facts'])]
    fa = [rule for s, rule, cond in FORBIDDEN_RULES
          if s in pred and cond(t['facts'])]
    court_ok = set(r['court_live']) == set(t['court_expected'])
    esc_live = bool(r['escalations'])
    esc_ok = esc_live == t['escalate_expected']
    rows.append({'id': t['id'], 'exact': pred == gt if set(pred) == set(gt) else False,
                 'precision': round(prec, 3), 'recall': round(rec, 3),
                 'tp': tp, 'fp': fp, 'fn': fn,
                 'pred_labels': [LABEL_BY_ID.get(s, s) for s in pred],
                 'gt_labels': t['gt_labels'],
                 'forbidden_before_recheck': fb, 'forbidden_after_recheck': fa,
                 'court_live': r['court_live'], 'court_expected': t['court_expected'],
                 'court_correct': court_ok,
                 'escalates_live': esc_live, 'escalates_expected': t['escalate_expected'],
                 'escalates_correct': esc_ok, 'error': r['error'],
                 'latency_s': r['latency_s']})

n = len(rows)
n_exact = sum(1 for x in rows if x['exact'])
micro_p = tot_tp / (tot_tp + tot_fp) if (tot_tp + tot_fp) else 0.0
micro_r = tot_tp / (tot_tp + tot_fn) if (tot_tp + tot_fn) else 0.0
agg = {
    'system': 'Laya 421M (classic ModernBERT checkpoint) + v2 two-stage graph, LIVE in Colab',
    'loader': LOAD_INFO,
    'n_questions': n,
    'exact_section_set_match': f'{n_exact}/{n}',
    'mean_precision': round(sum(x['precision'] for x in rows) / n, 3),
    'mean_recall': round(sum(x['recall'] for x in rows) / n, 3),
    'micro_precision': round(micro_p, 3),
    'micro_recall': round(micro_r, 3),
    'micro_tp_fp_fn': [tot_tp, tot_fp, tot_fn],
    'forbidden_before_recheck_total': sum(len(x['forbidden_before_recheck']) for x in rows),
    'forbidden_after_recheck_total': sum(len(x['forbidden_after_recheck']) for x in rows),
    'court_correct': f"{sum(1 for x in rows if x['court_correct'])}/{n}",
    'escalates_correct': f"{sum(1 for x in rows if x['escalates_correct'])}/{n}",
    'questions_with_model_error': sum(1 for x in rows if x['error']),
    'prose_forbidden_mappings': 'NOT MEASURED — section classification only, no answer prose generated',
    'walk_ceiling_reference': 'Graph-walk ceiling was 16/16 exact (deterministic walk, NOT live). Do not compare live numbers to it as if it were a baseline.',
}
print('=== LIVE Laya + v2 graph — Colab results ===')
for k, v in agg.items():
    print(f'{k}: {v}')
print()
print(f"{'ID':4s} {'exact':>5s} {'prec':>5s} {'rec':>5s} {'fb':>2s} {'court':>5s} {'esc':>3s}  predicted sections")
for x in rows:
    print(f"{x['id']:4s} {str(x['exact']):>5s} {x['precision']:5.3f} {x['recall']:5.3f} "
          f"{len(x['forbidden_before_recheck']):2d} {str(x['court_correct']):>5s} {str(x['escalates_correct']):>3s}  "
          f"{', '.join(x['pred_labels']) if x['pred_labels'] else '(none)'}"
    )
print()
print('fb = forbidden mappings BEFORE Stage 2 recheck (live Stage 1 errors).')
print('court = court correct, esc = escalates correctly.')

out = {'aggregate': agg, 'per_question': rows, 'raw_live_runs': RESULTS,
       'load_info': LOAD_INFO}
with open('live-laya-colab-results.json', 'w') as f:
    json.dump(out, f, indent=1, ensure_ascii=False)
md = ['# Live Laya inference test — Colab run (Laya 421M + v2 graph)',
      '',
      '## Aggregate (live, measured in Colab)',
      '']
for k, v in agg.items():
    md.append(f'- **{k}**: {v}')
md += ['', '## Per-question', '',
       '| ID | Exact | Precision | Recall | Forbidden (before recheck) | Court | Escalates | Predicted |',
       '|----|-------|-----------|--------|----------------------------|-------|-----------|-----------|']
for x in rows:
    md.append(f"| {x['id']} | {x['exact']} | {x['precision']} | {x['recall']} | "
              f"{len(x['forbidden_before_recheck'])} | {x['court_correct']} | {x['escalates_correct']} | "
              f"{', '.join(x['pred_labels']) if x['pred_labels'] else '(none)'} |")
md += ['', 'Forbidden-after-recheck is 0 by construction when Stage 2 ran (Stage 2 drops those sections); '
       'quote forbidden-before-recheck as the live error count.',
       'Prose-level forbidden mappings (Rajnesh / Satish / tenancy label) are NOT MEASURED here.',
       '']
with open('live-laya-colab-results.md', 'w') as f:
    f.write('\\n'.join(md))
print('saved live-laya-colab-results.json and live-laya-colab-results.md')
from google.colab import files as _cf
_cf.download('live-laya-colab-results.json')
_cf.download('live-laya-colab-results.md')
print('Downloaded both result files. Send them back to Muse to record the live score.')
"""

    cells = [
        _cell_md(header_md),
        _cell_code(env_code),
        _cell_code(install_code),
        _cell_code(inspect_code),
        _cell_code(load_code),
        _cell_code(graph_code),
        _cell_code(testset_code),
        _cell_code(run_code),
        _cell_code(score_code),
    ]

    for i, c in enumerate(cells):
        c["id"] = f"cell-{i}"
    nb = {"nbformat": 4, "nbformat_minor": 5,
          "metadata": {"kernelspec": {"display_name": "Python 3",
                                      "language": "python",
                                      "name": "python3"},
                       "language_info": {"name": "python", "version": "3.12"}},
          "cells": cells}
    with open(NB_PATH, "w") as f:
        json.dump(nb, f, indent=1)
    print("notebook written:", NB_PATH, os.path.getsize(NB_PATH), "bytes")
    return NB_PATH


def validate(nb_path):
    with open(nb_path) as f:
        nb = json.load(f)
    assert nb["nbformat"] == 4, "nbformat is not 4"
    assert len(nb["cells"]) == 9, f"expected 9 cells, got {len(nb['cells'])}"
    assert nb["cells"][0]["cell_type"] == "markdown"
    assert all(c["cell_type"] == "code" for c in nb["cells"][1:])
    src = "\n".join("".join(c.get("source", [])) for c in nb["cells"])
    # All 16 question IDs present (embedded test set).
    for qid in ["K0"] + [f"H{i}" for i in range(1, 16)]:
        assert f"'{qid}'" in src or f'"{qid}"' in src, f"missing question {qid}"
    # No local absolute paths, no workspace paths.
    for bad in ("/home/hatch", "~/workspace", "workspace/"):
        assert bad not in src, f"notebook contains local path {bad!r}"
    # No other-model references at all.
    bad_word = "ll" + "ama"
    assert bad_word not in src.lower(), "notebook contains a reference to another model"
    # No invented live scores: the scoring cell computes them; no
    # hard-coded live result may appear in the notebook source.
    for bad in ("16/16 exact (live", "exact_section_set_match': '16/16",
                "live exact-match: 16"):
        assert bad not in src, f"notebook contains an invented live score {bad!r}"
    # No keyword/phrase fallback anywhere in the run cell.
    assert "phrasebook" not in src.lower(), "notebook references phrasebook matching"
    try:
        import nbformat
        nbformat.validate(nb)
        print("nbformat.validate: PASS")
    except ImportError:
        print("nbformat not installed locally — skipped nbformat.validate, "
              "manual schema checks above passed")
    # Graph counts in the bundle copy match v2.
    g = json.load(open(os.path.join(
        BUNDLE, "laya-crpc-bns-section-decision-tree-v2.json")))
    assert (len(g["sections"]), len(g["nodes"]), len(g["edges"])) == (32, 46, 77)
    print("validation: PASS — 9 cells, 16 questions, no local paths, "
          "no other-model references, graph 32/46/77")


if __name__ == "__main__":
    build_bundle()
    path = build_notebook()
    validate(path)
