#!/usr/bin/env python3
"""One-shot sealed fresh-code evaluation runner for BITS A2 (PREREGISTRATION_DEPTH1.md).

Strictly enforces every preregistered invariant:
  1. Verifies exact SHA-256 identity of all 13 frozen artifacts in PREREGISTRATION_DEPTH1.md
     before inspecting or selecting any fresh file.
  2. Deterministically selects >= 20 independent fresh JavaScript repository lineages
     (24 distinct upstream GitHub organizations) from local node_modules, with ZERO
     overlap against corpus_split.json (exact + whitespace-squeezed SHA-256), all 59
     capacity/holdout lineages, and clocksmith/* repositories.
  3. Stages selected files in a temporary directory (zero third-party source vendored
     into git) and invokes the EXACT frozen unmodified `score_depth1_sealed.py` ONCE.
  4. Writes deterministic manifest metadata, `sealed_summary.json`, and `SEALED_REPORT.md`.
"""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
LIT = HERE.parent
DECO_ROOT = Path("/Users/xyz/deco")

# Exact SHA-256 table copied verbatim from PREREGISTRATION_DEPTH1.md Section 2.
FROZEN_SHA256: dict[str, str] = {
    "FORMAT.md": "fb69f8447d4535b872d4bd5c08b2524cef5f1910b89ff93023c10a9ac626b86a",
    "js_normalize_ast.mjs": "533a79f35dd2fb7e6fbbc1e77dc63ac81d81ecd6ea7eea73be901cac3a455c66",
    "verify_behavior.mjs": "50614d9a9683dbec862c31182861d989db078d72736d5f936974faa92d6acda2",
    "ast_frames.py": "706282d859ffb6fc4868f11cf1c6d52c73e3b29a8f27dd2319841fb457f482a2",
    "codec.py": "9b0d2ca64c17f9f550a243aa27852940d7edf16eb736c8c51544e9bb27838686",
    "independent_decode.py": "f18f40a132311a120d5257a2ca0af088c4b2bf43811a02cfe18875d85d806b7b",
    "score_depth1_sealed.py": "adf1089ea5262766d3309d24e477ebbd8defad1f163a681a8f5e182b85858f72",
    "eval_dev.py": "c65f07658130a728a1bc06fcd38ba06ac81d770e30b463321bc70f10f8d4e80e",
    "corpus_split.json": "175e529fb4d24c45ba4972e36af3378a608aa3b7893fec84baf6559bf2b6cc0e",
    "frozen/arm2_context_ast.header.a2bits": "27b98c044a78bf211245530493d0a92bc43732a82099eb29fd1d82d6dc9296c1",
    "frozen/arm3_depth1_frames.header.a2bits": "bbc390721469e6323fb2397f2aa02d78d833d7470b9d668904e7569cba4d2151",
    "out/dev_archives/arm2_context_ast.a2bits": "02eac2fdc88cf0da745537181ee1950f06e2e16f742f8dbeb8256cb787188f03",
    "out/dev_archives/arm3_depth1_frames.a2bits": "f1bb18f451028500646024d17f322290ddcbab910929b005a8284d2020f25028",
}

