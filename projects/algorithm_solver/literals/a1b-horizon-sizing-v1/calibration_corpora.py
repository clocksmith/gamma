#!/usr/bin/env python3
"""Independent calibration organization registry, 59-lineage exclusion verifier,
and verified B1RA grid builder for BITS Experiment Card A1b Stage-2 calibration.

Design contract:
- Selects 14 independent open-source organizations from local `.venv` site-packages
  strictly BEFORE looking at any compression scores.
- Verifies programmatic ZERO overlap against:
    (a) all 59 repository/corpus lineages across capacity-ladder-v1,
        capacity-deficit-race-v1, capacity-lagrangian-race-v1,
        capacity-boundary-v1, capacity-diagnostic-v1, and capacity-race-v1;
    (b) chain-fit org (ibm_codenet) and all 6 Stage-1 predictor-fit orgs;
    (c) A1b reserved sealed domains (SQL, JSON/Protobuf, Rust, TypeScript, YAML).
- Does NOT vendor third-party source code into git: writes only deterministic
  manifests (upstream org, repo, package, pinned version, file paths, sizes,
  SHA-256 hashes) and independently decoded archive receipts under `out/`.
"""

from __future__ import annotations

import hashlib
import importlib.metadata as importlib_metadata
import json
import os
import sys
import time
from multiprocessing import Pool
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
LITERALS = HERE.parent
WORKTREE = LITERALS.parent.parent.parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import archive_grid as AG  # noqa: E402
import sizing_policy as SP  # noqa: E402

VENV_SITE_PACKAGES = Path("/Users/xyz/deco/gamma/.venv/lib/python3.14/site-packages")

# Deterministic file-selection rules (frozen before scoring).
SELECTION_SEED = "a1b-cal-v1:"
EXCLUDED_PATH_PARTS = frozenset(
    {
        "test",
        "tests",
        "_tests",
        "testing",
        "benchmark",
        "benchmarks",
        "doc",
        "docs",
        "example",
        "examples",
        "conftest.py",
        "__pycache__",
    }
)
MIN_FILE_BYTES = 200
MAX_FILE_BYTES = 25_000
MAX_FILES_PER_ORG = 80
MAX_BYTES_PER_ORG = 200_000
MIN_FILES_BEFORE_BYTE_SKIP = 12

# 14 independent open-source organizations, fixed deterministically prior to scoring.
CALIBRATION_ORG_SPECS: tuple[dict[str, str], ...] = (
    {
        "lineage_id": "cal_aio_libs_aiohttp",
        "org_id": "aio-libs",
        "upstream_repo": "aio-libs/aiohttp",
        "package_name": "aiohttp",
        "domain": "async-http",
    },
    {
        "lineage_id": "cal_agronholm_anyio",
        "org_id": "agronholm",
        "upstream_repo": "agronholm/anyio",
        "package_name": "anyio",
        "domain": "async-concurrency",
    },
    {
        "lineage_id": "cal_python_attrs_attrs",
        "org_id": "python-attrs",
        "upstream_repo": "python-attrs/attrs",
        "package_name": "attrs",
        "domain": "declarative-classes",
    },
    {
        "lineage_id": "cal_fonttools_fonttools",
        "org_id": "fonttools",
        "upstream_repo": "fonttools/fonttools",
        "package_name": "fonttools",
        "domain": "typography",
    },
    {
        "lineage_id": "cal_fsspec_filesystem_spec",
        "org_id": "fsspec",
        "upstream_repo": "fsspec/filesystem_spec",
        "package_name": "fsspec",
        "domain": "virtual-filesystem",
    },
    {
        "lineage_id": "cal_encode_httpx",
        "org_id": "encode",
        "upstream_repo": "encode/httpx",
        "package_name": "httpx",
        "domain": "http-client",
    },
    {
        "lineage_id": "cal_joblib_joblib",
        "org_id": "joblib",
        "upstream_repo": "joblib/joblib",
        "package_name": "joblib",
        "domain": "parallel-pipelining",
    },
    {
        "lineage_id": "cal_matplotlib_matplotlib",
        "org_id": "matplotlib",
        "upstream_repo": "matplotlib/matplotlib",
        "package_name": "matplotlib",
        "domain": "scientific-plotting",
    },
    {
        "lineage_id": "cal_networkx_networkx",
        "org_id": "networkx",
        "upstream_repo": "networkx/networkx",
        "package_name": "networkx",
        "domain": "graph-algorithms",
    },
    {
        "lineage_id": "cal_numpy_numpy",
        "org_id": "numpy",
        "upstream_repo": "numpy/numpy",
        "package_name": "numpy",
        "domain": "numerical-arrays",
    },
    {
        "lineage_id": "cal_python_pillow_pillow",
        "org_id": "python-pillow",
        "upstream_repo": "python-pillow/Pillow",
        "package_name": "pillow",
        "domain": "image-processing",
    },
    {
        "lineage_id": "cal_textualize_rich",
        "org_id": "Textualize",
        "upstream_repo": "Textualize/rich",
        "package_name": "rich",
        "domain": "terminal-rendering",
    },
    {
        "lineage_id": "cal_scipy_scipy",
        "org_id": "scipy",
        "upstream_repo": "scipy/scipy",
        "package_name": "scipy",
        "domain": "scientific-computing",
    },
    {
        "lineage_id": "cal_sympy_sympy",
        "org_id": "sympy",
        "upstream_repo": "sympy/sympy",
        "package_name": "sympy",
        "domain": "symbolic-algebra",
    },
)

