"""Portable local runner for notebooks/live-laya-colab-test-v6-brutal.ipynb.

Normalizes git autocrlf checkouts back to canonical LF bytes in memory when
verifying SHA-256 digests and feeding the notebook's google.colab.files.upload
stub, keeping all frozen repository artifacts completely unmodified.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import sys
import time
import types


REPO_ROOT = Path(__file__).resolve().parent.parent
NB_PATH = REPO_ROOT / "notebooks" / "live-laya-colab-test-v6-brutal.ipynb"

EXPECTED_SHA256 = {
    "notebook": (
        NB_PATH,
        "d6ee579534b5f2ac0b836f834954afe73fd5480d0da7a7a9fc5bec6e2461ff98",
    ),
    "graph_v3": (
        REPO_ROOT / "graph" / "laya-crpc-bns-section-decision-tree-v3.json",
        "67bf2b04ca946f7c7fa3062068e01ce051fbce8f4d740c281afe6fff841c34a5",
    ),
    "gt_v2": (
        REPO_ROOT / "ground-truth" / "ground-truth-v2-hma27-A.json",
        "87818b1b659583bf06a25280a6b53dabedf65f29cab99058f02b8ed31c9ac97e",
    ),
    "brutal_bank": (
        REPO_ROOT / "test-bank" / "brutal-bank-v1-frozen.json",
        "934a2b2265ac137c96939e1fbeca3682a037010e42f972bfd459c2fcac4ec717",
    ),
    "sealed_fresh_20": (
        REPO_ROOT / "test-bank" / "sealed" / "sealed-fresh-20.json",
        "1d8b5dc376e711c3ac6ead4424bb2d8ce52b07552b9a533ad86e0616dbcf8837",
    ),
    "sealed_kannada_8": (
        REPO_ROOT / "test-bank" / "sealed" / "sealed-kannada-8.json",
        "2f652af1123a22441cc4158ddf480ef0981aa923858bbcb9dc3622f5e5c25853",
    ),
}


def canonical_lf_bytes(path: Path) -> bytes:
    return path.read_bytes().replace(b"\r\n", b"\n")


def sha256_lf(path: Path) -> str:
    return hashlib.sha256(canonical_lf_bytes(path)).hexdigest()


def verify_frozen_inputs() -> None:
    for label, (path, expected) in EXPECTED_SHA256.items():
        actual = sha256_lf(path)
        if actual != expected:
            raise RuntimeError(f"SHA-256 mismatch for {label} ({path}): {actual} != {expected}")
    print("[verify] All 6 frozen artifact canonical LF SHA-256 digests verified.")


def install_colab_stub(out_dir: Path) -> None:
    upload_sources = {
        "laya-crpc-bns-section-decision-tree-v3.json": REPO_ROOT / "graph" / "laya-crpc-bns-section-decision-tree-v3.json",
        "brutal-bank-v1-frozen.json": REPO_ROOT / "test-bank" / "brutal-bank-v1-frozen.json",
        "sealed-fresh-20.json": REPO_ROOT / "test-bank" / "sealed" / "sealed-fresh-20.json",
        "sealed-kannada-8.json": REPO_ROOT / "test-bank" / "sealed" / "sealed-kannada-8.json",
    }
    google_mod = types.ModuleType("google")
    colab_mod = types.ModuleType("google.colab")
    files_mod = types.ModuleType("google.colab.files")

    files_mod.upload = lambda: {k: canonical_lf_bytes(p) for k, p in upload_sources.items()}
    files_mod.download = lambda fn: print(f"[local-runner] saved {(out_dir / fn).resolve()}")
    colab_mod.files = files_mod
    google_mod.colab = colab_mod

    sys.modules["google"] = google_mod
    sys.modules["google.colab"] = colab_mod
    sys.modules["google.colab.files"] = files_mod


def main() -> None:
    parser = argparse.ArgumentParser(description="Run LAYA v6 brutal notebook locally.")
    parser.add_argument("--out-dir", type=Path, default=REPO_ROOT / "results")
    parser.add_argument("--start-cell", type=int, default=3)
    parser.add_argument("--end-cell", type=int, default=23)
    parser.add_argument("--force-cpu", action="store_true")
    args = parser.parse_args()

    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if args.force_cpu:
        os.environ["CUDA_VISIBLE_DEVICES"] = ""

    verify_frozen_inputs()
    args.out_dir.mkdir(parents=True, exist_ok=True)
    os.chdir(args.out_dir)
    install_colab_stub(args.out_dir)

    nb = json.loads(NB_PATH.read_text(encoding="utf-8"))
    ns: dict[str, object] = {"__name__": "__main__"}
    t_all = time.perf_counter()
    for idx in range(args.start_cell, args.end_cell + 1):
        cell = nb["cells"][idx]
        if cell.get("cell_type") != "code":
            continue
        src = "".join(cell.get("source", []))
        exec(compile(src, f"{NB_PATH.name}#cell_{idx}", "exec"), ns, ns)
    print(f"[local-runner] Completed cells {args.start_cell}..{args.end_cell} in {time.perf_counter() - t_all:.2f}s")


if __name__ == "__main__":
    main()
