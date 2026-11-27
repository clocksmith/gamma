"""Score the frozen A1a arms on a hash-pinned JS manifest or a spent fixture."""

import argparse
from collections import defaultdict
from concurrent.futures import ProcessPoolExecutor
import hashlib
import json
import math
from pathlib import Path
import subprocess
import tempfile
import time

import a1a_fit as fit
from a1a_fit import E, H
from a1a_native import native_chain, pretrained_controls, validate_reference
import independent_decode as decoder

TABLES_SHA = "e73b89ec503d2a03f73292deeb9d01fe84135733de07a513c1c020f7922634ac"


def sha(data):
    return hashlib.sha256(data).hexdigest()


def require(ok, msg):
    if not ok:
        raise ValueError(msg)


def sign(diffs):
    wins, losses = sum(x > 0 for x in diffs), sum(x < 0 for x in diffs)
    n = wins + losses
    prob = min(
        1.0, 2 * sum(math.comb(n, i) for i in range(min(wins, losses) + 1)) / 2**n
    )
    return {
        "wins": wins,
        "losses": losses,
        "ties": len(diffs) - n,
        "p_two_sided": prob,
        "positive_pass": wins > losses and prob < 0.05,
    }


def score_cell(job):
    arm, n, lengths, docs, groups = job
    chain = E.parse_chain_file(fit.CHAINS[arm])
    entries = chain["entries"][:n]
    dag = H.build_dag_spec(entries, explicit_pairs=chain["explicit_pairs"] or None)
    dictionary = H.Dictionary(dag.emitted_entries)
    parsings, per_file = [], []
    for raw in docs:
        edges = dictionary.edges(raw)
        parsings.append(H.parse_bits(edges, lengths, dictionary.ESC)[0])
        per_file.append(
            {
                "min_dp": len(H.parse_tokens(edges)),
                "ac_lmm": E.longest_match_tokens(entries, [raw]),
            }
        )
    native = native_chain(arm, chain, entries, docs)
    for counts, enc in zip(per_file, native["files"], strict=True):
        counts.update(enc)
        for key in ("hf_tokens", "tiktoken_tokens", "ac_lmm"):
            if key in counts and counts["min_dp"]:
                counts[key + "_over_dp"] = counts[key] / counts["min_dp"]
    stats = {}
    for lineage, indices in groups.items():
        sources = [docs[i] for i in indices]
        result = H.serialize_dual_archives(
            dag, lengths, sources, [parsings[i] for i in indices]
        )
        row = {
            k: result[k]
            for k in (
                "emitted_entries",
                "dag_mode",
                "dag_nodes",
                "table_bytes",
                "payload_bytes",
                "flat_header_bytes",
                "dag_header_bytes",
                "flat_complete_bytes",
                "dag_complete_bytes",
                "flat_complete_bits",
                "dag_complete_bits",
                "flat_random_access_bytes",
                "dag_random_access_bytes",
            )
        }
        body = []
        for kind in ("flat", "dag"):
            blob = result[kind + "_archive"]
            out = decoder.decode_archive(blob, measure_per_file_ns=True)
            require(out["files"] == sources, f"{arm} {lineage} {kind} byte mismatch")
            require(out["padding_bits"] < 8, "invalid padding")
            body.append(blob[out["payload_offset"] :])
            lat = sorted(t / 1000 for t in out["per_file_decode_ns"])
            row[kind + "_decode_us"] = {
                f"p{p}": lat[int((len(lat) - 1) * p / 100)] for p in (50, 95, 99)
            }
            row[kind + "_sha256"] = sha(blob)
            row[kind + "_ra_bits"] = 8 * result[kind + "_random_access_bytes"]
        require(body[0] == body[1], "header-only change altered payload")
        row.update(
            payload_sha256=sha(body[0]),
            source_bytes=sum(map(len, sources)),
            files=len(indices),
            min_dp=sum(per_file[i]["min_dp"] for i in indices),
            ac_lmm=sum(per_file[i]["ac_lmm"] for i in indices),
            header_strict_win=row["dag_complete_bytes"] < row["flat_complete_bytes"],
        )
        row["dag_vs_flat_horizon"] = horizon(row, row, "dag", "flat")
        stats[lineage] = row
    return f"{arm}@{n}", {
        "groups": stats,
        "files": per_file,
        "reachability": native["reachability"],
    }