# 24 pre-committed independent upstream GitHub JS organizations (selected strictly before scoring).
FRESH_JS_ORG_SPECS: tuple[dict[str, str], ...] = (
    {"lineage": "repo:jsdom/jsdom", "pkg": "jsdom", "org": "jsdom"},
    {"lineage": "repo:microsoft/playwright", "pkg": "playwright-core", "org": "microsoft"},
    {"lineage": "repo:capricorn86/happy-dom", "pkg": "happy-dom", "org": "capricorn86"},
    {"lineage": "repo:Hopding/pdf-lib", "pkg": "pdf-lib", "org": "hopding"},
    {"lineage": "repo:huggingface/transformers.js", "pkg": "@huggingface/transformers", "org": "huggingface"},
    {"lineage": "repo:cloudflare/workers-sdk", "pkg": "miniflare", "org": "cloudflare"},
    {"lineage": "repo:sinclairzx81/typebox", "pkg": "@sinclair/typebox", "org": "sinclairzx81"},
    {"lineage": "repo:grpc/grpc-node", "pkg": "@grpc/grpc-js", "org": "grpc"},
    {"lineage": "repo:digitalbazaar/forge", "pkg": "node-forge", "org": "digitalbazaar"},
    {"lineage": "repo:toji/gl-matrix", "pkg": "gl-matrix", "org": "toji"},
    {"lineage": "repo:openai/openai-node", "pkg": "openai", "org": "openai"},
    {"lineage": "repo:testing-library/user-event", "pkg": "@testing-library/user-event", "org": "testing-library"},
    {"lineage": "repo:mochajs/mocha", "pkg": "mocha", "org": "mochajs"},
    {"lineage": "repo:csstree/csstree", "pkg": "css-tree", "org": "csstree"},
    {"lineage": "repo:preactjs/preact", "pkg": "preact", "org": "preactjs"},
    {"lineage": "repo:chjj/blessed", "pkg": "blessed", "org": "chjj"},
    {"lineage": "repo:vitest-dev/vitest", "pkg": "vitest", "org": "vitest-dev"},
    {"lineage": "repo:open-telemetry/opentelemetry-js", "pkg": "@opentelemetry/api", "org": "open-telemetry"},
    {"lineage": "repo:fb55/entities", "pkg": "entities", "org": "fb55"},
    {"lineage": "repo:ExodusOSS/bytes", "pkg": "@exodus/bytes", "org": "exodusoss"},
    {"lineage": "repo:connor4312/blake3", "pkg": "blake3-wasm", "org": "connor4312"},
    {"lineage": "repo:speed-highlight/core", "pkg": "@speed-highlight/core", "org": "speed-highlight"},
    {"lineage": "repo:kpdecker/jsdiff", "pkg": "diff", "org": "kpdecker"},
    {"lineage": "repo:websockets/ws", "pkg": "ws", "org": "websockets"},
)

NM_ROOTS = (
    DECO_ROOT / "doppler" / "node_modules",
    DECO_ROOT / "simulatte" / "node_modules",
    DECO_ROOT / "reploid" / "node_modules",
    DECO_ROOT / "react_starter" / "node_modules",
    DECO_ROOT / "valera" / "node_modules",
    DECO_ROOT / "256one" / "node_modules",
    DECO_ROOT / "party" / "node_modules",
)

SELECTION_SEED = "a2-depth1-sealed-v1:"
MIN_FILE_BYTES = 200
MAX_FILE_BYTES = 25_000
MAX_FILES_PER_REPO = 25
MAX_BYTES_PER_REPO = 60_000
EXCLUDED_PARTS = frozenset({"node_modules", "test", "tests", "__tests__", "benchmark", "benchmarks", "example", "examples", "docs", "doc"})


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def squeezed_sha256(data: bytes) -> str:
    return hashlib.sha256(b"".join(data.split())).hexdigest()


def verify_frozen_artifacts() -> dict[str, str]:
    verified: dict[str, str] = {}
    for rel, expected in FROZEN_SHA256.items():
        p = HERE / rel
        if not p.is_file():
            raise AssertionError(f"Missing frozen A2 artifact: {p}")
        actual = sha256_bytes(p.read_bytes())
        if actual != expected:
            raise AssertionError(f"Frozen SHA-256 mismatch for {rel}: got {actual}, expected {expected}")
        verified[rel] = actual
    return verified


def collect_excluded_hashes_and_tokens() -> tuple[set[str], set[str], set[str]]:
    split = json.loads((HERE / "corpus_split.json").read_text(encoding="utf-8"))
    raw_hashes: set[str] = set()
    sq_hashes: set[str] = set()
    for part in ("train", "dev"):
        for row in split[part]:
            raw_hashes.add(row["raw_sha256"])
            sq_hashes.add(row["squeezed_sha256"])

    # Also hash every file in closure-holdout-v1, objective-holdout-v1, codenet-replication-v1
    for sub in (
        LIT / "closure-holdout-v1" / "corpus",
        LIT / "objective-holdout-v1" / "corpus",
        LIT / "codenet-replication-v1" / "corpus",
    ):
        if sub.is_dir():
            for f in sub.rglob("*"):
                if f.is_file() and f.suffix in (".js", ".mjs", ".cjs"):
                    b = f.read_bytes()
                    raw_hashes.add(sha256_bytes(b))
                    sq_hashes.add(squeezed_sha256(b))

    cap_tokens = {
        "ramda", "express", "expressjs", "lodash", "three", "rxjs", "babel", "babel-runtime",
        "ajv", "eslint", "zod", "caniuse-lite", "date-fns", "semver", "postcss", "protobufjs",
        "undici", "doppler", "fawn", "gamma", "reploid", "clocksmith", "ggml", "ffmpeg", "cairo", "brotli",
    }
    return raw_hashes, sq_hashes, cap_tokens


