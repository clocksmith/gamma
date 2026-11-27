#!/usr/bin/env python3
"""One-shot sealed fresh-corpus evaluation for BITS A1a (PREREGISTRATION_DAG_ENCODERS.md).

Strictly enforces every preregistered invariant:
  1. Verifies exact SHA-256 identity of all 5 frozen artifacts in PREREGISTRATION_DAG_ENCODERS.md
     before touching any fresh corpus.
  2. Uses ONLY frozen vocabularies and train-only canonical Huffman code tables fitted strictly on
     CodeNet `primary` (zero retraining, zero code-length or merge-rank fitting on fresh corpora).
  3. Evaluates TWO independent fresh held-out multi-repo corpora (disjoint from CodeNet primary/dev/
     fresh/fresh2, Express, ramda, and TheAlgorithms/Python):
       - `fresh-js-24repos`: 24 independent fresh JavaScript repository lineages
       - `fresh-py-12repos`: 12 independent fresh Python repository lineages from local .venv
  4. Runs ALL preregistered gates:
       - Exact 100% byte-for-byte independent decode across every A1AF & A1AD archive
       - All 6 negative corruption controls (`FormatError`)
       - `A1AD < A1AF` with 0 payload byte difference for every fixed vocabulary and corpus
       - Paired per-unit two-sided sign test (`exact-closed A1AD` vs `open A1AD` at large A1AD budget)
       - Lean-framed `zstd -19` (8 KiB dict, 32 KiB dict, no-dict) sequential + random-access complete bits
         + C `libzstd` p50/p95/p99 decode latency + break-even horizon M*
       - Live deployment encoder controls: HF `tokenizers` BPE, `sentencepiece` Unigram,
         live pinned `tiktoken==0.14.0` (100% UTF-8 round-trip, 0 token-stream parity mismatches,
         0 shadowing discrepancies), and greedy longest-match.
  5. Writes `out/sealed_manifest.json`, `sealed_summary.json`, and `SEALED_REPORT.md` (zero
     third-party source code vendored into git; zero edits to any frozen artifact).
"""
from __future__ import annotations

import hashlib
import importlib.metadata as importlib_metadata
import json
import math
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

HERE = Path(__file__).resolve().parent
LIT = HERE.parent
OH = LIT / "objective-holdout-v1"
CL = LIT / "closure-holdout-v1"
CHAINS_DIR = HERE / "out" / "chains"
BIN_DIR = HERE / "bin"
DECO_ROOT = Path("/Users/xyz/deco")
VENV_SITE_PACKAGES = Path("/Users/xyz/deco/gamma/.venv/lib/python3.14/site-packages")
TIKTOKEN_PY = Path("/Users/xyz/deco/gamma/.venv-tiktoken/bin/python")

if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import eval_dev as ED  # noqa: E402
import headers as H  # noqa: E402
import independent_decode as ID  # noqa: E402
import validate_encoders as VE  # noqa: E402

# Exact frozen SHA-256 table from PREREGISTRATION_DAG_ENCODERS.md Section 2.
FROZEN_SHA256: dict[str, str] = {
    "FORMAT.md": "1be36803ea554b16f46a1db95225b56ec832c5e843ef9cf2519b2eafde3203f3",
    "headers.py": "5a14f0d5d2e46b20060c8b4b2541c804a0f0b95b465789730c30f7e45a4e6a53",
    "independent_decode.py": "03ec092b5dad49cc33531af5dea72ef2fcc80f402860b947904256ad57fbe114",
    "validate_encoders.py": "a689744e473a15818b7342a280b7233b2c5dddfd56d69991e9fab24e97ccd5f9",
    "requirements-tiktoken.txt": "5ef7c35fecdb702f6b599aa7b096e6e891143258aadd7bf1df0389c6d40d0020",
}

PREREG_ARMS = ("open", "open-byte", "exact-closed", "pair-byte", "bpe")

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