# Reserved A1b sealed domains (must never be touched or included in calibration).
RESERVED_SEALED_DOMAIN_TOKENS = frozenset(
    {
        "sql",
        "sqlite",
        "sqlalchemy",
        "postgres",
        "psycopg",
        "mysql",
        "json",
        "ujson",
        "orjson",
        "jsonschema",
        "pydantic",
        "protobuf",
        "protobufjs",
        "proto",
        "rust",
        "cargo",
        "polars",
        "typescript",
        "tsc",
        "yaml",
        "pyyaml",
        "ruamel",
        "yml",
    }
)

# Capacity lineage JSON files covering all 59 capacity/sealed corpora.
CAPACITY_AUDIT_FILES: tuple[str, ...] = (
    "capacity-ladder-v1/real-corpora.json",
    "capacity-deficit-race-v1/instances-a.json",
    "capacity-deficit-race-v1/instances-b.json",
    "capacity-lagrangian-race-v1/public-instances.json",
    "capacity-boundary-v1/instances.json",
    "capacity-diagnostic-v1/independent-eval/independent-instances.json",
    "capacity-race-v1/boundary-instances.json",
)

# Canonical org/repo aliases for upstream sources appearing across the 59 capacity corpora.
CAPACITY_ORG_ALIASES: dict[str, tuple[str, ...]] = {
    "cpython": ("python", "cpython", "psf"),
    "cpython 3.14.2": ("python", "cpython", "psf"),
    "three": ("mrdoob", "three", "three.js"),
    "rxjs": ("reactivex", "rxjs"),
    "lodash": ("lodash",),
    "babel-runtime": ("babel", "babel-runtime"),
    "ajv": ("ajv-validator", "ajv"),
    "eslint": ("eslint",),
    "zod": ("colinhacks", "zod"),
    "caniuse-lite": ("browserslist", "caniuse-lite"),
    "date-fns": ("date-fns",),
    "ggml": ("ggml-org", "ggml", "gguf"),
    "ffmpeg": ("ffmpeg",),
    "cairo": ("freedesktop", "cairo"),
    "brotli": ("google", "brotli"),
    "semver": ("npm", "semver", "node-semver"),
    "postcss": ("postcss",),
    "protobufjs": ("protobufjs", "protobuf"),
    "undici": ("nodejs", "undici"),
    "doppler": ("clocksmith", "doppler"),
    "fawn": ("clocksmith", "fawn"),
    "gamma": ("clocksmith", "gamma"),
    "reploid": ("clocksmith", "reploid"),
}


class CalibrationDisjointnessError(RuntimeError):
    """Raised when a calibration org overlaps excluded lineages, fit orgs, or sealed domains."""


def _norm_tokens(text: str) -> set[str]:
    clean = text.lower().replace("/", " ").replace("_", " ").replace("-", " ")
    toks = {t for t in clean.split() if t}
    toks.add(text.lower())
    return toks


