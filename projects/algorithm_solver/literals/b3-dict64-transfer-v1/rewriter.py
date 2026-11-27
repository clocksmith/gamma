"""Frozen canonical JavaScript rewriter driver for B3 (Python interface to rewriter.mjs)."""
from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
REWRITER_MJS = HERE / "rewriter.mjs"
JS_AST_MJS = HERE / "js_ast.mjs"

# Single frozen canonical rewrite configuration (used by Arm 2 and Transfer).
FIXED_CANONICAL_OPTS: dict[str, Any] = {
    "eliminateGt": True,
    "eliminateXor": True,
    "incStyle": "plus_eq",
    "minimalBraces": True,
    "canonicalKeywords": True,
    "inlineMath": True,
    "pushToAssign": True,
    "lowerLocalClasses": True,
    "stringToConcat": True,
    "lowerDirectBuiltins": False,
    "namingOrder": "decl",
    "varAlphabet": ["a", "b", "c", "d", "e"],
}

# Finite, deterministic set of legal semantics-preserving canonical rewrite choices for Arm 3 joint search.
JOINT_VARIANT_SPECS: list[tuple[str, dict[str, Any]]] = [
    ("decl_pluseq_push2a_min", {**FIXED_CANONICAL_OPTS, "namingOrder": "decl", "incStyle": "plus_eq", "pushToAssign": True, "minimalBraces": True}),
    ("freq_pluseq_push2a_min", {**FIXED_CANONICAL_OPTS, "namingOrder": "freq", "incStyle": "plus_eq", "pushToAssign": True, "minimalBraces": True}),
    ("pfirst_pluseq_push2a_min", {**FIXED_CANONICAL_OPTS, "namingOrder": "param_first_freq", "incStyle": "plus_eq", "pushToAssign": True, "minimalBraces": True}),
    ("decl_pp_push2a_min", {**FIXED_CANONICAL_OPTS, "namingOrder": "decl", "incStyle": "plusplus", "pushToAssign": True, "minimalBraces": True}),
    ("freq_pp_push2a_min", {**FIXED_CANONICAL_OPTS, "namingOrder": "freq", "incStyle": "plusplus", "pushToAssign": True, "minimalBraces": True}),
    ("pfirst_pp_push2a_min", {**FIXED_CANONICAL_OPTS, "namingOrder": "param_first_freq", "incStyle": "plusplus", "pushToAssign": True, "minimalBraces": True}),
    ("decl_pluseq_push_min", {**FIXED_CANONICAL_OPTS, "namingOrder": "decl", "incStyle": "plus_eq", "pushToAssign": False, "minimalBraces": True}),
    ("pfirst_pp_push_min", {**FIXED_CANONICAL_OPTS, "namingOrder": "param_first_freq", "incStyle": "plusplus", "pushToAssign": False, "minimalBraces": True}),
    ("decl_pluseq_noinmath", {**FIXED_CANONICAL_OPTS, "namingOrder": "decl", "incStyle": "plus_eq", "inlineMath": False, "minimalBraces": True}),
    ("pfirst_pp_noinmath", {**FIXED_CANONICAL_OPTS, "namingOrder": "param_first_freq", "incStyle": "plusplus", "inlineMath": False, "minimalBraces": True}),
]


def rewriter_fingerprint() -> dict[str, str]:
    return {
        "rewriter_mjs_sha256": hashlib.sha256(REWRITER_MJS.read_bytes()).hexdigest(),
        "js_ast_mjs_sha256": hashlib.sha256(JS_AST_MJS.read_bytes()).hexdigest(),
        "rewriter_py_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    }


def rewrite_batch(jobs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    proc = subprocess.run(
        ["node", str(REWRITER_MJS)],
        input=json.dumps({"mode": "batch", "jobs": jobs}),
        capture_output=True,
        text=True,
        check=True,
    )
    return json.loads(proc.stdout)["results"]


def rewrite_fixed(sources_by_id: dict[int, str], opts: dict[str, Any] | None = None) -> dict[int, dict[str, Any]]:
    use_opts = FIXED_CANONICAL_OPTS if opts is None else opts
    jobs = [{"id": pid, "variant": "fixed", "code": code, "opts": use_opts} for pid, code in sorted(sources_by_id.items())]
    rows = rewrite_batch(jobs)
    return {r["id"]: r for r in rows}


def generate_joint_candidates(sources_by_id: dict[int, str]) -> dict[int, dict[str, dict[str, Any]]]:
    """Generate all unique legal canonical rewrite candidates per problem."""
    jobs = []
    for pid, code in sorted(sources_by_id.items()):
        for vname, vopts in JOINT_VARIANT_SPECS:
            jobs.append({"id": pid, "variant": vname, "code": code, "opts": vopts})
    rows = rewrite_batch(jobs)
    by_pid: dict[int, dict[str, dict[str, Any]]] = {}
    seen_code: dict[int, set[str]] = {}
    for r in rows:
        pid = r["id"]
        if not r.get("ok"):
            continue
        code = r["code"]
        s = seen_code.setdefault(pid, set())
        if code in s:
            continue
        s.add(code)
        by_pid.setdefault(pid, {})[r["variant"]] = r
    return by_pid