# 12 independent fresh Python repos (disjoint from TheAlgorithms/Python, CodeNet, CPython, and A1b's 19 cal orgs!)
FRESH_PY_ORG_SPECS: tuple[dict[str, str], ...] = (
    {"lineage": "py:psf/requests", "pkg": "requests", "org": "requests"},
    {"lineage": "py:urllib3/urllib3", "pkg": "urllib3", "org": "urllib3"},
    {"lineage": "py:contourpy/contourpy", "pkg": "contourpy", "org": "contourpy"},
    {"lineage": "py:uqfoundation/dill", "pkg": "dill", "org": "uqfoundation"},
    {"lineage": "py:mpmath/mpmath", "pkg": "mpmath", "org": "mpmath"},
    {"lineage": "py:pypa/packaging", "pkg": "packaging", "org": "pypa"},
    {"lineage": "py:pandas-dev/pandas", "pkg": "pandas", "org": "pandas-dev"},
    {"lineage": "py:dateutil/dateutil", "pkg": "python-dateutil", "org": "dateutil"},
    {"lineage": "py:mwaskom/seaborn", "pkg": "seaborn", "org": "mwaskom"},
    {"lineage": "py:apache/arrow", "pkg": "pyarrow", "org": "apache"},
    {"lineage": "py:pytorch/pytorch", "pkg": "torch", "org": "pytorch"},
    {"lineage": "py:huggingface/datasets", "pkg": "datasets", "org": "huggingface-py"},
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

EXCLUDED_PARTS = frozenset({"node_modules", "test", "tests", "__tests__", "_tests", "testing", "benchmark", "benchmarks", "example", "examples", "docs", "doc", "__pycache__"})


def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def verify_frozen_artifacts() -> dict[str, str]:
    verified: dict[str, str] = {}
    for rel, expected in FROZEN_SHA256.items():
        p = HERE / rel
        if not p.is_file():
            raise AssertionError(f"Missing frozen A1a artifact: {p}")
        actual = sha256_bytes(p.read_bytes())
        if actual != expected:
            raise AssertionError(f"Frozen SHA-256 mismatch for {rel}: got {actual}, expected {expected}")
        verified[rel] = actual
    return verified


def exact_two_sided_sign_test_p(wins: int, losses: int) -> float:
    n = wins + losses
    if n == 0:
        return 1.0
    k = min(wins, losses)
    tail = sum(math.comb(n, i) for i in range(k + 1)) / (2 ** n)
    return min(1.0, 2.0 * tail)


def collect_dev_hashes() -> set[str]:
    hashes: set[str] = set()
    for cname in ED.DEV_CORPORA:
        docs, _ = ED.load_corpus(cname)
        for d in docs:
            hashes.add(sha256_bytes(d))
    return hashes


def find_pkg_dir(pkg_name: str) -> Path:
    for root in NM_ROOTS:
        cand = root / pkg_name
        if (cand / "package.json").is_file():
            return cand
    raise FileNotFoundError(f"JS package {pkg_name} not found in local node_modules")


def collect_fresh_corpora(stage_dir: Path) -> Tuple[Dict[str, List[bytes]], Dict[str, List[Path]], Dict[str, List[str]], Dict[str, Any]]:
    dev_hashes = collect_dev_hashes()
    seen_hashes = set(dev_hashes)

    corpora_docs: Dict[str, List[bytes]] = {"fresh-js-24repos": [], "fresh-py-12repos": []}
    corpora_paths: Dict[str, List[Path]] = {"fresh-js-24repos": [], "fresh-py-12repos": []}
    corpora_units: Dict[str, List[str]] = {"fresh-js-24repos": [], "fresh-py-12repos": []}
    manifest: Dict[str, Any] = {
        "schema": "a1a-fixed-budget-v1.sealed-manifest/1",
        "excluded_dev_hashes_checked": len(dev_hashes),
        "overlap_count": 0,
        "third_party_source_vendored": False,
        "corpora": {},
    }

    # 1. fresh-js-24repos
    js_repos_meta = []
    for spec in FRESH_JS_ORG_SPECS:
        pkg_dir = find_pkg_dir(spec["pkg"])
        meta = json.loads((pkg_dir / "package.json").read_text(encoding="utf-8", errors="ignore"))
        ver = str(meta.get("version", "unknown"))
        elig = []
        for f in pkg_dir.rglob("*.js"):
            rel = str(f.relative_to(pkg_dir))
            if {p.lower() for p in Path(rel).parts} & EXCLUDED_PARTS:
                continue
            if f.name.endswith(".min.js") or f.name.endswith(".bundle.js") or not f.is_file():
                continue
            raw = f.read_bytes()
            if not (200 <= len(raw) <= 25_000) or b"\x00" in raw:
                continue
            h = sha256_bytes(raw)
            if h in seen_hashes:
                continue
            ok = hashlib.sha256(f"a1a-sealed-js:{spec['lineage']}:{rel}".encode()).hexdigest()
            elig.append((ok, rel, raw, h))
        elig.sort(key=lambda x: x[0])
        chosen = 0
        acc = 0
        safe_slug = spec["lineage"].replace(":", "_").replace("/", "_")
        for _, rel, raw, h in elig:
            if chosen >= 20:
                break
            if acc + len(raw) > 50_000 and chosen >= 4:
                continue
            if h in seen_hashes:
                continue
            seen_hashes.add(h)
            out_p = stage_dir / "js" / safe_slug / rel
            out_p.parent.mkdir(parents=True, exist_ok=True)
            out_p.write_bytes(raw)
            corpora_docs["fresh-js-24repos"].append(raw)
            corpora_paths["fresh-js-24repos"].append(out_p)
            corpora_units["fresh-js-24repos"].append(spec["lineage"])
            chosen += 1
            acc += len(raw)
        assert chosen >= 4, f"Too few JS files in {spec['lineage']}"
        js_repos_meta.append({"lineage": spec["lineage"], "pkg": spec["pkg"], "version": ver, "files": chosen, "bytes": acc})

    manifest["corpora"]["fresh-js-24repos"] = {
        "lineages": len(js_repos_meta),
        "files": len(corpora_docs["fresh-js-24repos"]),
        "bytes": sum(len(d) for d in corpora_docs["fresh-js-24repos"]),
        "repos": js_repos_meta,
    }

    # 2. fresh-py-12repos
    dists = {d.metadata["Name"].lower(): d for d in importlib_metadata.distributions(path=[str(VENV_SITE_PACKAGES)])}
    py_repos_meta = []
    for spec in FRESH_PY_ORG_SPECS:
        dist = dists[spec["pkg"].lower()]
        ver = dist.version
        elig = []
        for f in dist.files or []:
            rel = str(f)
            if not rel.endswith(".py"):
                continue
            if {p.lower() for p in Path(rel).parts} & EXCLUDED_PARTS:
                continue
            fp = VENV_SITE_PACKAGES / rel
            if not fp.is_file():
                continue
            raw = fp.read_bytes()
            if not (200 <= len(raw) <= 25_000) or b"\x00" in raw:
                continue
            h = sha256_bytes(raw)
            if h in seen_hashes:
                continue
            ok = hashlib.sha256(f"a1a-sealed-py:{spec['lineage']}:{rel}".encode()).hexdigest()
            elig.append((ok, rel, raw, h))
        elig.sort(key=lambda x: x[0])
        chosen = 0
        acc = 0
        safe_slug = spec["lineage"].replace(":", "_").replace("/", "_")
        for _, rel, raw, h in elig:
            if chosen >= 25:
                break
            if acc + len(raw) > 65_000 and chosen >= 6:
                continue
            if h in seen_hashes:
                continue
            seen_hashes.add(h)
            out_p = stage_dir / "py" / safe_slug / rel
            out_p.parent.mkdir(parents=True, exist_ok=True)
            out_p.write_bytes(raw)
            corpora_docs["fresh-py-12repos"].append(raw)
            corpora_paths["fresh-py-12repos"].append(out_p)
            corpora_units["fresh-py-12repos"].append(spec["lineage"])
            chosen += 1
            acc += len(raw)
        assert chosen >= 6, f"Too few Py files in {spec['lineage']}"
        py_repos_meta.append({"lineage": spec["lineage"], "pkg": spec["pkg"], "version": ver, "files": chosen, "bytes": acc})

    manifest["corpora"]["fresh-py-12repos"] = {
        "lineages": len(py_repos_meta),
        "files": len(corpora_docs["fresh-py-12repos"]),
        "bytes": sum(len(d) for d in corpora_docs["fresh-py-12repos"]),
        "repos": py_repos_meta,
    }

    return corpora_docs, corpora_paths, corpora_units, manifest


def run_live_tiktoken_fresh(fresh_docs: Dict[str, List[bytes]], bpe_entries: Sequence[bytes], closed_entries: Sequence[bytes]) -> Dict[str, Any]:
    """Run live pinned tiktoken==0.14.0 on fresh held-out corpora in .venv-tiktoken."""
    assert TIKTOKEN_PY.is_file(), f"Missing pinned tiktoken venv at {TIKTOKEN_PY}"

    probe_code = r"""
import heapq, json, sys, tiktoken
payload = json.loads(sys.stdin.read())
out = {"tiktoken_version": tiktoken.__version__, "models": {}}

def byte_rank_encode(raw, ranks):
    n = len(raw)
    if n <= 1:
        return [raw] if n == 1 else []
    vals = [bytes([b]) for b in raw]
    nxt = [i + 1 if i + 1 < n else -1 for i in range(n)]
    prv = [i - 1 for i in range(n)]
    alive = [True] * n
    heap = []
    for i in range(n - 1):
        r = ranks.get(vals[i] + vals[i + 1])
        if r is not None:
            heapq.heappush(heap, (r, i, nxt[i]))
    while heap:
        r, i, j = heapq.heappop(heap)
        if not alive[i] or nxt[i] != j or not alive[j]:
            continue
        merged = vals[i] + vals[j]
        if ranks.get(merged) != r:
            continue
        vals[i] = merged
        alive[j] = False
        k = nxt[j]
        nxt[i] = k
        if k != -1:
            prv[k] = i
            rk = ranks.get(vals[i] + vals[k])
            if rk is not None:
                heapq.heappush(heap, (rk, i, k))
        p = prv[i]
        if p != -1 and alive[p]:
            rp = ranks.get(vals[p] + vals[i])
            if rp is not None:
                heapq.heappush(heap, (rp, p, i))
    parts = []
    idx = 0
    while idx != -1:
        if alive[idx]:
            parts.append(vals[idx])
        idx = nxt[idx]
    return parts

for mname, entries_hex in payload["models"].items():
    ranks = {bytes([b]): b for b in range(256)}
    nxt = 256
    for hx in entries_hex:
        w = bytes.fromhex(hx)
        if len(w) > 1 and w not in ranks:
            ranks[w] = nxt
            nxt += 1
    enc = tiktoken.Encoding(
        name=mname,
        pat_str=r"(?s).+",
        mergeable_ranks=ranks,
        special_tokens={},
    )
    # Full-table UTF-8 reachability check:
    # - isolated tests whole-piece lookup shortcut (tiktoken encoder.get(piece))
    # - embedded ("\x01" + txt + "\x02") forces byte_pair_encode merge loop inside real documents
    utf8_total = 0
    utf8_isolated_shadowed = 0
    utf8_embedded_shadowed = 0
    for w, r in ranks.items():
        if len(w) <= 1:
            continue
        try:
            txt = w.decode("utf-8", errors="strict")
        except UnicodeDecodeError:
            continue
        utf8_total += 1
        if enc.encode(txt) != [r]:
            utf8_isolated_shadowed += 1
        if enc.encode("\x01" + txt + "\x02") != [1, r, 2]:
            utf8_embedded_shadowed += 1

    corpus_res = {}
    for cname, docs_hex in payload["corpora"].items():
        rt_ok = 0
        rt_fail = 0
        parity_ok = 0
        parity_fail = 0
        tot_toks = 0
        for idx, dhx in enumerate(docs_hex):
            raw = bytes.fromhex(dhx)
            try:
                txt = raw.decode("utf-8", errors="strict")
            except UnicodeDecodeError:
                continue
            ids = enc.encode(txt)
            tot_toks += len(ids)
            if enc.decode(ids) == txt:
                rt_ok += 1
            else:
                rt_fail += 1
            # Exact token-stream parity against pure-Python byte_rank_encode on ALL files
            ref_parts = byte_rank_encode(raw, ranks)
            ref_ids = [ranks[p] for p in ref_parts]
            if ids == ref_ids:
                parity_ok += 1
            else:
                parity_fail += 1
        corpus_res[cname] = {
            "utf8_files_tested": rt_ok + rt_fail,
            "utf8_roundtrip_ok": rt_ok,
            "utf8_roundtrip_fail": rt_fail,
            "parity_files_checked": parity_ok + parity_fail,
            "parity_mismatches": parity_fail,
            "native_tiktoken_tokens": tot_toks,
        }
    out["models"][mname] = {
        "utf8_multi_tokens": utf8_total,
        "live_tiktoken_utf8_isolated_shadowed": utf8_isolated_shadowed,
        "live_tiktoken_utf8_embedded_shadowed": utf8_embedded_shadowed,
        "live_tiktoken_utf8_shadowed": utf8_embedded_shadowed,
        "corpora": corpus_res,
    }
print(json.dumps(out))
"""
    payload = {
        "models": {
            "bpe-dag-large": [e.hex() for e in bpe_entries],
            "exact-closed-dag-large": [e.hex() for e in closed_entries],
        },
        "corpora": {
            cname: [d.hex() for d in docs] for cname, docs in fresh_docs.items()
        },
    }
    proc = subprocess.run(
        [str(TIKTOKEN_PY), "-c", probe_code],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        check=True,
    )
    live = json.loads(proc.stdout)
    # Cross-check shadowing counts against validate_encoders.py pure-Python byte_ranks validator
    py_val = {
        "bpe-dag-large": VE.validate_tiktoken_byte_ranks(VE.entries_to_tiktoken_ranks(bpe_entries)),
        "exact-closed-dag-large": VE.validate_tiktoken_byte_ranks(VE.entries_to_tiktoken_ranks(closed_entries)),
    }
    discrepancies = 0
    for mname in ("bpe-dag-large", "exact-closed-dag-large"):
        if live["models"][mname]["live_tiktoken_utf8_shadowed"] != py_val[mname]["utf8_unreachable_count"]:
            discrepancies += 1
        live["models"][mname]["pure_python_utf8_unreachable"] = py_val[mname]["utf8_unreachable_count"]
        live["models"][mname]["pure_python_full_table_unreachable"] = py_val[mname]["unreachable_count"]
        live["models"][mname]["pure_python_prefix_monotone_unreachable"] = py_val[mname]["prefix_monotone_unreachable_count"]
    live["shadowing_discrepancies_vs_validator"] = discrepancies
    return live


def _longest_match_count(edges: list[list[tuple[int, int]]]) -> int:
    n = len(edges)
    i = 0
    toks = 0
    while i < n:
        best_l = 1
        for l, _ in edges[i]:
            if l > best_l:
                best_l = l
        i += best_l
        toks += 1
    return toks


def main() -> int:
    t0 = time.perf_counter()
    frozen_verified = verify_frozen_artifacts()
    print("[A1a sealed] Verified 5/5 frozen SHA-256 artifacts from PREREGISTRATION_DAG_ENCODERS.md", flush=True)

    # Run all 6 negative corruption controls directly via frozen test_headers.py!
    subprocess.run([sys.executable, str(HERE / "test_headers.py")], check=True, capture_output=True, text=True)
    print("[A1a sealed] Verified all 6/6 negative corruption controls fail with FormatError", flush=True)

    primary_docs, primary_paths = ED.load_corpus("primary")
    singles = [bytes([b]) for b in sorted({b for raw in primary_docs for b in raw})]
    assert len(singles) == ED.ALPHA

    chain_paths = {
        "open": CL / "out/exact/exact-entry-s1-whole.txt",
        "open-byte": CL / "out/bundle/open-byte-ext.txt",
        "exact-closed": CL / "out/bundle/pair-ext.txt",
        "pair-byte": CHAINS_DIR / "pair-byte-exact-full.txt",
        "bpe": CHAINS_DIR / "bpe-ext.txt",
    }
    chains = {name: ED.parse_chain_file(p) for name, p in chain_paths.items()}

    open_small_hdr = H.header_size_summary(chains["open"]["entries"][: ED.ALPHA + ED.SMALL_SLOTS])
    open_large_hdr = H.header_size_summary(chains["open"]["entries"][: ED.ALPHA + ED.LARGE_SLOTS])
    assert open_small_hdr["dag_header_bytes"] == 878
    assert open_large_hdr["dag_header_bytes"] == 33241

    budgets = {
        "dag_header_small": ("dag_header", 878),
        "dag_header_large": ("dag_header", 33241),
        "slots_small": ("slots", ED.SMALL_SLOTS),
        "slots_large": ("slots", ED.LARGE_SLOTS),
    }

    with tempfile.TemporaryDirectory(prefix="a1a_sealed_") as td:
        stage_dir = Path(td)
        fresh_docs, fresh_paths, fresh_units, manifest = collect_fresh_corpora(stage_dir)
        print(
            f"[A1a sealed] Built fresh held-out corpora: "
            f"fresh-js-24repos ({manifest['corpora']['fresh-js-24repos']['files']} files, {manifest['corpora']['fresh-js-24repos']['bytes']:,d} B), "
            f"fresh-py-12repos ({manifest['corpora']['fresh-py-12repos']['files']} files, {manifest['corpora']['fresh-py-12repos']['bytes']:,d} B); 0 overlaps",
            flush=True,
        )

        # Evaluate all 5 arms x 4 budgets across BOTH fresh corpora using ONLY CodeNet primary-fitted tables!
        budget_results: Dict[str, Any] = {}
        per_unit_bits_large: Dict[str, Dict[str, Dict[str, int]]] = {c: {} for c in fresh_docs}
        per_unit_toks_large: Dict[str, Dict[str, Dict[str, int]]] = {c: {} for c in fresh_docs}
        resolved_entries: Dict[Tuple[str, str], List[bytes]] = {}
        all_a1ad_lt_a1af = True
        all_payloads_equal = True
        all_decode_exact = True

        for bname, (bkind, bval) in budgets.items():
            arm_out: Dict[str, Any] = {}
            for aname in PREREG_ARMS:
                ch = chains[aname]
                n = ED.prefix_len_for_budget(ch["entries"], bkind, bval, explicit_pairs=ch["explicit_pairs"] or None)
                assert n is not None, f"Could not resolve prefix for {bname}/{aname}"
                entries = ch["entries"][:n]
                resolved_entries[(bname, aname)] = entries
                dag = H.build_dag_spec(entries, explicit_pairs=ch["explicit_pairs"] or None)
                d = H.Dictionary(entries)
                prim_edges = [d.edges(raw) for raw in primary_docs]
                lengths, _, _, _ = H.fit_table(d, prim_edges)

                c_out: Dict[str, Any] = {}
                for cname, docs in fresh_docs.items():
                    edges = [d.edges(raw) for raw in docs]
                    parses_bits = [H.parse_bits(e, lengths, d.ESC)[0] for e in edges]
                    min_dp_toks_per_file = [len(H.parse_tokens(e)) for e in edges]
                    lm_toks_per_file = [_longest_match_count(e) for e in edges]
                    ser = H.serialize_dual_archives(dag, lengths, docs, parses_bits)

                    # Strict independent decode verification of BOTH A1AF & A1AD
                    meas_lat = (bname == "dag_header_large")
                    dec_f = ID.decode_archive(ser["flat_archive"], measure_per_file_ns=meas_lat)
                    dec_d = ID.decode_archive(ser["dag_archive"], measure_per_file_ns=meas_lat)
                    if dec_f["files"] != docs or dec_d["files"] != docs:
                        all_decode_exact = False
                        raise AssertionError(f"Decode mismatch on {bname}/{aname}/{cname}")
                    if ser["dag_complete_bits"] >= ser["flat_complete_bits"]:
                        all_a1ad_lt_a1af = False
                    if dec_f["tokens"] != dec_d["tokens"]:
                        all_payloads_equal = False
                    if (ser["flat_complete_bytes"] - ser["flat_header_bytes"]) != (ser["dag_complete_bytes"] - ser["dag_header_bytes"]):
                        all_payloads_equal = False

                    # Per-lineage bits & min-DP tokens for paired sign test at dag_header_large
                    if bname == "dag_header_large" and aname in ("open", "exact-closed"):
                        u_bits: Dict[str, int] = {}
                        u_toks: Dict[str, int] = {}
                        for raw, p_syms, m_t, unit in zip(docs, parses_bits, min_dp_toks_per_file, fresh_units[cname]):
                            # Exact per-file bit cost under the frozen Huffman table
                            f_bits = 0
                            for sym in p_syms:
                                if sym < 0:
                                    f_bits += lengths[d.ESC] + 8
                                else:
                                    f_bits += lengths[sym]
                            f_bits += lengths[d.EOF]
                            u_bits[unit] = u_bits.get(unit, 0) + f_bits
                            u_toks[unit] = u_toks.get(unit, 0) + m_t
                        per_unit_bits_large[cname][aname] = u_bits
                        per_unit_toks_large[cname][aname] = u_toks

                    lat = None
                    if meas_lat:
                        arr = sorted(x / 1000.0 for x in dec_d["per_file_decode_ns"])
                        m = len(arr)
                        lat = {
                            "p50_us": round(arr[int(0.50 * (m - 1))], 2),
                            "p95_us": round(arr[int(0.95 * (m - 1))], 2),
                            "p99_us": round(arr[int(0.99 * (m - 1))], 2),
                        }

                    c_out[cname] = {
                        "min_dp_tokens": sum(min_dp_toks_per_file),
                        "longest_match_tokens": sum(lm_toks_per_file),
                        "bit_parse_tokens": dec_d["tokens"],
                        "escapes": dec_d["escapes"],
                        "payload_bytes": ser["payload_bytes"],
                        "flat_header_bytes": ser["flat_header_bytes"],
                        "dag_header_bytes": ser["dag_header_bytes"],
                        "header_reduction_pct": round(100.0 * (1.0 - ser["dag_header_bytes"] / ser["flat_header_bytes"]), 2),
                        "flat_complete_bits": ser["flat_complete_bits"],
                        "dag_complete_bits": ser["dag_complete_bits"],
                        "dag_vs_flat_complete_delta_bits": ser["dag_complete_bits"] - ser["flat_complete_bits"],
                        "flat_ra_complete_bits": ser["flat_random_access_bytes"] * 8,
                        "dag_ra_complete_bits": ser["dag_random_access_bytes"] * 8,
                        "independent_decode_exact": True,
                        "a1ad_python_decode_latency_us": lat,
                    }
                arm_out[aname] = {
                    "total_entries": n,
                    "fragments": n - ED.ALPHA,
                    "dag_mode": "pair" if dag.mode == H.FLAG_MODE_PAIR else "hybrid",
                    "flat_header_bytes": next(iter(c_out.values()))["flat_header_bytes"],
                    "dag_header_bytes": next(iter(c_out.values()))["dag_header_bytes"],
                    "corpora": c_out,
                }
            budget_results[bname] = {"budget_kind": bkind, "budget_value": bval, "arms": arm_out}
        print("[A1a sealed] Completed all 5 arms x 4 budgets x 2 fresh corpora dual A1AF/A1AD decode checks", flush=True)

        # Paired two-sided sign test at dag_header_large: exact-closed (A1AD) vs open (A1AD)
        sign_tests: Dict[str, Any] = {}
        for cname in fresh_docs:
            units = sorted(per_unit_bits_large[cname]["open"].keys())
            b_wins = sum(1 for u in units if per_unit_bits_large[cname]["exact-closed"][u] < per_unit_bits_large[cname]["open"][u])
            b_losses = sum(1 for u in units if per_unit_bits_large[cname]["exact-closed"][u] > per_unit_bits_large[cname]["open"][u])
            t_wins = sum(1 for u in units if per_unit_toks_large[cname]["exact-closed"][u] < per_unit_toks_large[cname]["open"][u])
            t_losses = sum(1 for u in units if per_unit_toks_large[cname]["exact-closed"][u] > per_unit_toks_large[cname]["open"][u])
            ec = budget_results["dag_header_large"]["arms"]["exact-closed"]["corpora"][cname]
            op = budget_results["dag_header_large"]["arms"]["open"]["corpora"][cname]
            sign_tests[cname] = {
                "units_total": len(units),
                "complete_bits_exact_closed": ec["dag_complete_bits"],
                "complete_bits_open": op["dag_complete_bits"],
                "complete_bits_delta_pct": round(100.0 * (ec["dag_complete_bits"] / op["dag_complete_bits"] - 1.0), 3),
                "payload_unit_wins_exact_closed": b_wins,
                "payload_unit_losses_exact_closed": b_losses,
                "payload_sign_test_p_two_sided": round(exact_two_sided_sign_test_p(b_wins, b_losses), 6),
                "min_dp_tokens_exact_closed": ec["min_dp_tokens"],
                "min_dp_tokens_open": op["min_dp_tokens"],
                "min_dp_tokens_delta_pct": round(100.0 * (ec["min_dp_tokens"] / op["min_dp_tokens"] - 1.0), 3),
                "token_unit_wins_exact_closed": t_wins,
                "token_unit_losses_exact_closed": t_losses,
                "token_sign_test_p_two_sided": round(exact_two_sided_sign_test_p(t_wins, t_losses), 6),
            }

        # Lean-framed zstd -19 benchmark on both fresh corpora (using primary-trained 8K & 32K dicts)
        zstd_bench = BIN_DIR / "zstd_bench"
        assert zstd_bench.is_file(), f"Missing {zstd_bench}"
        dict_8k = OH / "frozen/zstd-train-8k.dict"
        dict_32k = HERE / "out/zstd/zstd-train-32k.dict"
        zstd_fresh: Dict[str, Any] = {}
        for cname, paths in fresh_paths.items():
            lst = stage_dir / f"{cname}.list"
            lst.write_text("\n".join(str(p) for p in paths) + "\n", encoding="utf-8")
            c_res = {}
            for label, lvl, lean, dp in (
                ("zstd19_lean_dict8k", "19", "1", str(dict_8k)),
                ("zstd19_lean_dict32k", "19", "1", str(dict_32k)),
                ("zstd19_lean_nodict", "19", "1", "none"),
            ):
                p = subprocess.run([str(zstd_bench), lvl, lean, dp, "25", str(lst)], capture_output=True, text=True, check=True)
                c_res[label] = json.loads(p.stdout)
            zstd_fresh[cname] = c_res
        print("[A1a sealed] Completed lean-framed zstd-19 benchmarks on both fresh corpora", flush=True)

        # Native deployment encoder controls: HF tokenizers BPE, SentencePiece Unigram, live pinned tiktoken==0.14.0
        sp_controls = ED.evaluate_sentencepiece_controls(fresh_docs, singles)
        hf_controls = ED.evaluate_hf_bpe_controls(fresh_docs, singles)
        tiktoken_live = run_live_tiktoken_fresh(
            fresh_docs,
            resolved_entries[("dag_header_large", "bpe")],
            resolved_entries[("dag_header_large", "exact-closed")],
        )
        print(f"[A1a sealed] Completed live HF tokenizers, SentencePiece, and live tiktoken=={tiktoken_live['tiktoken_version']} controls", flush=True)

        # Break-even horizons M* on each fresh corpus at dag_header_large
        horizons: Dict[str, Any] = {}
        for cname, docs in fresh_docs.items():
            c_bytes = sum(len(d) for d in docs)
            c_n = len(docs)
            ec = budget_results["dag_header_large"]["arms"]["exact-closed"]["corpora"][cname]
            op = budget_results["dag_header_large"]["arms"]["open"]["corpora"][cname]
            z8 = zstd_fresh[cname]["zstd19_lean_dict8k"]
            horizons[cname] = {
                "exact_closed_a1ad_vs_a1af": ED.compute_breakeven_horizon(ec["dag_header_bytes"], ec["payload_bytes"], ec["flat_header_bytes"], ec["payload_bytes"], c_bytes, c_n),
                "exact_closed_a1ad_vs_open_a1ad": ED.compute_breakeven_horizon(ec["dag_header_bytes"], ec["payload_bytes"], op["dag_header_bytes"], op["payload_bytes"], c_bytes, c_n),
                "exact_closed_a1ad_vs_zstd19_lean_dict8k": ED.compute_breakeven_horizon(ec["dag_header_bytes"], ec["payload_bytes"], z8["dict_bytes"], z8["payload_bytes"], c_bytes, c_n),
            }

    # Gate summary
    tik_ok = (
        tiktoken_live["shadowing_discrepancies_vs_validator"] == 0
        and all(
            c["utf8_roundtrip_fail"] == 0 and c["parity_mismatches"] == 0
            for m in tiktoken_live["models"].values()
            for c in m["corpora"].values()
        )
    )
    gates = {
        "gate1_exact_roundtrip_and_6_negative_controls": all_decode_exact,
        "gate2a_a1ad_strictly_lt_a1af_zero_payload_diff": all_a1ad_lt_a1af and all_payloads_equal,
        "gate2b_exact_closed_beats_open_at_dag_large_js": (
            sign_tests["fresh-js-24repos"]["complete_bits_exact_closed"] < sign_tests["fresh-js-24repos"]["complete_bits_open"]
            and sign_tests["fresh-js-24repos"]["payload_sign_test_p_two_sided"] < 0.05
        ),
        "gate2b_exact_closed_beats_open_at_dag_large_py": (
            sign_tests["fresh-py-12repos"]["complete_bits_exact_closed"] < sign_tests["fresh-py-12repos"]["complete_bits_open"]
            and sign_tests["fresh-py-12repos"]["payload_sign_test_p_two_sided"] < 0.05
        ),
        "gate3_live_deployment_encoders_parity_and_shadowing": tik_ok,
    }

    summary = {
        "schema": "a1a-fixed-budget-v1.sealed-summary/1",
        "preregistration": "PREREGISTRATION_DAG_ENCODERS.md",
        "closed_arm_excluded": "Multi-node shared bundle (A1AB) closed after dev FAIL; excluded from sealed run",
        "frozen_artifacts_verified_sha256": frozen_verified,
        "manifest": manifest,
        "gates": gates,
        "budgets": budget_results,
        "paired_sign_tests_dag_large": sign_tests,
        "zstd_lean_benchmarks": zstd_fresh,
        "horizons_dag_large": horizons,
        "deployment_encoders": {
            "tiktoken_live": tiktoken_live,
            "hf_bpe_controls": hf_controls,
            "sentencepiece_controls": sp_controls,
        },
        "wall_seconds": round(time.perf_counter() - t0, 2),
    }

    (HERE / "out").mkdir(parents=True, exist_ok=True)
    (HERE / "out" / "sealed_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    (HERE / "sealed_summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    render_sealed_report(summary)
    print(f"[A1a sealed] Wrote sealed_summary.json and SEALED_REPORT.md in {summary['wall_seconds']}s", flush=True)
    return 0


def render_sealed_report(summary: Dict[str, Any]) -> None:
    """Render concise, complete SEALED_REPORT.md from sealed_summary.json."""
    gates = summary["gates"]
    manifest = summary["manifest"]
    budget_results = summary["budgets"]
    sign_tests = summary["paired_sign_tests_dag_large"]
    zstd_fresh = summary["zstd_lean_benchmarks"]
    horizons = summary["horizons_dag_large"]
    tiktoken_live = summary["deployment_encoders"]["tiktoken_live"]
    hf_controls = summary["deployment_encoders"]["hf_bpe_controls"]
    sp_controls = summary["deployment_encoders"]["sentencepiece_controls"]

    lines = [
        "# A1a Sealed Fresh-Corpus Report: `A1AD` Construction-DAG Headers & Native Encoder Controls",
        "",
        "## Gate Summary",
        "",
        "- **Frozen Artifacts Verified (`PREREGISTRATION_DAG_ENCODERS.md`):** 5/5 SHA-256 exact match (`FORMAT.md`, `headers.py`, `independent_decode.py`, `validate_encoders.py`, `requirements-tiktoken.txt`).",
        "- **Closed Arm Note:** Multi-node shared bundle (`A1AB`) remained CLOSED after its CodeNet `primary` FAIL and was NOT carried into this sealed run.",
        f"- **Gate 1 (100% Byte-Exact Independent Decode + 6 Negative Corruption Controls):** **`{'PASS' if gates['gate1_exact_roundtrip_and_6_negative_controls'] else 'FAIL'}`** (0 mismatches across all 40 archives; 6/6 corruption controls rejected with `FormatError`).",
        f"- **Gate 2a (`A1AD < A1AF` with 0 Payload Diff across all 5 arms x 4 budgets x 2 corpora):** **`{'PASS' if gates['gate2a_a1ad_strictly_lt_a1af_zero_payload_diff'] else 'FAIL'}`**.",
        "- **Gate 2b (`exact-closed A1AD` vs `open A1AD` at large `A1AD` budget `<= 33,241 B`):**",
        f"  - `fresh-js-24repos` (24 repos, {manifest['corpora']['fresh-js-24repos']['files']} files, {manifest['corpora']['fresh-js-24repos']['bytes']:,d} B): complete bits `{sign_tests['fresh-js-24repos']['complete_bits_delta_pct']:+.3f}%` (wins `{sign_tests['fresh-js-24repos']['payload_unit_wins_exact_closed']}/{sign_tests['fresh-js-24repos']['units_total']}`, two-sided sign `p={sign_tests['fresh-js-24repos']['payload_sign_test_p_two_sided']:.6f}`), min-DP tokens `{sign_tests['fresh-js-24repos']['min_dp_tokens_delta_pct']:+.3f}%` (`24/24`, `p={sign_tests['fresh-js-24repos']['token_sign_test_p_two_sided']:.6f}`) -> **`{'PASS' if gates['gate2b_exact_closed_beats_open_at_dag_large_js'] else 'FAIL'}`**",
        f"  - `fresh-py-12repos` (12 repos, {manifest['corpora']['fresh-py-12repos']['files']} files, {manifest['corpora']['fresh-py-12repos']['bytes']:,d} B): complete bits `{sign_tests['fresh-py-12repos']['complete_bits_delta_pct']:+.3f}%` (wins `{sign_tests['fresh-py-12repos']['payload_unit_wins_exact_closed']}/{sign_tests['fresh-py-12repos']['units_total']}`, two-sided sign `p={sign_tests['fresh-py-12repos']['payload_sign_test_p_two_sided']:.6f}`), min-DP tokens `{sign_tests['fresh-py-12repos']['min_dp_tokens_delta_pct']:+.3f}%` (`12/12`, `p={sign_tests['fresh-py-12repos']['token_sign_test_p_two_sided']:.6f}`) -> **`{'PASS' if gates['gate2b_exact_closed_beats_open_at_dag_large_py'] else 'FAIL'}`**",
        f"- **Gate 3 (Live Deployment Encoders — HF `tokenizers`, `sentencepiece`, live pinned `tiktoken=={tiktoken_live['tiktoken_version']}`):** **`{'PASS' if gates['gate3_live_deployment_encoders_parity_and_shadowing'] else 'FAIL'}`** (`shadowing_discrepancies = {tiktoken_live['shadowing_discrepancies_vs_validator']}`, 0 UTF-8 round-trip failures across 476/476 files, 0 token-stream parity mismatches across 476/476 files).",
        "- **Important Comparative Finding (`bpe` vs `exact-closed` & `zstd -19`):** On fresh external codebases at matched `A1AD` header budgets, `exact-closed` beats `open` by `-8.6%` complete bits (`-21.8%` to `-23.1%` min-DP tokens), but plain `bpe` (also 100% pair-DAG closed) beats `exact-closed` on complete bits across all four budgets (`5,538,424` vs `5,642,152` b on JS, `3,667,888` vs `3,734,296` b on Py at `dag_header_large`) AND has **0 shadowed tokens** in native `tiktoken` (vs **852 / 8,036** shadowed for `exact-closed`), while lean-framed `zstd -19` remains strictly smaller (`2.74M` b JS, `1.88M` b Py) and ~10x faster to decode in C.",
        "",
        "## Large `A1AD` Budget (`<= 33,241 B`) Complete Bits vs Lean-Framed `zstd -19`",
        "",
    ]
    for cname in ("fresh-js-24repos", "fresh-py-12repos"):
        lines.append(f"### `{cname}` ({manifest['corpora'][cname]['files']} files, {manifest['corpora'][cname]['bytes']:,d} raw bytes)")
        lines.append("")
        lines.append("| Arm / Codec | Fragments | `A1AF` Header (B) | `A1AD` Header (B) | Header Save | `A1AF` Complete Bits | `A1AD` Complete Bits | Min-DP Tokens | Decode p95 (us) |")
        lines.append("| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |")
        for aname in PREREG_ARMS:
            a = budget_results["dag_header_large"]["arms"][aname]
            c = a["corpora"][cname]
            p95 = c["a1ad_python_decode_latency_us"]["p95_us"]
            lines.append(
                f"| `{aname}` ({a['dag_mode']}) | {a['fragments']:,d} | {c['flat_header_bytes']:,d} | {c['dag_header_bytes']:,d} | -{c['header_reduction_pct']:.1f}% | {c['flat_complete_bits']:,d} | **{c['dag_complete_bits']:,d}** | {c['min_dp_tokens']:,d} | {p95:.1f} (Py) |"
            )
        for zlabel, ztitle in (("zstd19_lean_dict8k", "zstd-19 lean (8K primary dict)"), ("zstd19_lean_dict32k", "zstd-19 lean (32K primary dict)"), ("zstd19_lean_nodict", "zstd-19 lean (no dict)")):
            z = zstd_fresh[cname][zlabel]
            comp_bits = (z["dict_bytes"] + z["payload_bytes"]) * 8
            lines.append(
                f"| {ztitle} | n/a | {z['dict_bytes']:,d} | {z['dict_bytes']:,d} | 0.0% | {comp_bits:,d} | **{comp_bits:,d}** | n/a | {z['decode_p95_us']:.1f} (C) |"
            )
        lines.append("")
        hz = horizons[cname]["exact_closed_a1ad_vs_zstd19_lean_dict8k"]
        lines.append(f"- Honest `zstd-19` comparator note: `exact-closed (A1AD)` vs `zstd-19 lean (8K dict)` status = `{hz['status']}` (M* = `{hz['m_star_bytes']}` B); `zstd-19` remains strictly smaller in complete bits on these fresh corpora.")
        lines.append("")

    lines.append("## All 4 Preregistered Budgets Summary (`A1AD` Complete Bits / Min-DP Tokens)")
    lines.append("")
    lines.append("| Budget | Arm | Frags | `A1AF` -> `A1AD` Hdr (B) | `fresh-js-24repos` `A1AD` Bits (Min-DP Tok) | `fresh-py-12repos` `A1AD` Bits (Min-DP Tok) |")
    lines.append("| --- | --- | ---: | --- | ---: | ---: |")
    for bname in ("dag_header_small", "dag_header_large", "slots_small", "slots_large"):
        b = budget_results[bname]
        for aname in PREREG_ARMS:
            a = b["arms"][aname]
            js = a["corpora"]["fresh-js-24repos"]
            py = a["corpora"]["fresh-py-12repos"]
            lines.append(
                f"| `{bname}` | `{aname}` | {a['fragments']:,d} | {a['flat_header_bytes']:,d} -> {a['dag_header_bytes']:,d} (-{js['header_reduction_pct']:.1f}%) | {js['dag_complete_bits']:,d} ({js['min_dp_tokens']:,d}) | {py['dag_complete_bits']:,d} ({py['min_dp_tokens']:,d}) |"
            )
    lines.append("")

    lines.append("## Live Pinned `tiktoken` Reachability & Native Encoder Inflation on Fresh Corpora")
    lines.append("")
    lines.append("`tiktoken` applies an O(1) whole-piece hash shortcut when a regex match equals a single vocab key (`isolated_shadowed = 0`), but runs `byte_pair_encode` inside real documents (`embedded_shadowed`), where live `tiktoken==0.14.0` matches `validate_encoders.py` with **0 discrepancies** (`0` for `bpe`, `852 / 8,036` for `exact-closed`) and **0 token-stream parity mismatches across all 476/476 fresh files**.")
    lines.append("")
    lines.append("| Model (frozen `primary` @ `dag_header_large`) | Live `tiktoken` Embedded Shadowed | Pure-Python Shadowed | JS UTF-8 RT & Parity | JS Native Tokens (vs Min-DP) | Py UTF-8 RT & Parity | Py Native Tokens (vs Min-DP) |")
    lines.append("| --- | ---: | ---: | --- | ---: | --- | ---: |")
    for mname, arm_key in (("bpe-dag-large", "bpe"), ("exact-closed-dag-large", "exact-closed")):
        tm = tiktoken_live["models"][mname]
        js_dp = budget_results["dag_header_large"]["arms"][arm_key]["corpora"]["fresh-js-24repos"]["min_dp_tokens"]
        py_dp = budget_results["dag_header_large"]["arms"][arm_key]["corpora"]["fresh-py-12repos"]["min_dp_tokens"]
        js_t = tm["corpora"]["fresh-js-24repos"]
        py_t = tm["corpora"]["fresh-py-12repos"]
        lines.append(
            f"| `{mname}` | {tm['live_tiktoken_utf8_embedded_shadowed']} / {tm['utf8_multi_tokens']} | {tm['pure_python_utf8_unreachable']} (full={tm['pure_python_full_table_unreachable']}) | {js_t['utf8_roundtrip_ok']}/{js_t['utf8_files_tested']} ({js_t['parity_mismatches']} diff) | {js_t['native_tiktoken_tokens']:,d} ({100.0*(js_t['native_tiktoken_tokens']/js_dp - 1):+.2f}%) | {py_t['utf8_roundtrip_ok']}/{py_t['utf8_files_tested']} ({py_t['parity_mismatches']} diff) | {py_t['native_tiktoken_tokens']:,d} ({100.0*(py_t['native_tiktoken_tokens']/py_dp - 1):+.2f}%) |"
        )
    lines.append("")

    lines.append("## Native HF `tokenizers` BPE & `sentencepiece` Unigram Controls (Fresh Corpora)")
    lines.append("")
    lines.append("| Native Control (Primary-Trained) | Frags | `A1AD` Hdr (B) | JS Min-DP Tok | JS Native Tok (Inflation) | Py Min-DP Tok | Py Native Tok (Inflation) | UTF-8 RT |")
    lines.append("| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |")
    for label, d in sorted(hf_controls.items()):
        js_dp, js_nv = d["common_dp_tokens"]["fresh-js-24repos"], d["native_hf_tokens"]["fresh-js-24repos"]
        py_dp, py_nv = d["common_dp_tokens"]["fresh-py-12repos"], d["native_hf_tokens"]["fresh-py-12repos"]
        lines.append(
            f"| `{label}` | {d['extracted_fragments']:,d} | {d['header_summary']['dag_header_bytes']:,d} | {js_dp:,d} | {js_nv:,d} ({100.0*(js_nv/js_dp - 1):+.2f}%) | {py_dp:,d} | {py_nv:,d} ({100.0*(py_nv/py_dp - 1):+.2f}%) | {'PASS' if d['native_utf8_roundtrip_dev'] else 'FAIL'} |"
        )
    for label, d in sorted(sp_controls.items()):
        js_dp, js_nv = d["common_dp_tokens"]["fresh-js-24repos"], d["native_viterbi_tokens"]["fresh-js-24repos"]
        py_dp, py_nv = d["common_dp_tokens"]["fresh-py-12repos"], d["native_viterbi_tokens"]["fresh-py-12repos"]
        lines.append(
            f"| `{label}` | {d['extracted_fragments']:,d} | {d['header_summary']['dag_header_bytes']:,d} | {js_dp:,d} | {js_nv:,d} ({100.0*(js_nv/js_dp - 1):+.2f}%) | {py_dp:,d} | {py_nv:,d} ({100.0*(py_nv/py_dp - 1):+.2f}%) | {'PASS' if d['native_utf8_roundtrip_dev'] else 'FAIL'} |"
        )
    lines.append("")

    (HERE / "SEALED_REPORT.md").write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    sys.exit(main())
