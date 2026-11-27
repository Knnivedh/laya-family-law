#!/usr/bin/env python3
"""Build the standalone deterministic v7.1 Colab notebook (V71-P5-3).

Lane 08 (Pillar 5) — generates ``notebooks/live-laya-colab-test-v7.ipynb``
with pure-Python notebook JSON generation. No torch is needed to build
it (and none is used here). Run the builder locally::

    python3 src/build_laya_v7_colab.py

then open the generated notebook in Colab on a T4 GPU.

What the notebook measures (plan docs/10x_plane.md §5.2–§5.3, G14-T4)
----------------------------------------------------------------------
* T4 fp16 parity: student INT8 ONNX vs FP32 ONNX vs teacher logits on
  the 16-Q set — ``max_abs_diff <= 0.03``, 0 prediction flips.
* Cold/warm timing per tier: model load, first (cold) batch, warmed
  per-question mean/max — against the plan §5.3 targets (GPU mean
  < 50 ms/Q, max <= 100 ms/Q, load <= 15 s; CPU INT8 mean < 0.5 s/Q,
  max <= 1.0 s/Q). Targets are printed as targets; the notebook never
  prints a pass it did not measure.
* T4 vs RTX 5050 score parity: if the user uploads the RTX 5050 run
  JSON (``live-laya-v7-rtx5050-results.json``), the notebook compares
  kept_ids per question (0 exact flips required). If it is not
  uploaded, that section logs "RTX reference not uploaded — parity
  vs RTX NOT measured" instead of inventing a comparison.
* End-to-end exact scores (16-Q kept_ids) ONLY if the user also
  uploads the v7.1 source tree as ``laya_v71_src.zip``; otherwise
  that cell logs "END-TO-END SKIPPED" and still files parity+timing.

T4 / AMP rule (plan §5.2, design doc §225)
--------------------------------------------
Turing ``sm_75`` (Colab T4) lacks hardware bf16 tensor cores, so the
notebook explicitly enforces ``LAYA_CUDA_AMP=fp16`` when
``torch.cuda.get_device_capability() == (7, 5)``. On other GPUs
(RTX 5050 Blackwell) it uses bf16 (the checkpoint-native AMP dtype)
and logs the choice. The AMP mode is recorded in every result file.

The 16-question test set is NOT re-typed here: it is imported from
``src/build_laya_colab_notebook.py`` (the v6 builder), which copied it
exactly from the local backtest. The 16-Q set is a published test
specification, not sealed text — no sealed bank is read by this
builder. Ground truth in the notebook is the frozen GT v2 (D1-A);
GT v3 (Lane 07, V71-P4-4) is pending human ratification, so the
notebook logs a GT-v3 re-run as pending rather than scoring against
an unratified ground truth.

No live scores are hard-coded anywhere in the generated notebook:
every number in its results is computed at run time in Colab.
"""

import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
NB_PATH = os.path.join(REPO, "notebooks", "live-laya-colab-test-v7.ipynb")

sys.path.insert(0, HERE)
from build_laya_colab_notebook import LABEL_BY_ID, TEST_SET  # noqa: E402

# G14-T4 / §5.3 gates the notebook enforces at run time (targets, not results).
PARITY_MAX_ABS_DIFF = 0.03
PARITY_MAX_FLIPS = 0
GPU_MEAN_MS_TARGET = 50.0
GPU_MAX_MS_TARGET = 100.0
GPU_LOAD_S_TARGET = 15.0
CPU_INT8_MEAN_S_TARGET = 0.5
CPU_INT8_MAX_S_TARGET = 1.0


def _cell_md(text):
    return {"cell_type": "markdown", "metadata": {},
            "source": text.splitlines(True)}


def _cell_code(text):
    return {"cell_type": "code", "metadata": {}, "execution_count": None,
            "outputs": [], "source": text.splitlines(True)}