def horizon(a, b, x, y):
    return E.compute_breakeven_horizon(
        a[x + "_header_bytes"],
        a[x + "_complete_bytes"] - a[x + "_header_bytes"],
        b[y + "_header_bytes"],
        b[y + "_complete_bytes"] - b[y + "_header_bytes"],
        a["source_bytes"],
        a["files"],
    )


def zstd_rows(paths, groups):
    out = {}
    with tempfile.TemporaryDirectory() as td:
        bin_path = Path(td) / "zstd"
        subprocess.run(
            [
                "cc",
                "-O3",
                "-I/opt/homebrew/include",
                "-L/opt/homebrew/lib",
                "-Wl,-rpath,/opt/homebrew/lib",
                str(fit.A1 / "zstd_bench.c"),
                "-lzstd",
                "-o",
                str(bin_path),
            ],
            check=True,
        )
        for group, ix in groups.items():
            listing = Path(td) / "files.txt"
            listing.write_text("".join(str(paths[i]) + "\n" for i in ix))
            out[group] = {}
            for key, dictionary in {"none": "none", **fit.DICTS}.items():
                run = subprocess.check_output(
                    [str(bin_path), "19", "1", str(dictionary), "40", str(listing)]
                )
                out[group][key] = json.loads(run)
    return out