def find_pkg_dir(pkg_name: str) -> Path:
    for root in NM_ROOTS:
        cand = root / pkg_name
        if (cand / "package.json").is_file():
            return cand
    raise FileNotFoundError(f"Package {pkg_name} not found in local node_modules")


def build_sealed_manifest(stage_dir: Path) -> dict[str, Any]:
    excl_raw, excl_sq, excl_tokens = collect_excluded_hashes_and_tokens()
    seen_orgs: set[str] = set()
    seen_raw: set[str] = set(excl_raw)
    seen_sq: set[str] = set(excl_sq)

    files_out: list[dict[str, Any]] = []
    repos_summary: list[dict[str, Any]] = []

    for spec in FRESH_JS_ORG_SPECS:
        org = spec["org"].lower()
        pkg = spec["pkg"]
        lineage = spec["lineage"]
        if org in seen_orgs:
            raise AssertionError(f"Duplicate org in sealed selection: {org}")
        seen_orgs.add(org)
        ident_toks = {org, pkg.lower(), pkg.split("/")[-1].lower()}
        if ident_toks & excl_tokens:
            raise AssertionError(f"Sealed repo {lineage} overlaps excluded token set: {ident_toks & excl_tokens}")

        pkg_dir = find_pkg_dir(pkg)
        meta = json.loads((pkg_dir / "package.json").read_text(encoding="utf-8", errors="ignore"))
        version = str(meta.get("version", "unknown"))

        elig: list[tuple[str, Path, str, bytes, str, str]] = []
        for f in pkg_dir.rglob("*.js"):
            rel = str(f.relative_to(pkg_dir))
            parts_low = {p.lower() for p in Path(rel).parts}
            if parts_low & EXCLUDED_PARTS:
                continue
            if f.name.endswith(".min.js") or f.name.endswith(".bundle.js"):
                continue
            if not f.is_file():
                continue
            raw = f.read_bytes()
            if not (MIN_FILE_BYTES <= len(raw) <= MAX_FILE_BYTES):
                continue
            if b"\x00" in raw:
                continue
            try:
                raw.decode("utf-8")
            except UnicodeDecodeError:
                continue
            rh = sha256_bytes(raw)
            sh = squeezed_sha256(raw)
            if rh in seen_raw or sh in seen_sq:
                continue
            order_key = hashlib.sha256(f"{SELECTION_SEED}{lineage}:{rel}".encode("utf-8")).hexdigest()
            elig.append((order_key, f, rel, raw, rh, sh))

        elig.sort(key=lambda x: x[0])
        chosen = 0
        acc_bytes = 0
        safe_slug = lineage.replace(":", "_").replace("/", "_")
        for _, fpath, rel, raw, rh, sh in elig:
            if chosen >= MAX_FILES_PER_REPO:
                break
            if acc_bytes + len(raw) > MAX_BYTES_PER_REPO and chosen >= 4:
                continue
            if rh in seen_raw or sh in seen_sq:
                continue
            seen_raw.add(rh)
            seen_sq.add(sh)
            staged_rel = f"{safe_slug}/{rel}"
            staged_path = stage_dir / staged_rel
            staged_path.parent.mkdir(parents=True, exist_ok=True)
            staged_path.write_bytes(raw)
            files_out.append({
                "path": staged_rel,
                "lineage": lineage,
                "pkg": pkg,
                "version": version,
                "rel_in_pkg": rel,
                "raw_bytes": len(raw),
                "raw_sha256": rh,
                "squeezed_sha256": sh,
            })
            chosen += 1
            acc_bytes += len(raw)
            if acc_bytes >= MAX_BYTES_PER_REPO:
                break

        if chosen < 4:
            raise AssertionError(f"Fresh repo {lineage} ({pkg}) yielded only {chosen} eligible files")
        repos_summary.append({
            "lineage": lineage,
            "org": org,
            "pkg": pkg,
            "version": version,
            "files": chosen,
            "raw_bytes": acc_bytes,
            "eligible_pool": len(elig),
        })

    assert len(repos_summary) >= 20, f"Preregistration requires >= 20 lineages, got {len(repos_summary)}"
    return {
        "schema": "gamma.bits.a2.depth1_sealed_manifest.v1",
        "set": "fresh_js_24repos_sealed_v1",
        "selection_seed": SELECTION_SEED,
        "lineages_total": len(repos_summary),
        "files_total": len(files_out),
        "raw_bytes_total": sum(r["raw_bytes"] for r in repos_summary),
        "disjointness_audit": {
            "excluded_raw_hashes_checked": len(excl_raw),
            "excluded_squeezed_hashes_checked": len(excl_sq),
            "excluded_lineage_tokens_checked": len(excl_tokens),
            "overlap_count": 0,
            "third_party_source_vendored": False,
        },
        "repos": repos_summary,
        "files": files_out,
    }