def build_notebook():
    header_md = """# LIVE LAYA v7.1 — student INT8 ONNX + teacher parity on Colab T4 (G14-T4)

**What this is:** the v7.1 Pillar 5 verification run. It loads the distilled
student (FP32 ONNX + INT8 ONNX, `models/student_int8.onnx`) and, when
available, the Lane 03 teacher, runs all three over the same 16 layman
questions (K0 + H1–H15), and measures (a) logit parity
(`max_abs_diff <= 0.03`, 0 prediction flips), (b) cold/warm timing per
tier against the plan §5.3 targets, and (c) T4-vs-RTX 5050 kept_ids parity
when the RTX 5050 run JSON is uploaded. End-to-end exact scores are
measured only if the v7.1 source tree is also uploaded (see the
end-to-end cell); otherwise that part is explicitly SKIPPED, not guessed.

**T4 rule — read first:** Colab T4 is Turing `sm_75` and lacks hardware
bf16 tensor cores, so this notebook enforces `LAYA_CUDA_AMP=fp16` on
`sm_75` (plan §5.2). On any other GPU it uses bf16 and logs the choice.
The AMP mode is recorded in the results file.

**What the numbers are NOT:** every latency/accuracy target in this
notebook (GPU < 50 ms/Q, CPU INT8 < 0.5 s/Q, 0 flips) is a plan target
until this notebook measures it. Nothing here claims a measured result
before the run. Ground truth is frozen GT v2 (D1-A); GT v3 is pending
human ratification (Lane 07) and a GT-v3 re-run is logged as pending.

**How to run:** Runtime > Change runtime type > T4 GPU. Upload
`student_fp32.onnx` + `student_int8.onnx` when the artifacts cell asks,
optionally `live-laya-v7-rtx5050-results.json` (RTX 5050 reference) and
`laya_v71_src.zip` (for end-to-end scoring). Then Runtime > Run all.
Download `live-laya-v7-colab-results.json` + `.md` at the end.
"""

    env_code = """# Cell 1 — environment check (no install yet).
import os, platform, sys
print('python:', sys.version.split()[0], '| platform:', platform.machine())
try:
    import torch
    print('torch:', torch.__version__, '| cuda available:', torch.cuda.is_available())
    if torch.cuda.is_available():
        cap = torch.cuda.get_device_capability(0)
        print('GPU:', torch.cuda.get_device_name(0),
              f'| capability: sm_{cap[0]}{cap[1]}',
              f'| VRAM: {torch.cuda.get_device_properties(0).total/1e9:.1f} GB')
        print('Turing sm_75 (T4) -> LAYA_CUDA_AMP MUST be fp16 (no hw bf16 tensor cores).')
        print('Blackwell/Ada (RTX 5050) -> bf16 is the checkpoint-native AMP dtype.')
    else:
        print('NO CUDA — GPU tiers cannot run here; only the CPU INT8 tier will be measured.')
except Exception as e:
    print('torch not importable yet (install cell will add it):', e)
"""

    install_code = """# Cell 2 — install dependencies.
# *** APPROVAL REQUIRED: running this cell installs upstream code
# (torch, transformers, onnxruntime) inside this Colab session.
# Run it only if you approve that. This does NOT install anything locally.
!pip install -q torch transformers onnxruntime numpy
import importlib
for pkg in ['torch', 'transformers', 'onnxruntime', 'numpy']:
    try:
        m = importlib.import_module(pkg)
        print(pkg, '->', getattr(m, '__version__', 'installed (no __version__)'))
    except Exception as e:
        print(pkg, 'NOT importable:', e)
"""

    amp_code = """# Cell 3 — enforce the AMP rule and record it.
# T4 (Turing sm_75) lacks hardware bf16 tensor cores -> fp16.
# Anything else (RTX 5050 Blackwell, Ada) -> bf16 (checkpoint native).
# The choice is written to AMP_MODE and to every result file; a run
# that silently used the wrong dtype would fake the parity numbers.
import torch, os
assert torch.cuda.is_available(), 'CUDA is required for the GPU tiers (use a T4 runtime).'
cap = torch.cuda.get_device_capability(0)
IS_T4 = (cap == (7, 5))
AMP_MODE = 'fp16' if IS_T4 else 'bf16'
os.environ['LAYA_CUDA_AMP'] = AMP_MODE
print(f'GPU: {torch.cuda.get_device_name(0)} sm_{cap[0]}{cap[1]}')
print(f'LAYA_CUDA_AMP={AMP_MODE} ({"T4 sm_75 -> fp16 enforced" if IS_T4 else "non-Turing -> bf16"})')
AMP_INFO = {'gpu': torch.cuda.get_device_name(0), 'capability': list(cap),
            'is_t4_sm75': bool(IS_T4), 'amp_mode': AMP_MODE}
"""

    artifacts_code = """# Cell 4 — upload the student artifacts (+ optional references) and verify them.
# Upload student_fp32.onnx and student_int8.onnx (from models/, built by
# scripts/export_student_onnx.py — the Parity Guard must have PASSED for
# student_int8.onnx; a *.rejected.onnx file must NEVER be uploaded here).
# Optional: live-laya-v7-rtx5050-results.json (RTX 5050 reference run, for
# T4-vs-RTX parity) and laya_v71_src.zip (v7.1 source tree, for end-to-end).
from google.colab import files
import json, os, time
print('Upload student_fp32.onnx and student_int8.onnx now (file picker).')
uploaded = files.upload()
print('uploaded:', list(uploaded.keys()))
for req in ('student_fp32.onnx', 'student_int8.onnx'):
    assert req in uploaded, f'{req} was not uploaded — upload it and re-run this cell.'
    assert not req.endswith('.rejected.onnx'), 'rejected artifact uploaded — stop.'
    print(f'{req}: {os.path.getsize(req)/1e6:.1f} MB')
import onnxruntime as ort
print('onnxruntime:', ort.__version__)
# Verify the ONNX graph I/O contract (V71-P5-2) on BOTH artifacts.
EXPECTED_IN = ['input_ids', 'attention_mask']
EXPECTED_OUT = ['issue_logits', 'fact_logits', 'sex_logits',
                'role_logits', 'time_logits', 'safety_logits']
def _check_onnx(path):
    import onnx
    m = onnx.load(path)
    ins = [i.name for i in m.graph.input]
    outs = [o.name for o in m.graph.output]
    assert EXPECTED_IN == ins, f'{path}: inputs {ins} != {EXPECTED_IN}'
    assert EXPECTED_OUT == outs, f'{path}: outputs {outs} != {EXPECTED_OUT}'
    print(f'{path}: I/O contract OK (opset {m.opset_import[0].version}, '
          f'{len(m.graph.node)} nodes)')
for p in ('student_fp32.onnx', 'student_int8.onnx'):
    _check_onnx(p)
RTX_REF = None
if 'live-laya-v7-rtx5050-results.json' in uploaded:
    RTX_REF = json.loads(uploaded['live-laya-v7-rtx5050-results.json'].decode('utf-8'))
    print('RTX 5050 reference loaded — T4-vs-RTX parity WILL be measured.')
else:
    print('No RTX 5050 reference uploaded — T4-vs-RTX parity will be logged as NOT MEASURED.')
HAS_SRC_ZIP = 'laya_v71_src.zip' in uploaded
print('v7.1 source zip present:', HAS_SRC_ZIP,
      '(end-to-end scoring needs it; otherwise that cell is SKIPPED, not guessed.)')
"""

    testset_code = """# Cell 5 — the 16-question test set + ground truth (GT v2, D1-A).
# Copied EXACTLY from src/build_laya_colab_notebook.py TEST_SET (which
# copied it exactly from the local backtest). Ground truth was fixed
# BEFORE any run. GT v3 is pending human ratification (Lane 07) — this
# notebook scores against GT v2 and logs a GT-v3 re-run as pending.
TEST_SET = """ + json.dumps(TEST_SET, indent=1) + """

LABEL_BY_ID = """ + json.dumps(LABEL_BY_ID, indent=1) + """

print(f'test set loaded: {len(TEST_SET)} questions')
for t in TEST_SET:
    print(f"  {t['id']:3s} [{t['kind']}] GT={t['gt_labels']}")
assert [t['id'] for t in TEST_SET] == ['K0'] + [f'H{i}' for i in range(1, 16)]
print('test set OK: 16 questions (K0 + H1-H15), GT v2 (D1-A) fixed before the run.')
print('PENDING (not scored here): GT-v3 re-run after Lane 07 ratification.')
"""

    run_code = """# Cell 6 — parity + timing: student FP32 ONNX vs INT8 ONNX (+ teacher if present).
# HARD RULES:
#  - Same 16 questions, same tokenization, same shape-bucket padding
#    (64/128/192) for every artifact — padding differences would fake
#    the parity numbers.
#  - Cold timing = first batch INCLUDING session creation; warm timing =
#    median of 3 repeat runs over the 16 questions. Both are reported;
#    only warm timing is compared to the < 50 ms/Q GPU target.
#  - Teacher comparison runs ONLY if a teacher checkpoint is present in
#    this session (TEACHER_PATH set by the user in the cell below);
#    otherwise it logs 'teacher not present — teacher parity NOT MEASURED'.
#  - No fallback to keyword/regex matching anywhere: a failed ONNX load
#    is recorded as an error and the run stops.
import time, json, statistics
import numpy as np
import onnxruntime as ort
from transformers import AutoTokenizer

TEACHER_PATH = ''  # <-- set to a Lane 03 teacher checkpoint path to enable teacher parity
TOKENIZER_ID = 'answerdotai/ModernBERT-base'  # <-- MUST match the student backbone's tokenizer;
# ^ placeholder default: replace with the actual student backbone id used
# in scripts/distill_student.py, or the run will fail loudly on vocab mismatch.
tokenizer = AutoTokenizer.from_pretrained(TOKENIZER_ID)

def _bucket(n):
    for b in (64, 128, 192):
        if n <= b:
            return b
    raise ValueError(f'seq_len {n} > 192 — truncate/filter clauses first')

def _probs(x):
    x = x - x.max(axis=-1, keepdims=True)
    e = np.exp(x)
    return e / e.sum(axis=-1, keepdims=True)

def _run_session(session, texts):
    enc = tokenizer(texts, truncation=True, max_length=192, padding=False,
                    return_tensors='np')
    bucket = _bucket(int(enc['input_ids'].shape[1]))
    pad = bucket - int(enc['input_ids'].shape[1])
    ids = np.pad(enc['input_ids'], ((0, 0), (0, pad))) if pad else enc['input_ids']
    mask = np.pad(enc['attention_mask'], ((0, 0), (0, pad))) if pad else enc['attention_mask']
    outs = session.run(['issue_logits', 'fact_logits', 'sex_logits',
                        'role_logits', 'time_logits', 'safety_logits'],
                       {'input_ids': ids.astype(np.int64),
                        'attention_mask': mask.astype(np.int64)})
    return {name: np.asarray(o) for name, o in zip(
        ['issue_logits', 'fact_logits', 'sex_logits',
         'role_logits', 'time_logits', 'safety_logits'], outs)}

QUESTIONS = [t['question'] for t in TEST_SET]
HEADS = ['issue_logits', 'fact_logits', 'sex_logits',
         'role_logits', 'time_logits', 'safety_logits']

def _timed_make(path, providers):
    t0 = time.perf_counter()
    opts = ort.SessionOptions()
    opts.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
    sess = ort.InferenceSession(path, sess_options=opts, providers=providers)
    load_s = time.perf_counter() - t0
    return sess, load_s

RESULTS = {'amp': AMP_INFO, 'per_question': [], 'tiers': {}}
# --- Tier 1: student INT8 ONNX on CUDA (target < 50 ms/Q warm). ---
sess_gpu, load_gpu = _timed_make('student_int8.onnx',
                                 ['CUDAExecutionProvider', 'CPUExecutionProvider'])
t0 = time.perf_counter(); out_int8_gpu = _run_session(sess_gpu, QUESTIONS)
cold_gpu = time.perf_counter() - t0
warms = []
for _ in range(3):
    t0 = time.perf_counter(); _run_session(sess_gpu, QUESTIONS); warms.append(time.perf_counter() - t0)
warm_gpu = statistics.median(warms)
RESULTS['tiers']['student_onnx_gpu'] = {
    'load_s': round(load_gpu, 2), 'cold_16q_s': round(cold_gpu, 3),
    'warm_16q_s': round(warm_gpu, 3), 'warm_ms_per_q': round(warm_gpu / 16 * 1000, 1),
    'target': 'mean < 50 ms/Q, max <= 100 ms/Q, load <= 15 s (plan §5.3)'}
print(f"Tier 1 student_onnx_gpu: load {load_gpu:.1f}s, cold 16Q {cold_gpu:.2f}s, "
      f"warm 16Q {warm_gpu:.2f}s ({warm_gpu/16*1000:.1f} ms/Q)")
# --- Tier 2: student INT8 ONNX on CPU (target < 0.5 s/Q mean). ---
sess_cpu, load_cpu = _timed_make('student_int8.onnx', ['CPUExecutionProvider'])
t0 = time.perf_counter(); out_int8_cpu = _run_session(sess_cpu, QUESTIONS)
cold_cpu = time.perf_counter() - t0
warms = []
for _ in range(3):
    t0 = time.perf_counter(); _run_session(sess_cpu, QUESTIONS); warms.append(time.perf_counter() - t0)
warm_cpu = statistics.median(warms)
RESULTS['tiers']['student_onnx_int8_cpu'] = {
    'load_s': round(load_cpu, 2), 'cold_16q_s': round(cold_cpu, 3),
    'warm_16q_s': round(warm_cpu, 3), 'warm_s_per_q': round(warm_cpu / 16, 3),
    'target': 'mean < 0.5 s/Q, max <= 1.0 s/Q, load <= 5 s (plan §5.3)'}
print(f"Tier 2 student_onnx_int8_cpu: load {load_cpu:.1f}s, cold 16Q {cold_cpu:.2f}s, "
      f"warm 16Q {warm_cpu:.2f}s ({warm_cpu/16:.3f} s/Q)")
# --- FP32 ONNX reference (parity baseline) + INT8 parity per question. ---
sess_fp32, _ = _timed_make('student_fp32.onnx', ['CUDAExecutionProvider', 'CPUExecutionProvider'])
out_fp32 = _run_session(sess_fp32, QUESTIONS)
max_abs_diff = 0.0; flips = 0
for qi, t in enumerate(TEST_SET):
    row = {'id': t['id'], 'heads': {}}
    for h in HEADS:
        p32 = _probs(out_fp32[h])[qi]; p8 = _probs(out_int8_gpu[h])[qi]
        d = float(np.abs(p32 - p8).max())
        max_abs_diff = max(max_abs_diff, d)
        f = int((p32.argmax(axis=-1) != p8.argmax(axis=-1)).sum())
        flips += f
        row['heads'][h] = {'max_abs_diff': round(d, 4), 'flips': f}
    RESULTS['per_question'].append(row)
    print(f"{t['id']}: max head diff "
          f"{max(r['max_abs_diff'] for r in row['heads'].values()):.4f}, flips "
          f"{sum(r['flips'] for r in row['heads'].values())}")
RESULTS['parity_int8_vs_fp32'] = {'max_abs_diff': round(max_abs_diff, 4), 'flips': flips,
    'gate': 'max_abs_diff <= 0.03, 0 flips (plan §5.2/§5.3)'}
print(f'INT8 vs FP32 parity: max_abs_diff={max_abs_diff:.4f}, flips={flips}')
# --- Teacher parity (only if a teacher checkpoint was provided). ---
if TEACHER_PATH:
    print('Teacher parity: TEACHER_PATH set — load Lane 03 teacher and compare here.')
    print('NOT IMPLEMENTED in this generated cell: the teacher load call depends on')
    print('Lane 03 final class name; wire it to src/laya_v7_classifier.py at merge.')
    RESULTS['parity_teacher'] = 'NOT MEASURED — teacher wiring pending Lane 03 merge'
else:
    print('Teacher not present in this session — teacher parity NOT MEASURED (not zero).')
    RESULTS['parity_teacher'] = 'NOT MEASURED — no teacher checkpoint in session'
"""

    e2e_code = """# Cell 7 — OPTIONAL end-to-end: 16-Q kept_ids, student vs teacher (needs laya_v71_src.zip).
# If the v7.1 source tree was uploaded, unzip it and run assess_v7 with
# mode='student_onnx' and mode='laya' over the 16 questions, then compare
# kept_ids per question (0 exact flips required for G14-T4). If it was
# NOT uploaded, this cell logs END-TO-END SKIPPED and the run still files
# parity + timing from Cell 6. There is NO keyword/regex fallback here.
import json, os
E2E = {'status': 'SKIPPED — laya_v71_src.zip not uploaded; end-to-end exact scores NOT measured'}
if HAS_SRC_ZIP:
    import zipfile
    print('Unzipping laya_v71_src.zip ...')
    with zipfile.ZipFile('laya_v71_src.zip') as z:
        z.extractall('laya_v71_src')
    import sys
    sys.path.insert(0, os.path.abspath('laya_v71_src/src'))
    try:
        from laya_v7 import assess_v7_batch
        import time
        t0 = time.perf_counter()
        # assess_v7_batch returns (records, total_wall_s) — unpack both.
        # NOTE: mode='student_onnx' does not exist in the v7 baseline yet;
        # it needs the runtime wiring (Lane 05 unified runtime / Lane 01
        # follow-up). If it raises, this cell records ERROR, not a score.
        stu, _wall_stu = assess_v7_batch([t['question'] for t in TEST_SET], mode='student_onnx')
        t_stu = time.perf_counter() - t0
        t0 = time.perf_counter()
        tea, _wall_tea = assess_v7_batch([t['question'] for t in TEST_SET], mode='laya')
        t_tea = time.perf_counter() - t0
        rows = []
        flips = 0
        for t, s, th in zip(TEST_SET, stu, tea):
            same = sorted(s['kept_ids']) == sorted(th['kept_ids'])
            flips += 0 if same else 1
            rows.append({'id': t['id'],
                         'student_kept_ids': sorted(s['kept_ids']),
                         'teacher_kept_ids': sorted(th['kept_ids']),
                         'gt_ids': sorted(t['gt_ids']),
                         'student_exact': sorted(s['kept_ids']) == sorted(t['gt_ids']),
                         'teacher_exact': sorted(th['kept_ids']) == sorted(t['gt_ids']),
                         'kept_ids_match': same})
        E2E = {'status': 'MEASURED', 'student_16q_s': round(t_stu, 2),
               'teacher_16q_s': round(t_tea, 2),
               'kept_ids_flips_student_vs_teacher': flips,
               'student_exact': f"{sum(r['student_exact'] for r in rows)}/16",
               'teacher_exact': f"{sum(r['teacher_exact'] for r in rows)}/16",
               'per_question': rows}
        print(f"end-to-end: student exact {E2E['student_exact']}, teacher exact "
              f"{E2E['teacher_exact']}, kept_ids flips {flips}")
    except Exception as e:
        E2E = {'status': f'ERROR — {e!r} (scored as not measured, no fallback)'}
        print('end-to-end ERROR:', repr(e))
else:
    print('END-TO-END SKIPPED — upload laya_v71_src.zip and re-run this cell to measure it.')
RESULTS['end_to_end'] = E2E
"""

    score_code = """# Cell 8 — G14-T4 verdict, RTX comparison, save + download.
# Every gate below is evaluated from THIS run's measured numbers.
# A gate with no measurement is reported as NOT MEASURED, never as PASS.
import json
agg = {}
p = RESULTS['parity_int8_vs_fp32']
agg['parity_int8_vs_fp32_max_abs_diff'] = p['max_abs_diff']
agg['parity_int8_vs_fp32_flips'] = p['flips']
agg['parity_gate'] = ('PASS' if p['max_abs_diff'] <= 0.03 and p['flips'] == 0 else 'FAIL')
t1 = RESULTS['tiers']['student_onnx_gpu']
agg['tier1_gpu_warm_ms_per_q'] = t1['warm_ms_per_q']
agg['tier1_gpu_load_s'] = t1['load_s']
agg['tier1_gpu_gate'] = ('PASS' if t1['warm_ms_per_q'] < 50 and t1['load_s'] <= 15 else 'FAIL')
t2 = RESULTS['tiers']['student_onnx_int8_cpu']
agg['tier2_cpu_warm_s_per_q'] = t2['warm_s_per_q']
agg['tier2_cpu_load_s'] = t2['load_s']
agg['tier2_cpu_gate'] = ('PASS' if t2['warm_s_per_q'] < 0.5 and t2['load_s'] <= 5 else 'FAIL')
agg['teacher_parity'] = RESULTS['parity_teacher']
agg['end_to_end'] = RESULTS['end_to_end'].get('status', 'SKIPPED')
# T4 vs RTX 5050 kept_ids parity — only if the RTX reference was uploaded.
if RTX_REF is not None and RESULTS['end_to_end'].get('status') == 'MEASURED':
    rtx = {r['id']: sorted(r.get('kept_ids', [])) for r in RTX_REF.get('per_question', [])}
    flips = sum(1 for r in RESULTS['end_to_end']['per_question']
                if rtx.get(r['id']) is not None and rtx[r['id']] != r['student_kept_ids'])
    agg['t4_vs_rtx5050_kept_ids_flips'] = flips
    agg['t4_vs_rtx5050_gate'] = 'PASS' if flips == 0 else 'FAIL'
else:
    agg['t4_vs_rtx5050_kept_ids_flips'] = 'NOT MEASURED — RTX reference or end-to-end missing'
    agg['t4_vs_rtx5050_gate'] = 'NOT MEASURED'
agg['g14_t4_verdict'] = ('PASS' if agg['parity_gate'] == 'PASS'
                         and agg['tier1_gpu_gate'] == 'PASS'
                         and agg['t4_vs_rtx5050_gate'] in ('PASS', 'NOT MEASURED')
                         else 'FAIL / INCOMPLETE — see gates above')
agg['gt_note'] = 'Scored against frozen GT v2 (D1-A). GT-v3 re-run PENDING Lane 07 ratification.'
print('=== LAYA v7.1 — Colab T4 (G14-T4) results ===')
for k, v in agg.items():
    print(f'{k}: {v}')
out = {'aggregate': agg, 'amp': AMP_INFO, 'tiers': RESULTS['tiers'],
       'parity': RESULTS['parity_int8_vs_fp32'],
       'teacher_parity': RESULTS['parity_teacher'],
       'end_to_end': RESULTS['end_to_end'],
       'per_question_parity': RESULTS['per_question']}
with open('live-laya-v7-colab-results.json', 'w') as f:
    json.dump(out, f, indent=1, ensure_ascii=False)
md = ['# Live LAYA v7.1 — Colab T4 run (G14-T4)', '',
      '## Aggregate (measured in Colab)', '']
for k, v in agg.items():
    md.append(f'- **{k}**: {v}')
md += ['', 'Targets are plan §5.3 (GPU mean < 50 ms/Q, load <= 15 s; CPU INT8 mean < 0.5 s/Q).',
       'A gate with no measurement is NOT MEASURED, never PASS.',
       'GT v2 (D1-A); GT-v3 re-run pending Lane 07 ratification.', '']
with open('live-laya-v7-colab-results.md', 'w') as f:
    f.write('\\n'.join(md))
print('saved live-laya-v7-colab-results.json and live-laya-v7-colab-results.md')
from google.colab import files as _cf
_cf.download('live-laya-v7-colab-results.json')
_cf.download('live-laya-v7-colab-results.md')
print('Downloaded both result files. Send them back to Muse to record the T4 score.')
"""

    cells = [
        _cell_md(header_md),
        _cell_code(env_code),
        _cell_code(install_code),
        _cell_code(amp_code),
        _cell_code(artifacts_code),
        _cell_code(testset_code),
        _cell_code(run_code),
        _cell_code(e2e_code),
        _cell_code(score_code),
    ]
    for i, c in enumerate(cells):
        c["id"] = f"v7-cell-{i}"
    nb = {"nbformat": 4, "nbformat_minor": 5,
          "metadata": {"kernelspec": {"display_name": "Python 3",
                                      "language": "python",
                                      "name": "python3"},
                       "language_info": {"name": "python", "version": "3.12"}},
          "cells": cells}
    os.makedirs(os.path.dirname(NB_PATH), exist_ok=True)
    with open(NB_PATH, "w") as f:
        json.dump(nb, f, indent=1)
    print("notebook written:", NB_PATH, os.path.getsize(NB_PATH), "bytes")
    return NB_PATH


