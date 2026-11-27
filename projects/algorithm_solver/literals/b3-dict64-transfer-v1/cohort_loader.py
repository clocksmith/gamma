"""Exact matched80 cohort loader + separate disjoint spent JS dev transfer loader.

Strict isolation guarantees:
- matched80 sources are loaded from scale-v2/generated/manifest.json, verified
  byte-for-byte against their SHA-256 digests and against Git pin
  59ff04415ff2afd04ff2ed451340f4f02852bf18, preserving exact trailing newlines.
- Baseline rank verification reproduces the exact witness-coverage-v1 minima
  (79 unrestricted, 92 witnessed) on raw matched80 compact and canonical sources.
- Dev transfer problems are loaded strictly from already-exposed authored
  continuation cohorts in catalogue/authored/, programmatically verified to be
  100% disjoint from matched80 and from every reserved/protected ID in
  contracts/js_corpus_reservations_v1.json and contracts/typed_confirmation_v1.json.
"""
from __future__ import annotations

import collections
import hashlib
import importlib.util
import json
import math
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
LIT_ROOT = HERE.parent
ALGSOLVE_ROOT = LIT_ROOT.parent
REPO_ROOT = ALGSOLVE_ROOT.parent.parent

MATCHED80_PIN = "59ff04415ff2afd04ff2ed451340f4f02852bf18"

DEV_TRANSFER_COHORTS = (
    "continuation-a-20261028-v1",
    "continuation-d-20261028-v1",
    "continuation-f-20261028-v1",
    "continuation-h-20261028-v1",
    "continuation-j-20261028-v1",
    "continuation-l-20261028-v1",
    "continuation-n-20261028-v1",
    "continuation-o-20261028-v1",
)