def collect_excluded_registry() -> dict[str, Any]:
    """Read all 59 capacity lineages + fit/predictor-fit orgs + reserved domains from disk."""
    ladder_path = LITERALS / "capacity-ladder-v1/real-corpora.json"
    ladder = json.loads(ladder_path.read_text())
    ladder_corpus_ids = sorted(ladder["corpora"].keys())

    capacity_sources: set[str] = set()
    capacity_tokens: set[str] = set()
    file_digests: dict[str, str] = {}

    for rel in CAPACITY_AUDIT_FILES:
        p = LITERALS / rel
        if not p.exists():
            raise FileNotFoundError(f"required capacity audit file missing: {p}")
        raw = p.read_bytes()
        file_digests[rel] = AG.sha256_bytes(raw)
        d = json.loads(raw.decode("utf-8"))
        for src_key in d.get("sources", {}):
            s_low = str(src_key).lower()
            capacity_sources.add(s_low)
            capacity_tokens.add(s_low)
            capacity_tokens.update(CAPACITY_ORG_ALIASES.get(s_low, ()))
        corpora = d.get("corpora", {})
        if isinstance(corpora, dict):
            for entry in corpora.values():
                if not isinstance(entry, dict):
                    continue
                for fld in ("source", "upstreamProject", "repo", "project"):
                    val = entry.get(fld)
                    if val:
                        v_low = str(val).lower()
                        capacity_sources.add(v_low)
                        capacity_tokens.add(v_low)
                        capacity_tokens.update(CAPACITY_ORG_ALIASES.get(v_low, ()))

    # Chain-fit and Stage-1 predictor-fit organizations (and un-opened objective-holdout candidates).
    fit_corpus = AG.load_fit_corpus()
    dev_lineages = AG.load_spent_lineages()
    fit_and_dev_orgs = {fit_corpus["org_id"].lower()} | {
        l["org_id"].lower() for l in dev_lineages
    }
    fit_and_dev_tokens = set(fit_and_dev_orgs)
    for l in dev_lineages:
        fit_and_dev_tokens.add(l["lineage_id"].lower())
    fit_and_dev_tokens.update({"codenet", "express", "expressjs", "ramda", "thealgorithms", "lodash", "cpython", "python", "clocksmith", "gamma"})

    forbidden_file_hashes: set[str] = set(fit_corpus["file_hashes"])
    for l in dev_lineages:
        forbidden_file_hashes.update(l["file_hashes"])

    return {
        "capacity_ladder_corpus_count": len(ladder_corpus_ids),
        "capacity_ladder_corpus_ids": ladder_corpus_ids,
        "capacity_audit_files_sha256": file_digests,
        "capacity_sources": sorted(capacity_sources),
        "capacity_forbidden_tokens": sorted(capacity_tokens),
        "fit_and_predictor_fit_orgs": sorted(fit_and_dev_orgs),
        "fit_and_predictor_fit_tokens": sorted(fit_and_dev_tokens),
        "reserved_sealed_domain_tokens": sorted(RESERVED_SEALED_DOMAIN_TOKENS),
        "forbidden_file_hash_count": len(forbidden_file_hashes),
        "forbidden_file_hashes": forbidden_file_hashes,
    }