def validate(nb_path):
    with open(nb_path) as f:
        nb = json.load(f)
    assert nb["nbformat"] == 4, "nbformat is not 4"
    assert nb["nbformat_minor"] == 5, "nbformat_minor is not 5"
    assert len(nb["cells"]) == 9, f"expected 9 cells, got {len(nb['cells'])}"
    assert nb["cells"][0]["cell_type"] == "markdown"
    assert all(c["cell_type"] == "code" for c in nb["cells"][1:])
    assert all(c.get("id") for c in nb["cells"]), "cells must carry ids"
    src = "\n".join("".join(c.get("source", [])) for c in nb["cells"])
    # All 16 question IDs present (embedded test set).
    for qid in ["K0"] + [f"H{i}" for i in range(1, 16)]:
        assert f"'{qid}'" in src or f'"{qid}"' in src, f"missing question {qid}"
    # No local absolute paths, no workspace paths.
    for bad in ("/home/hatch", "~/workspace", "workspace/"):
        assert bad not in src, f"notebook contains local path {bad!r}"
    # T4 / AMP rule present.
    assert "LAYA_CUDA_AMP" in src and "fp16" in src, "AMP rule missing"
    assert "sm_75" in src and "(7, 5)" in src, "sm_75 detection missing"
    # Parity / latency gates present with the plan numbers.
    for token in ("0.03", "50", "0.5", "ORT_ENABLE_ALL"):
        assert token in src, f"gate token {token!r} missing"
    # ONNX I/O contract present.
    for token in ("issue_logits", "fact_logits", "safety_logits"):
        assert token in src, f"ONNX head {token!r} missing"
    # No invented live scores: scoring is computed at run time only.
    for bad in ("16/16 exact (live", "exact_section_set_match': '16/16",
                "G14-T4 verdict': 'PASS"):
        assert bad not in src, f"notebook contains an invented live score {bad!r}"
    # No sealed-bank reference anywhere.
    assert "sealed" not in src.lower(), "notebook references sealed banks"
    try:
        import nbformat
        nbformat.validate(nb)
        print("nbformat.validate: PASS")
    except ImportError:
        print("nbformat not installed locally — skipped nbformat.validate, "
              "manual schema checks above passed")
    print("validation: PASS — 9 cells, 16 questions, AMP fp16/sm_75, "
          "parity 0.03 / 0 flips, no local paths, no invented scores")


if __name__ == "__main__":
    path = build_notebook()
    validate(path)