def sha256_bytes(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _load_py_module(name: str, path: Path, extra_sys_path: Path | None = None):
    old_path = list(sys.path)
    if extra_sys_path is not None:
        sys.path.insert(0, str(extra_sys_path))
    try:
        for stale in ("oracles", "test_oracles"):
            if extra_sys_path is not None:
                sys.modules.pop(stale, None)
        spec = importlib.util.spec_from_file_location(name, path)
        mod = importlib.util.module_from_spec(spec)
        sys.modules[name] = mod
        spec.loader.exec_module(mod)
        return mod
    finally:
        sys.path[:] = old_path


def _git_blob(rel_path: str, pin: str = MATCHED80_PIN) -> bytes:
    return subprocess.check_output(
        ["git", "-C", str(REPO_ROOT), "show", f"{pin}:{rel_path}"],
        stderr=subprocess.PIPE,
    )


def _field_rank(words: list[bytes], chars: dict[int, int], prime: int = 1_000_000_007, base: int = 2) -> int:
    """Prime-field polynomial vector rank (matches witness-coverage-v1/check_rank.py)."""
    rows: list[list[int]] = []
    for w in set(words):
        v = [0] * len(chars)
        weight = 1
        for c in w:
            v[chars[c]] = (v[chars[c]] + weight) % prime
            weight = (weight * base) % prime
        rows.append(v)
    r = 0
    for col in range(len(chars)):
        pivot = next((i for i in range(r, len(rows)) if rows[i][col]), None)
        if pivot is None:
            continue
        rows[r], rows[pivot] = rows[pivot], rows[r]
        inv = pow(rows[r][col], prime - 2, prime)
        rows[r] = [(x * inv) % prime for x in rows[r]]
        for i in range(len(rows)):
            if i != r and rows[i][col]:
                f = rows[i][col]
                rows[i] = [(x - f * y) % prime for x, y in zip(rows[i], rows[r])]
        r += 1
    return r


def verify_matched80_rank_baselines(sources_by_variant: dict[str, dict[int, bytes]]) -> dict[str, Any]:
    """Reproduce exact witness-coverage-v1 rank minima (79 unrestricted, 92 witnessed)."""
    out: dict[str, Any] = {}
    for variant in ("compact", "canonical"):
        sources = [sources_by_variant[variant][pid] for pid in sorted(sources_by_variant[variant])]
        assert len(sources) == 80 and len(set(sources)) == 80
        letters = sorted(set(b"".join(sources)))
        chars = {c: i for i, c in enumerate(letters)}
        unrestricted_rank = _field_rank(sources, chars)

        owners: dict[bytes, set[int]] = collections.defaultdict(set)
        for idx, s in enumerate(sources):
            for i in range(len(s) - 1):
                owners[s[i : i + 2]].add(idx)
        blocks: list[bytes] = []
        for s in sources:
            start = 0
            for i in range(len(s) - 1):
                if len(owners[s[i : i + 2]]) < 2:
                    blocks.append(s[start : i + 1])
                    start = i + 1
            blocks.append(s[start:])
        witnessed_rank = _field_rank(blocks, chars)
        assert unrestricted_rank == 79, f"{variant}: expected unrestricted rank 79, got {unrestricted_rank}"
        assert witnessed_rank == 92 and len(letters) == 92, (
            f"{variant}: expected witnessed rank 92 / alphabet 92, got {witnessed_rank} / {len(letters)}"
        )
        out[variant] = {
            "programs": 80,
            "total_bytes": sum(len(s) for s in sources),
            "distinct_chars": len(letters),
            "trailing_newlines": sum(s.endswith(b"\n") for s in sources),
            "unrestricted_rank_min": unrestricted_rank,
            "witnessed_rank_min": witnessed_rank,
            "forced_blocks_distinct": len(set(blocks)),
            "verified": True,
        }
    return out


def classify_problem_family(slug: str, title: str = "") -> str:
    """Deterministic coarse algorithmic problem family from public slug/title."""
    s = f"{slug} {title}".lower()
    if any(k in s for k in ("tree", "graph", "path", "grid", "island", "maze", "network", "trapezoid", "triangle", "point", "coordinate", "surface", "projection", "matrix", "toeplitz", "transpose", "smoother", "reshape", "flipping")):
        return "geometry_matrix_graph"
    if any(k in s for k in ("subsequence", "subarray", "substring", "palindrome", "window", "contiguous", "longest", "prefix", "anagram", "string", "word", "letter", "email", "vowel", "goat", "backspace", "lower", "defang", "ip", "binary-string", "parenthes", "character", "digits")):
        return "string_window_sequence"
    if any(k in s for k in ("xor", "bit", "prime", "gcd", "divisible", "sqrt", "reverse-integer", "power", "modulo", "number", "sum", "integer", "odd", "even", "parity", "climb", "stair", "fibonacci", "count", "ways", "combination", "permutation")):
        return "math_bitwise_combinatorics"
    if any(k in s for k in ("sort", "median", "search", "binary", "heap", "stone", "queue", "stack", "baseball", "merge", "interval", "schedule", "jump", "profit", "stock", "flower", "candy", "candies", "majority", "pivot", "height", "relative", "degree", "score", "k-negation")):
        return "array_greedy_search_ds"
    return "general_algorithmic"


def _collect_reserved_ids() -> set[int]:
    """Read ONLY numeric reservation IDs from public contract metadata."""
    reserved: set[int] = set()
    contracts_dir = ALGSOLVE_ROOT / "contracts"
    res_path = contracts_dir / "js_corpus_reservations_v1.json"
    if res_path.exists():
        data = json.loads(res_path.read_text())

        def walk(obj: Any) -> None:
            if isinstance(obj, dict):
                for k, v in obj.items():
                    if k in ("id", "problem_id", "frontend_id") and isinstance(v, int):
                        reserved.add(v)
                    elif k in ("ids", "reserved_ids", "protected_ids") and isinstance(v, list):
                        for item in v:
                            if isinstance(item, int):
                                reserved.add(item)
                    else:
                        walk(v)
            elif isinstance(obj, list):
                for item in obj:
                    walk(item)

        walk(data)

    tc_path = contracts_dir / "typed_confirmation_v1.json"
    if tc_path.exists():
        tc = json.loads(tc_path.read_text())
        for entry in tc.get("reservation", {}).get("pool", []):
            for member in entry.get("members", []):
                m = re.search(r"(\d+)$", str(member))
                if m:
                    reserved.add(int(m.group(1)))
    return reserved


def load_matched80(verify_git_pin: bool = True) -> dict[str, Any]:
    """Load the exact exposed matched80 JS cohort and all 8,412 frozen test cases."""
    ids = sorted(json.loads((LIT_ROOT / "matched80-v1/labels/ids.json").read_text()))
    assert len(ids) == 80
    id_set = set(ids)

    scale_dir = LIT_ROOT / "scale-v2"
    manifest_bytes = (scale_dir / "generated/manifest.json").read_bytes()
    manifest = json.loads(manifest_bytes)
    scale_contract = json.loads((scale_dir / "contract.json").read_text())
    additional_ids = set(scale_contract["additional_ids"])

    # Verify qualification receipts exist and bind the exact manifest
    for rel_receipt in ("qualification/report.json", "qualification-rerun-v1/report.json"):
        receipt = json.loads((scale_dir / rel_receipt).read_text())
        assert receipt["generated_manifest_sha256"] == sha256_bytes(manifest_bytes)
        assert receipt["passed_sources"] == 240

    sources_by_variant: dict[str, dict[int, bytes]] = {
        "original": {},
        "canonical": {},
        "compact": {},
    }
    meta_by_id: dict[int, dict[str, Any]] = {}

    for row in manifest["rows"]:
        pid = row["id"]
        variant = row["variant"]
        if pid not in id_set or variant not in sources_by_variant:
            continue
        file_path = scale_dir / "generated" / row["file"]
        raw = file_path.read_bytes()
        assert sha256_bytes(raw) == row["sha256"], f"SHA mismatch for matched80 #{pid} {variant}"
        assert raw.endswith(b"\n"), f"Missing trailing newline for matched80 #{pid} {variant}"
        if verify_git_pin:
            pinned = _git_blob(f"projects/algorithm_solver/literals/scale-v2/generated/{row['file']}")
            assert raw == pinned, f"Git pin mismatch for matched80 #{pid} {variant}"
        sources_by_variant[variant][pid] = raw
        if variant == "original":
            meta_by_id[pid] = {
                "id": pid,
                "method": row["method"],
                "original_entry": row["entry"],
                "original_interface": row["interface"],
                "original_sha256": row["sha256"],
            }
        elif variant == "compact":
            meta_by_id.setdefault(pid, {})["compact_sha256"] = row["sha256"]
        elif variant == "canonical":
            meta_by_id.setdefault(pid, {})["canonical_sha256"] = row["sha256"]

    for variant in sources_by_variant:
        assert len(sources_by_variant[variant]) == 80

    # Load all frozen test cases (same three check modules used in scale-v2/verify.py)
    old_checks = _load_py_module("b3_old_checks", LIT_ROOT / "checks.py")
    cluster_checks = _load_py_module("b3_cluster_checks", LIT_ROOT / "clusters-v1/checks.py")
    new_checks = _load_py_module("b3_new_checks", scale_dir / "checks.py")

    cases_by_id: dict[int, list[dict[str, Any]]] = {}
    check_kind_by_id: dict[int, str] = {}
    for pid in ids:
        if pid in additional_ids:
            cases = new_checks.make_cases(pid)
            check_kind_by_id[pid] = "scale_v2_additional"
        elif pid in old_checks.METHODS:
            cases = old_checks.cases_by_problem[pid]
            check_kind_by_id[pid] = "pilot_20"
        else:
            cases = cluster_checks.make_cases(pid)
            check_kind_by_id[pid] = "clusters_40"
        cases_by_id[pid] = cases

    rank_verification = verify_matched80_rank_baselines(sources_by_variant)

    problems = []
    for pid in ids:
        m = meta_by_id[pid]
        problems.append({
            "id": pid,
            "key": f"m80:{pid:04d}",
            "cohort": "matched80",
            "family": classify_problem_family(m["method"]),
            "method": m["method"],
            "original_entry": m["original_entry"],
            "original_interface": m["original_interface"],
            "original_source": sources_by_variant["original"][pid].decode("utf-8"),
            "canonical_source": sources_by_variant["canonical"][pid].decode("utf-8"),
            "compact_source": sources_by_variant["compact"][pid].decode("utf-8"),
            "original_sha256": m["original_sha256"],
            "canonical_sha256": m["canonical_sha256"],
            "compact_sha256": m["compact_sha256"],
            "check_kind": check_kind_by_id[pid],
            "cases": cases_by_id[pid],
        })

    return {
        "schema": "b3.matched80.cohort.v1",
        "pin_commit": MATCHED80_PIN,
        "git_pin_verified": verify_git_pin,
        "problem_count": len(problems),
        "total_cases": sum(len(p["cases"]) for p in problems),
        "rank_verification": rank_verification,
        "problems": problems,
        "check_modules": {
            "old": old_checks,
            "cluster": cluster_checks,
            "new": new_checks,
            "additional_ids": additional_ids,
        },
    }


def _same_value(value: Any, expected: Any, abs_tol: float | None = None) -> bool:
    if isinstance(expected, bool):
        return type(value) is bool and value == expected
    if isinstance(expected, (int, float)):
        if type(value) not in (int, float) or isinstance(value, bool) or not math.isfinite(value):
            return False
        if abs_tol is not None:
            return abs(value - expected) <= abs_tol
        return value == expected
    if isinstance(expected, list):
        return isinstance(value, list) and len(value) == len(expected) and all(
            _same_value(x, y, abs_tol=abs_tol) for x, y in zip(value, expected)
        )
    if isinstance(expected, dict):
        return isinstance(value, dict) and value.keys() == expected.keys() and all(
            _same_value(value[k], expected[k], abs_tol=abs_tol) for k in expected
        )
    return type(value) is type(expected) and value == expected


def check_matched80_case(
    pid: int,
    case_index: int,
    case: dict[str, Any],
    rec: dict[str, Any],
    check_modules: dict[str, Any],
    original_obs: dict[str, Any] | None = None,
) -> tuple[bool, str]:
    """Exact host-side oracle + input-effect + original-parity verdict for matched80."""
    if "error" in rec:
        return False, f"runtime_error:{rec['error']}"
    if rec.get("args_before") != case["args"]:
        return False, "args_before_mismatch"
    preserved = rec.get("args_before") == rec.get("args_after")
    additional = check_modules["additional_ids"]
    old = check_modules["old"]
    cluster = check_modules["cluster"]

    if pid in additional:
        ok = _same_value(rec.get("result"), case["expected"]) and preserved
    elif pid in old.METHODS:
        ok = bool(old.check_observation(pid, case_index, rec)["passed"])
    else:
        out_ok = bool(cluster.output_ok(pid, case["args"], rec.get("result"), case["expected"]))
        if pid in (832, 922):
            eff_ok = rec.get("args_after") == [rec.get("result")]
        elif pid == 976:
            eff_ok = rec.get("args_after") == [sorted(case["args"][0])]
        else:
            eff_ok = preserved
        ok = out_ok and eff_ok

    if not ok:
        return False, "oracle_or_effect_mismatch"
    if original_obs is not None:
        cur_obs = {k: rec.get(k) for k in ("result", "args_after", "error")}
        if cur_obs != original_obs:
            return False, "original_parity_mismatch"
    return True, "ok"


def check_transfer_case(
    case: dict[str, Any],
    rec: dict[str, Any],
    original_obs: dict[str, Any] | None = None,
    abs_tol: float | None = None,
) -> tuple[bool, str]:
    """Exact host-side oracle + input preservation + original parity for dev transfer."""
    if "error" in rec:
        return False, f"runtime_error:{rec['error']}"
    if rec.get("args_before") != case["args"]:
        return False, "args_before_mismatch"
    if rec.get("args_before") != rec.get("args_after"):
        # If original itself mutated, require exact original parity; otherwise reject mutation
        if original_obs is None or rec.get("args_after") != original_obs.get("args_after"):
            return False, "input_mutation_mismatch"
    compare = case.get("compare", "return")
    if compare == "return":
        if not _same_value(rec.get("result"), case["expected"], abs_tol=abs_tol):
            return False, "result_mismatch"
    else:
        return False, f"unsupported_compare:{compare}"
    if original_obs is not None:
        cur_obs = {k: rec.get(k) for k in ("result", "args_after", "error")}
        if abs_tol is not None:
            if cur_obs.get("error") != original_obs.get("error") or cur_obs.get("args_after") != original_obs.get("args_after") or not _same_value(cur_obs.get("result"), original_obs.get("result"), abs_tol=abs_tol):
                return False, "original_parity_mismatch"
        elif cur_obs != original_obs:
            return False, "original_parity_mismatch"
    return True, "ok"


def load_dev_transfer_cohort(max_cases_per_problem: int | None = None) -> dict[str, Any]:
    """Load separate disjoint spent JS dev transfer problems from catalogue/authored/."""
    matched80_ids = set(json.loads((LIT_ROOT / "matched80-v1/labels/ids.json").read_text()))
    reserved_ids = _collect_reserved_ids()
    authored_root = ALGSOLVE_ROOT / "catalogue/authored"

    problems = []
    seen_ids: set[int] = set()
    families: dict[str, int] = collections.Counter()

    for cohort_name in DEV_TRANSFER_COHORTS:
        cohort_dir = authored_root / cohort_name
        assert cohort_dir.is_dir(), f"Missing transfer cohort directory: {cohort_dir}"
        asgn = json.loads((cohort_dir / "assignment.public-safe.json").read_text())
        by_pid = {p["id"]: p for p in asgn.get("problems", [])}

        cases_mod = _load_py_module(f"b3_transfer_cases_{cohort_name.replace('-', '_')}", cohort_dir / "cases.py", cohort_dir)

        for js_path in sorted((cohort_dir / "javascript").glob("*.js")):
            if not js_path.stem.isdigit():
                continue
            pid = int(js_path.stem)
            assert pid not in matched80_ids, f"Transfer problem {pid} overlaps matched80!"
            assert pid not in reserved_ids, f"Transfer problem {pid} overlaps reserved/protected IDs!"
            assert pid not in seen_ids, f"Duplicate transfer problem {pid}"
            seen_ids.add(pid)

            raw_bytes = js_path.read_bytes()
            raw_text = raw_bytes.decode("utf-8")
            pmeta = by_pid.get(pid, {})
            slug = pmeta.get("slug", f"problem-{pid}")
            title = pmeta.get("title", "")
            comp_meta = pmeta.get("comparison", {})
            abs_tol = comp_meta.get("absolute_tolerance") if isinstance(comp_meta, dict) else None
            family = classify_problem_family(slug, title)
            families[family] += 1

            try:
                cases = cases_mod.build_cases(pid, include_analytic_boundaries=False)
            except TypeError:
                cases = cases_mod.build_cases(pid, include_maximum=False)

            if max_cases_per_problem is not None and len(cases) > max_cases_per_problem:
                # Deterministic evenly-spaced subsample keeping first & last boundary cases
                n = len(cases)
                idxs = sorted({0, n - 1} | {int(round(k * (n - 1) / (max_cases_per_problem - 1))) for k in range(max_cases_per_problem)})
                cases = [cases[i] for i in idxs[:max_cases_per_problem]]

            problems.append({
                "id": pid,
                "key": f"dev:{cohort_name.split('-')[1]}:{pid}",
                "cohort": cohort_name,
                "slug": slug,
                "title": title,
                "family": family,
                "abs_tol": abs_tol,
                "source_path": str(js_path.relative_to(REPO_ROOT)),
                "raw_source": raw_text,
                "raw_sha256": sha256_bytes(raw_bytes),
                "raw_bytes": len(raw_bytes),
                "cases": cases,
            })

    return {
        "schema": "b3.dev_transfer.cohort.v1",
        "cohorts": list(DEV_TRANSFER_COHORTS),
        "problem_count": len(problems),
        "total_cases": sum(len(p["cases"]) for p in problems),
        "disjoint_from_matched80": True,
        "disjoint_from_reserved": True,
        "reserved_ids_checked": len(reserved_ids),
        "family_counts": dict(sorted(families.items())),
        "problems": problems,
    }


if __name__ == "__main__":
    m80 = load_matched80(verify_git_pin=True)
    dt = load_dev_transfer_cohort(max_cases_per_problem=64)
    print(json.dumps({
        "matched80_count": m80["problem_count"],
        "matched80_cases": m80["total_cases"],
        "matched80_ranks": m80["rank_verification"],
        "dev_transfer_count": dt["problem_count"],
        "dev_transfer_cases": dt["total_cases"],
        "dev_transfer_families": dt["family_counts"],
    }, indent=2))