def assert_calibration_disjoint_from_excluded(
    cal_orgs: list[dict[str, Any]],
    excluded_registry: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Programmatically verify ZERO overlap with 59 capacity lineages, fit orgs, and reserved domains."""
    reg = excluded_registry if excluded_registry is not None else collect_excluded_registry()
    cap_toks = set(reg["capacity_forbidden_tokens"])
    fit_toks = set(reg["fit_and_predictor_fit_tokens"])
    res_toks = set(reg["reserved_sealed_domain_tokens"])
    forbidden_hashes: set[str] = set(reg["forbidden_file_hashes"])

    seen_orgs: set[str] = set()
    seen_repos: set[str] = set()
    seen_pkgs: set[str] = set()
    seen_hashes: dict[str, str] = {}

    for item in cal_orgs:
        lid = str(item["lineage_id"])
        org = str(item["org_id"])
        repo = str(item["upstream_repo"])
        pkg = str(item["package_name"])
        domain = str(item.get("domain", ""))

        org_l = org.lower()
        repo_l = repo.lower()
        pkg_l = pkg.lower()

        if org_l in seen_orgs:
            raise CalibrationDisjointnessError(f"duplicate calibration org_id: {org}")
        if repo_l in seen_repos:
            raise CalibrationDisjointnessError(f"duplicate calibration upstream_repo: {repo}")
        if pkg_l in seen_pkgs:
            raise CalibrationDisjointnessError(f"duplicate calibration package_name: {pkg}")
        seen_orgs.add(org_l)
        seen_repos.add(repo_l)
        seen_pkgs.add(pkg_l)

        # Check org, repo, package, and domain tokens against all three exclusion sets.
        # Note: strip generic language token "python" only when part of compound org like "python-attrs"/"python-pillow"
        # while STILL checking the exact org/repo/pkg names!
        id_fields = [org_l, repo_l, pkg_l, domain.lower()]
        repo_parts = [p.strip() for p in repo_l.split("/") if p.strip()]
        strict_ident = set(id_fields + repo_parts)
        domain_toks = _norm_tokens(domain) | _norm_tokens(pkg) | _norm_tokens(repo)

        hit_cap = strict_ident & cap_toks
        if hit_cap:
            raise CalibrationDisjointnessError(
                f"calibration org {org} ({repo}) overlaps 59-lineage capacity registry: {sorted(hit_cap)}"
            )
        hit_fit = strict_ident & fit_toks
        if hit_fit:
            raise CalibrationDisjointnessError(
                f"calibration org {org} ({repo}) overlaps chain/predictor-fit orgs: {sorted(hit_fit)}"
            )
        hit_res = (strict_ident | domain_toks) & res_toks
        if hit_res:
            raise CalibrationDisjointnessError(
                f"calibration org {org} ({repo}, domain={domain}) overlaps reserved sealed domain: {sorted(hit_res)}"
            )

        hashes = item.get("file_hashes") or [f["sha256"] for f in item.get("files", [])]
        for h in hashes:
            if h in forbidden_hashes:
                raise CalibrationDisjointnessError(
                    f"calibration org {org} shares exact file SHA-256 {h[:12]} with fit/dev corpora"
                )
            prev = seen_hashes.get(h)
            if prev is not None:
                raise CalibrationDisjointnessError(
                    f"calibration orgs {prev} and {lid} share exact file SHA-256 {h[:12]}"
                )
            seen_hashes[h] = lid

    return {
        "disjoint_ok": True,
        "calibration_org_count": len(cal_orgs),
        "capacity_ladder_corpus_count_checked": reg["capacity_ladder_corpus_count"],
        "capacity_sources_checked": reg["capacity_sources"],
        "fit_and_predictor_fit_orgs_checked": reg["fit_and_predictor_fit_orgs"],
        "reserved_sealed_domains_checked": ["SQL", "JSON/Protobuf", "Rust", "TypeScript", "YAML"],
        "unique_calibration_file_hashes_checked": len(seen_hashes),
        "overlap_count": 0,
    }


def select_calibration_corpora_from_venv(
    site_packages: Path = VENV_SITE_PACKAGES,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Deterministically select 14 independent calibration orgs from local .venv site-packages."""
    if not site_packages.exists():
        raise FileNotFoundError(f"local site-packages directory not found: {site_packages}")

    reg = collect_excluded_registry()
    forbidden_hashes: set[str] = set(reg["forbidden_file_hashes"])
    dists = {
        d.metadata["Name"].lower(): d
        for d in importlib_metadata.distributions(path=[str(site_packages)])
    }

    selected_lineages: list[dict[str, Any]] = []
    global_seen_hashes: set[str] = set(forbidden_hashes)

    for spec in CALIBRATION_ORG_SPECS:
        pkg_key = spec["package_name"].lower()
        if pkg_key not in dists:
            raise FileNotFoundError(f"calibration package not installed in .venv: {spec['package_name']}")
        dist = dists[pkg_key]
        version = dist.version
        lic_raw = dist.metadata.get("License-Expression") or dist.metadata.get("License") or "see upstream metadata"
        lic = lic_raw.splitlines()[0].strip()[:80]

        elig: list[tuple[str, str, bytes, str]] = []
        local_seen: set[str] = set()
        for f in dist.files or []:
            rel = str(f)
            if not rel.endswith(".py"):
                continue
            parts_low = {p.lower() for p in Path(rel).parts}
            if parts_low & EXCLUDED_PATH_PARTS:
                continue
            full_path = site_packages / rel
            if not full_path.is_file():
                continue
            raw = full_path.read_bytes()
            if not (MIN_FILE_BYTES <= len(raw) <= MAX_FILE_BYTES):
                continue
            if b"\x00" in raw:
                continue
            try:
                raw.decode("utf-8")
            except UnicodeDecodeError:
                continue
            h = AG.sha256_bytes(raw)
            if h in local_seen or h in global_seen_hashes:
                continue
            local_seen.add(h)
            order_key = hashlib.sha256(f"{SELECTION_SEED}{spec['org_id']}:{rel}".encode()).hexdigest()
            elig.append((order_key, rel, raw, h))

        elig.sort(key=lambda x: x[0])
        chosen_files: list[dict[str, Any]] = []
        chosen_docs: list[bytes] = []
        chosen_hashes: list[str] = []
        acc_bytes = 0
        for _, rel, raw, h in elig:
            if len(chosen_files) >= MAX_FILES_PER_ORG:
                break
            if acc_bytes + len(raw) > MAX_BYTES_PER_ORG and len(chosen_files) >= MIN_FILES_BEFORE_BYTE_SKIP:
                continue
            chosen_files.append({"rel_path": rel, "bytes": len(raw), "sha256": h})
            chosen_docs.append(raw)
            chosen_hashes.append(h)
            global_seen_hashes.add(h)
            acc_bytes += len(raw)
            if acc_bytes >= MAX_BYTES_PER_ORG:
                break

        if len(chosen_files) < 10:
            raise RuntimeError(f"calibration org {spec['org_id']} yielded too few files ({len(chosen_files)})")

        selected_lineages.append(
            {
                "lineage_id": spec["lineage_id"],
                "org_id": spec["org_id"],
                "upstream_repo": spec["upstream_repo"],
                "package_name": spec["package_name"],
                "version": version,
                "license": lic,
                "domain": spec["domain"],
                "role": "calibration_disjoint",
                "language": "python",
                "source": f"{spec['upstream_repo']} ({spec['package_name']}=={version}, local .venv site-packages)",
                "eligible_file_count": len(elig),
                "record_count": len(chosen_files),
                "source_bytes": acc_bytes,
                "files": chosen_files,
                "file_hashes": chosen_hashes,
                "docs": chosen_docs,
            }
        )

    audit = assert_calibration_disjoint_from_excluded(selected_lineages, reg)
    return selected_lineages, audit


def verify_live_site_packages_hashes(
    manifest: dict[str, Any],
    site_packages: Path = VENV_SITE_PACKAGES,
) -> dict[str, Any]:
    """Verify every file hash in calibration_manifest.json live against .venv site-packages if present."""
    if not site_packages.exists():
        return {
            "checked_live": False,
            "reason": f"site-packages absent at {site_packages}; deterministic receipt replay remains valid",
            "files_verified": 0,
        }
    total_files = 0
    mismatches = []
    missing = []
    for org in manifest["calibration_orgs"]:
        for f in org["files"]:
            p = site_packages / f["rel_path"]
            total_files += 1
            if not p.is_file():
                missing.append(f"{org['org_id']}:{f['rel_path']}")
                continue
            raw = p.read_bytes()
            if len(raw) != int(f["bytes"]) or AG.sha256_bytes(raw) != f["sha256"]:
                mismatches.append(f"{org['org_id']}:{f['rel_path']}")
    if missing or mismatches:
        raise AssertionError(
            f"live site-packages verification failed: missing={missing[:5]}, mismatches={mismatches[:5]}"
        )
    return {
        "checked_live": True,
        "site_packages": str(site_packages),
        "files_verified": total_files,
        "mismatches": 0,
    }


def build_calibration_manifest_and_grid(jobs: int = 8) -> tuple[dict[str, Any], dict[str, Any]]:
    """Build and independently decode all B1RA archives + micro-sketch receipts for 14 calibration orgs."""
    t0 = time.perf_counter()
    fit_corpus = AG.load_fit_corpus()
    chains = {name: AG.load_verified_chain(name) for name in AG.CHAIN_SPECS}
    cal_lineages, disjoint_audit = select_calibration_corpora_from_venv()

    # Fit frozen B1RA headers strictly on codenet_primary.
    headers = AG.fit_all_prefix_headers(chains, fit_corpus, jobs=jobs)

    # Serialize and independently decode EVERY (cal_org, chain, K) archive!
    t_eval0 = time.perf_counter()
    rows = AG.evaluate_full_grid(cal_lineages, chains, headers, jobs=jobs)
    eval_wall = time.perf_counter() - t_eval0

    # Extract micro-sketch features on primary chain with exact measured work.
    dicts_by_k = {
        K: AG.Dictionary(headers[(AG.PRIMARY_CHAIN_NAME, K)]["entries"]) for K in AG.PRIMARY_GRID
    }
    lengths_by_k = {
        K: headers[(AG.PRIMARY_CHAIN_NAME, K)]["lengths"] for K in AG.PRIMARY_GRID
    }
    sketch_receipts: dict[str, Any] = {}
    for lin in cal_lineages:
        lid = lin["lineage_id"]
        feat = SP.extract_micro_sketch_features(lin["docs"], dicts_by_k, lengths_by_k, SP.PROBE_KS)
        sketch_receipts[lid] = {
            "sketch_bytes": feat["sketch_bytes"],
            "sketch_records": feat["sketch_records"],
            "sketch_fraction": round(feat["sketch_fraction"], 6),
            "full_bytes": feat["full_bytes"],
            "full_records": feat["full_records"],
            "probe_ks": feat["probe_ks"],
            "probes_r": {str(k): v for k, v in feat["probes_r"].items()},
            "probes_tok": {str(k): v for k, v in feat["probes_tok"].items()},
            "paired_se_r": {f"{k1}:{k2}": v for (k1, k2), v in feat["paired_se_r"].items()},
            "paired_se_tok": {f"{k1}:{k2}": v for (k1, k2), v in feat["paired_se_tok"].items()},
            "work": feat["work"],
        }

    reg = collect_excluded_registry()
    manifest = {
        "schema": "gamma.bits-a1b.calibration-manifest.v1",
        "selection_rule": {
            "seed": SELECTION_SEED,
            "source_root": str(VENV_SITE_PACKAGES),
            "min_file_bytes": MIN_FILE_BYTES,
            "max_file_bytes": MAX_FILE_BYTES,
            "max_files_per_org": MAX_FILES_PER_ORG,
            "max_bytes_per_org": MAX_BYTES_PER_ORG,
            "excluded_path_parts": sorted(EXCLUDED_PATH_PARTS),
            "third_party_code_vendored": False,
        },
        "disjointness_audit": disjoint_audit,
        "capacity_audit_files_sha256": reg["capacity_audit_files_sha256"],
        "calibration_orgs": [
            {k: v for k, v in lin.items() if k != "docs"} for lin in cal_lineages
        ],
    }

    manifest_bytes = (json.dumps(manifest, indent=1) + "\n").encode("utf-8")
    manifest_sha = AG.sha256_bytes(manifest_bytes)

    cal_grid = {
        "schema": "gamma.bits-a1b.calibration-grid.v1",
        "calibration_manifest_sha256": manifest_sha,
        "primary_chain": AG.PRIMARY_CHAIN_NAME,
        "chains": {
            cname: {k: v for k, v in ch.items() if k not in ("singles", "fragments")}
            for cname, ch in chains.items()
        },
        "verified_archive_count": len(rows),
        "all_independent_decode_ok": all(
            r.get("independent_decode_ok") is True and r.get("fidelity") == 1.0 for r in rows
        ),
        "sketch_receipts": sketch_receipts,
        "rows": rows,
        "timing": {
            "evaluate_grid_wall_seconds": round(eval_wall, 3),
            "total_wall_seconds": round(time.perf_counter() - t0, 3),
        },
    }

    out_dir = HERE / "out"
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "calibration_manifest.json").write_bytes(manifest_bytes)
    (out_dir / "calibration_grid.json").write_text(json.dumps(cal_grid, indent=1) + "\n")
    return manifest, cal_grid


def main() -> int:
    jobs = min(8, os.cpu_count() or 1)
    manifest, cal_grid = build_calibration_manifest_and_grid(jobs=jobs)
    orgs = manifest["calibration_orgs"]
    print(
        f"Built and independently verified {cal_grid['verified_archive_count']} B1RA archives "
        f"across {len(orgs)} independent calibration orgs x {len(cal_grid['chains'])} chains "
        f"in {cal_grid['timing']['total_wall_seconds']:.2f}s (overlap_count=0)"
    )
    for o in orgs:
        print(
            f"  {o['org_id']:14s} | {o['package_name']:11s} v{o['version']:10s} | "
            f"{o['record_count']:2d} files, {o['source_bytes']:7,d} B | {o['domain']}"
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