def render_sealed_report(manifest: dict[str, Any], score: dict[str, Any], frozen_verified: dict[str, str]) -> str:
    cb = score["complete_bits"]
    fid = score["fidelity"]
    wk = score["measured_work"]
    lines = [
        "# A2 Sealed Fresh-Code Evaluation Report: Depth-1 AST Frames (Arm 3) vs Context AST (Arm 2)",
        "",
        "## Verdict",
        "",
        f"- **Preregistered Sealed Verdict (`PREREGISTRATION_DEPTH1.md`):** **`{cb['verdict']}`**",
        f"- **Point Estimate (`delta_complete_pct`):** `{cb['delta_complete_pct']:+.4f}%` (`{cb['delta_complete_bits']:+d}` complete bits; Arm 3 `{cb['arm3_complete_bits']:,d}` vs Arm 2 `{cb['arm2_complete_bits']:,d}` bits)",
        f"- **Paired Repository-Lineage 95% CI (10,000 resamples, seed=20261127):** `[{cb['ci95_pct'][0]:+.4f}%, {cb['ci95_pct'][1]:+.4f}%]` (pass bar: point `<= -1.0%` AND 95% CI upper `<= -1.0%`)",
        f"- **Fidelity Gate:** `corrupt_decodes = {fid['corrupt_decodes']}`, `arm2_byte_exact = {fid['arm2_byte_exact']}`, `arm3_byte_exact = {fid['arm3_byte_exact']}` across `{fid['files_total']}` files / `{fid['lineages_total']}` independent JS repository lineages",
        f"- **AST Coverage & Charged Raw Fallback:** `{fid['ast_supported_files']}/{fid['files_total']}` AST-supported, `{fid['raw_fallback_files']}` raw-fallback files (`{fid['raw_fallback_byte_pct']:.2f}%` of `{cb['total_norm_bytes']:,d}` normalized bytes; kill threshold `> 25.0%`)",
        f"- **Decode Latency Ratio (p95):** Arm 3 `{wk['arm3_decode_p95_ms']:.3f} ms` vs Arm 2 `{wk['arm2_decode_p95_ms']:.3f} ms` (`{wk['arm3_decode_p95_ms'] / max(1e-9, wk['arm2_decode_p95_ms']):.2f}x`; kill threshold `> 5.0x`)",
        "- **Closed Arm Note:** Recursive Frames (`Arm 4, D_max=3`) remained CLOSED after its `-0.11%` dev FAIL and was NOT run on sealed code.",
        "",
        "## Frozen Preregistration Audit (13/13 SHA-256 Verified)",
        "",
        f"- `score_depth1_sealed.py`: `{frozen_verified['score_depth1_sealed.py']}` (invoked unmodified)",
        f"- `frozen/arm2_context_ast.header.a2bits`: `{frozen_verified['frozen/arm2_context_ast.header.a2bits']}` (`{cb['arm2_header_bits']:,d}` header bits)",
        f"- `frozen/arm3_depth1_frames.header.a2bits`: `{frozen_verified['frozen/arm3_depth1_frames.header.a2bits']}` (`{cb['arm3_header_bits']:,d}` header bits; `+{cb['arm3_header_bits'] - cb['arm2_header_bits']:,d}` bit header tax)",
        f"- Disjointness audit: `0` lineage, exact-SHA-256, or whitespace-squeezed-SHA-256 overlaps across `{manifest['disjointness_audit']['excluded_raw_hashes_checked']}` excluded source hashes.",
        "",
        "## Complete-Bits & Measured-Work Breakdown",
        "",
        "| Arm | Header Bits | Payload Bits | Complete Bits | Encode Wall (s) | Indep. Decode Wall (s) | Decode p95 (ms) |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
        f"| Arm 2 (Context AST, `D=0`) | {cb['arm2_header_bits']:,d} | {cb['arm2_payload_bits']:,d} | {cb['arm2_complete_bits']:,d} | {wk['arm2_encode_seconds']:.3f} | {wk['arm2_decode_seconds']:.3f} | {wk['arm2_decode_p95_ms']:.3f} |",
        f"| **Arm 3 (Depth-1 Frames, `D=1`)** | **{cb['arm3_header_bits']:,d}** | **{cb['arm3_payload_bits']:,d}** | **{cb['arm3_complete_bits']:,d}** | **{wk['arm3_encode_seconds']:.3f}** | **{wk['arm3_decode_seconds']:.3f}** | **{wk['arm3_decode_p95_ms']:.3f}** |",
        "",
        f"- Normalization wall: `{wk['normalize_seconds']:.3f} s`, total wall: `{wk['total_seconds']:.3f} s`, peak RSS: `{wk['peak_rss_mb']:.2f} MB`.",
        f"- Arm 3 exact 8-shift evaluations: `{wk['arm3_shift_evals']:,d}`, total Depth-1 frame uses: `{wk['arm3_frame_uses']:,d}`.",
        "",
        "## Fresh Sealed JS Repositories (24 Independent Lineages)",
        "",
        "| Lineage | Package | Version | Files | Raw Bytes |",
        "| --- | --- | --- | ---: | ---: |",
    ]
    for r in manifest["repos"]:
        lines.append(f"| `{r['lineage']}` | `{r['pkg']}` | `{r['version']}` | {r['files']} | {r['raw_bytes']:,d} |")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    frozen_verified = verify_frozen_artifacts()
    print(f"[A2 sealed] Verified 13/13 frozen SHA-256 artifacts from PREREGISTRATION_DEPTH1.md", flush=True)

    with tempfile.TemporaryDirectory(prefix="a2_sealed_") as tmp:
        tmp_path = Path(tmp)
        stage_dir = tmp_path / "src"
        out_dir = tmp_path / "out"
        manifest = build_sealed_manifest(stage_dir)
        manifest_path = tmp_path / "manifest.json"
        manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
        print(
            f"[A2 sealed] Built disjoint manifest: {manifest['lineages_total']} lineages, "
            f"{manifest['files_total']} files, {manifest['raw_bytes_total']:,d} raw bytes (0 overlaps)",
            flush=True,
        )

        proc = subprocess.run(
            [
                sys.executable,
                str(HERE / "score_depth1_sealed.py"),
                "--manifest",
                str(manifest_path),
                "--root",
                str(stage_dir),
                "--out",
                str(out_dir),
            ],
            capture_output=True,
            text=True,
            check=True,
        )
        print(proc.stdout, flush=True)
        score = json.loads((out_dir / "sealed_score_report.json").read_text(encoding="utf-8"))

    # Persist metadata-only manifest + sealed summary + SEALED_REPORT.md (zero third-party source vendored!)
    (HERE / "out").mkdir(parents=True, exist_ok=True)
    (HERE / "out" / "sealed_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    summary = {
        "schema": "gamma.bits.a2.depth1_sealed_summary.v1",
        "preregistration": "PREREGISTRATION_DEPTH1.md",
        "frozen_artifacts_verified_sha256": frozen_verified,
        "manifest_summary": {k: v for k, v in manifest.items() if k != "files"},
        "sealed_score": score,
    }
    (HERE / "sealed_summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    (HERE / "SEALED_REPORT.md").write_text(render_sealed_report(manifest, score, frozen_verified), encoding="utf-8")
    print(f"[A2 sealed] Wrote sealed_summary.json and SEALED_REPORT.md (verdict={score['complete_bits']['verdict']})", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
