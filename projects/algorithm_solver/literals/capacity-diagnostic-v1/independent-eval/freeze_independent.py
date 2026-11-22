#!/usr/bin/env python3
"""Freeze exact pinned bytes for the 9 independently selected JS/Python/C corpora.

Reads ONLY from pinned Git blobs at clocksmith/gamma@59ff0441 and clocksmith/fawn@a281360f.
Does NOT run diagnostic.py or compute any bounds.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import subprocess

GAMMA_PIN = "59ff04415ff2afd04ff2ed451340f4f02852bf18"
FAWN_PIN = "a281360ff04321f08e5627c5309503d0259a0e70"

SPECS = [
    {
        "id": "JS-1",
        "name": "2038_compact_rule_tests",
        "language": "js",
        "repo": "gamma",
        "pin": GAMMA_PIN,
        "origin": "Mandate 2038 board-game rule tests",
        "paths": [
            "apps/games/2038/tests/construction-study.test.mjs",
            "apps/games/2038/tests/research-cost.test.mjs",
            "apps/games/2038/tests/sole-rules.test.mjs",
            "apps/games/2038/tests/spatial-counterplay.test.mjs",
        ],
    },
    {
        "id": "JS-2",
        "name": "gamma_web_game_utils",
        "language": "js",
        "repo": "gamma",
        "pin": GAMMA_PIN,
        "origin": "Gamma web frontend utils + game session",
        "paths": [
            "apps/web/utils/event-bus.js",
            "apps/web/utils/math.js",
            "apps/web/utils/storage.js",
            "apps/web/game/game-controller.js",
            "apps/web/game/game-session.js",
            "apps/web/game/tutorial.js",
        ],
    },
    {
        "id": "JS-3",
        "name": "reconfig_contrastive_rank_one",
        "language": "js",
        "repo": "gamma",
        "pin": GAMMA_PIN,
        "origin": "Reconfiguration rank-one operator experiment",
        "paths": [
            "projects/reconfiguration/contrastive_rank_one_v1/discrimination.mjs",
            "projects/reconfiguration/contrastive_rank_one_v1/operator.mjs",
            "projects/reconfiguration/contrastive_rank_one_v1/position_balanced_tasks.mjs",
            "projects/reconfiguration/contrastive_rank_one_v1/run.mjs",
            "projects/reconfiguration/contrastive_rank_one_v1/tasks.mjs",
            "projects/reconfiguration/contrastive_rank_one_v1/test_discrimination.mjs",
            "projects/reconfiguration/contrastive_rank_one_v1/test_operator.mjs",
        ],
    },
    {
        "id": "PY-1",
        "name": "swe_search_write_tools",
        "language": "python",
        "repo": "gamma",
        "pin": GAMMA_PIN,
        "origin": "Gamma SWE agent search/write scripts",
        "paths": [
            "gamma/swe/tools/scripts/find_refs.py",
            "gamma/swe/tools/scripts/grep.py",
            "gamma/swe/tools/scripts/rg_context.py",
            "gamma/swe/tools/scripts/write_file.py",
        ],
    },
    {
        "id": "PY-2",
        "name": "functiongemma_training_pkg",
        "language": "python",
        "repo": "gamma",
        "pin": GAMMA_PIN,
        "origin": "FunctionGemma training package",
        "paths": [
            "gamma/functiongemma_training/__init__.py",
            "gamma/functiongemma_training/formats.py",
            "gamma/functiongemma_training/reploid.py",
            "gamma/functiongemma_training/router.py",
            "gamma/functiongemma_training/train.py",
        ],
    },
    {
        "id": "PY-3",
        "name": "mind_meld_strategies_pkg",
        "language": "python",
        "repo": "gamma",
        "pin": GAMMA_PIN,
        "origin": "Mind-Meld decoding strategies package",
        "paths": [
            "gamma/mind_meld/strategies/__init__.py",
            "gamma/mind_meld/strategies/base_strategy.py",
            "gamma/mind_meld/strategies/perplexity_strategy.py",
            "gamma/mind_meld/strategies/semantic_strategy.py",
        ],
    },
    {
        "id": "C-1",
        "name": "fawn_metal_frontend_headers",
        "language": "c",
        "repo": "fawn",
        "pin": FAWN_PIN,
        "origin": "Doe native Metal frontend headers",
        "paths": [
            "runtime/c/native/src/metal_draw_guard.h",
            "runtime/c/native/src/metal_indirect.h",
            "runtime/c/native/src/metal_pass_timestamps.h",
            "runtime/c/native/src/metal_render_bindings.h",
        ],
    },
    {
        "id": "C-2",
        "name": "fawn_metal_objc_abi_types",
        "language": "c",
        "repo": "fawn",
        "pin": FAWN_PIN,
        "origin": "Doe Metal backend ObjC ABI type headers",
        "paths": [
            "runtime/c/backends/metal/src/objc_archive_types.h",
            "runtime/c/backends/metal/src/objc_external_types.h",
            "runtime/c/backends/metal/src/objc_query_types.h",
            "runtime/c/backends/metal/src/objc_render_types.h",
        ],
    },
    {
        "id": "C-3",
        "name": "enwiki9_nncp_runtime_hooks_c",
        "language": "c",
        "repo": "gamma",
        "pin": GAMMA_PIN,
        "origin": "Enwiki9 NNCP runtime C instrumentation hooks",
        "paths": [
            "projects/enwiki9/tools/nncp_libnc_gradient_hook.c",
            "projects/enwiki9/tools/nncp_libnc_internal_tensor_hook.c",
            "projects/enwiki9/tools/nncp_libnc_matmul_trace.c",
            "projects/enwiki9/tools/nncp_libnc_save_hook.c",
            "projects/enwiki9/tools/nncp_libnc_update_hook.c",
        ],
    },
]


def git_cat(repo: Path, rev_path: str) -> bytes:
    return subprocess.check_output(
        ["git", "--no-replace-objects", "-C", str(repo), "cat-file", "blob", rev_path]
    )


def main() -> None:
    here = Path(__file__).resolve().parent
    gamma_repo = here.parents[4]
    fawn_env = os.environ.get("FAWN_REPO")
    if fawn_env:
        fawn_repo = Path(fawn_env)
    elif (gamma_repo.parent / "fawn" / ".git").exists():
        fawn_repo = gamma_repo.parent / "fawn"
    else:
        fawn_repo = gamma_repo.parents[1] / "fawn"
    repo_map = {"gamma": gamma_repo, "fawn": fawn_repo}

    corpora = {}
    for spec in SPECS:
        repo = repo_map[spec["repo"]]
        files = []
        programs = []
        for path in spec["paths"]:
            raw = git_cat(repo, f"{spec['pin']}:{path}")
            files.append({"path": path, "bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()})
            programs.append(raw.decode("utf-8"))
        corpora[spec["id"]] = {
            "name": spec["name"],
            "language": spec["language"],
            "repo": spec["repo"],
            "pin": spec["pin"],
            "origin": spec["origin"],
            "fileCount": len(files),
            "totalBytes": sum(f["bytes"] for f in files),
            "files": files,
            "programs": programs,
        }

    out = {
        "schema": "capacity-diagnostic-independent-instances/v1",
        "pins": {"gamma": GAMMA_PIN, "fawn": FAWN_PIN},
        "corpora": corpora,
    }
    (here / "independent-instances.json").write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")
    print(f"Froze {len(corpora)} independent JS/Python/C corpora (zero diagnostics run).")


if __name__ == "__main__":
    main()