def score(files, paths, tables, jobs):
    groups = defaultdict(list)
    docs = []
    for i, (row, path) in enumerate(zip(files, paths, strict=True)):
        data = path.read_bytes()
        require(sha(data) == row["sha256"], f"source hash differs: {row['path']}")
        docs.append(data)
        require(row["lineage"] != "@pooled", "reserved lineage")
        groups[row["lineage"]].append(i)
    require(len(groups) > 0 and sum(map(len, docs)) > 0, "empty manifest")
    groups["@pooled"] = list(range(len(docs)))
    cells = fit.cells()
    specs = {(a, n) for by_arm in cells.values() for a, n in by_arm.items()}
    tasks = [
        (a, n, bytes.fromhex(tables[f"{a}@{n}"]), docs, groups)
        for a, n in sorted(specs)
    ]
    with ProcessPoolExecutor(max_workers=jobs) as pool:
        records = dict(pool.map(score_cell, tasks))
    zstd = zstd_rows(paths, groups)
    comparisons = {}
    all_header = True
    native_ok = True
    for key, record in records.items():
        native_ok &= record["reachability"]["mismatch_count"] == 0
        for file in record["files"]:
            native_ok &= all(
                v for k, v in file.items() if k.endswith(("_roundtrip", "_parity"))
            )
        for g, row in record["groups"].items():
            all_header &= row["header_strict_win"]
            baseline = zstd[g]["8k"]
            row["dag_vs_zstd8k_horizon"] = E.compute_breakeven_horizon(
                row["dag_header_bytes"],
                row["dag_complete_bytes"] - row["dag_header_bytes"],
                baseline["dict_bytes"],
                baseline["payload_bytes"],
                row["source_bytes"],
                row["files"],
            )
            row["dag_minus_zstd8k_bytes"] = (
                row["dag_complete_bytes"] - baseline["complete_bytes"]
            )
    for b, sizes in cells.items():
        closed = records[f"exact-closed@{sizes['exact-closed']}"]["groups"]
        comparisons[b] = {}
        for arm in ("open", "open-byte"):
            base = records[f"{arm}@{sizes[arm]}"]["groups"]
            differences = {
                g: {
                    "bytes_saved": r["dag_complete_bytes"]
                    - closed[g]["dag_complete_bytes"],
                    "tokens_saved": r["min_dp"] - closed[g]["min_dp"],
                    "horizon": horizon(closed[g], r, "dag", "dag"),
                }
                for g, r in base.items()
            }
            comparisons[b][arm] = {
                "groups": differences,
                "sign": {
                    k: sign([r[k] for g, r in differences.items() if g != "@pooled"])
                    for k in ("bytes_saved", "tokens_saved")
                },
            }
    singles = sorted({bytes([x]) for d in E.load_corpus("primary")[0] for x in d})
    stock = pretrained_controls(docs, singles)
    for name, rows in stock.items():
        for row in rows:
            if row.get("valid_utf8") and row["dp"]:
                row["native_over_dp"] = row["native"] / row["dp"]
    hf_stock_ok = all(
        r["roundtrip"] and r["parity"]
        for k, rs in stock.items()
        if k.startswith("hf_")
        for r in rs
        if r["valid_utf8"]
    )
    unigram_rt = all(
        r["roundtrip"]
        for k, rs in stock.items()
        if k.startswith("unigram")
        for r in rs
        if r["valid_utf8"]
    )
    primary = comparisons["dag_header_large"]["open"]
    positive_closed = all(v["positive_pass"] for v in primary["sign"].values()) and all(
        primary["groups"]["@pooled"][k] > 0 for k in ("bytes_saved", "tokens_saved")
    )
    return {
        "cells": cells,
        "cell_records": records,
        "stock_controls": stock,
        "zstd": zstd,
        "comparisons": comparisons,
        "gates": {
            "both_header_decodes_all_byte_exact": True,
            "all_identical_payloads": True,
            "headers_strictly_smaller": bool(all_header),
            "closed_large_outperforms_open": positive_closed,
            "native_hf_tiktoken_parity_roundtrip_reachability": bool(
                native_ok and hf_stock_ok
            ),
            "unigram_native_utf8_roundtrip": unigram_rt,
        },
    }


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--tables", type=Path, required=True)
    group = p.add_mutually_exclusive_group(required=True)
    group.add_argument("--manifest", type=Path)
    group.add_argument("--spent-fixture", action="store_true")
    p.add_argument("--root", type=Path)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--jobs", type=int, default=3)
    args = p.parse_args()
    start = time.monotonic()
    cache = args.tables.read_bytes()
    require(sha(cache) == TABLES_SHA, "primary-only frozen lengths differ")
    snapshot = json.loads(cache)
    require(snapshot["inputs_sha256"] == fit.hashes(), "frozen artifacts differ")
    versions = validate_reference()
    if args.spent_fixture:
        _, paths = E.load_corpus("dev")
        paths = paths[:3]
        files = [
            dict(lineage=f"spent-fixture-{i}", path=p.name, sha256=sha(p.read_bytes()))
            for i, p in enumerate(paths)
        ]
        manifest_sha = None
    else:
        require(args.root is not None, "manifest needs corpus root")
        raw = args.manifest.read_bytes()
        manifest_sha = sha(raw)
        files = json.loads(raw)["files"]
        require(len({f["path"] for f in files}) == len(files), "duplicate paths")
        paths = []
        for f in files:
            rel = Path(f["path"])
            path = (args.root / rel).resolve()
            require(
                not rel.is_absolute() and path.is_relative_to(args.root.resolve()),
                "manifest path leaves root",
            )
            paths.append(path)
    receipt = score(files, paths, snapshot["tables"], args.jobs)
    receipt.update(
        schema="bits.a1a.frozen-transfer/1",
        mode="spent-fixture" if args.spent_fixture else "sealed",
        source_files=files,
        manifest_sha256=manifest_sha,
        primary_snapshot_sha256=TABLES_SHA,
        dependency_versions=versions,
        negative_controls=snapshot["negative_controls"],
        parallel_workers=args.jobs,
        work_seconds=time.monotonic() - start,
    )
    args.output.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")


if __name__ == "__main__":
    main()
