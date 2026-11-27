#!/usr/bin/env python3
"""Deterministic, strictly lineage-disjoint corpus split for BITS Experiment A2.

Uses ONLY already-spent local JavaScript sources inside the worktree:
  Train lineages (strictly disjoint from Dev):
    - codenet-primary (200 CodeNet JS files, grouped by IBM identical-problem cluster)
    - codenet-secondary (200 CodeNet JS files, grouped by IBM cluster)
    - guides-algo (162 qualified algorithm JS files excluding the 20 sources-20 IDs)
    - repo:ramda (200 Ramda JS files, 1 repository lineage)
  Dev lineages (strictly disjoint from Train):
    - codenet-fresh (200 CodeNet JS files, IBM-cluster-disjoint from Train)
    - codenet-fresh2 (200 CodeNet JS files, IBM-cluster-disjoint from Train & fresh)
    - sources-20 (20 algorithm JS files with 3,834 frozen Node behavior checks in checks.py)
    - repo:express (120 Express JS files, 1 repository lineage, disjoint from Ramda)
"""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
LIT = HERE.parent


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def squeezed_sha256(data: bytes) -> str:
    return hashlib.sha256(b"".join(data.split())).hexdigest()


def load_ibm_clusters() -> dict[str, str]:
    """Map each CodeNet problem ID to a canonical IBM cluster ID."""
    path = LIT / "objective-holdout-v1" / "metadata" / "ibm-identical-problem-clusters.txt"
    cluster_of = {}
    for line in path.read_text(encoding="utf-8").split():
        members = sorted(line.split(","))
        canon = members[0]
        for pid in members:
            cluster_of[pid] = canon
    return cluster_of


def build_split() -> dict:
    clusters = load_ibm_clusters()
    src20_dir = LIT / "sources" / "original"
    src20_pids = {p.stem for p in sorted(src20_dir.glob("*.js"))}

    def make_entry(path: Path, split: str, slice_name: str, lineage: str, problem_id: str | None = None) -> dict:
        raw = path.read_bytes()
        rel = str(path.relative_to(LIT))
        return {
            "id": f"{slice_name}/{path.name}",
            "rel_path": rel,
            "split": split,
            "slice": slice_name,
            "lineage": lineage,
            "problem_id": problem_id,
            "raw_bytes": len(raw),
            "raw_sha256": sha256_bytes(raw),
            "squeezed_sha256": squeezed_sha256(raw),
        }

    train_files = []
    dev_files = []

    # Train: CodeNet primary + secondary
    for slice_name, sub in [
        ("codenet-primary", LIT / "codenet-replication-v1" / "corpus" / "primary" / "javascript"),
        ("codenet-secondary", LIT / "codenet-replication-v1" / "corpus" / "secondary" / "javascript"),
    ]:
        for p in sorted(sub.glob("*.js")):
            pid = p.name.split("_")[0]
            cid = clusters.get(pid, pid)
            train_files.append(make_entry(p, "train", slice_name, f"cn:{cid}", pid))

    # Train: guides-qualified-v1 excluding any problem ID in sources-20
    guides_dir = LIT / "guides-qualified-v1" / "sources" / "javascript"
    for p in sorted(guides_dir.glob("*.js")):
        pid = p.stem.split("-")[0]
        if pid in src20_pids:
            continue
        train_files.append(make_entry(p, "train", "guides-algo", f"algo:{pid}", pid))

    # Train: Ramda repository lineage
    ramda_dir = LIT / "closure-holdout-v1" / "corpus" / "project-javascript"
    for p in sorted(ramda_dir.glob("*.js")):
        train_files.append(make_entry(p, "train", "ramda", "repo:ramda", None))

    # Dev: CodeNet fresh + fresh2
    for slice_name, sub in [
        ("codenet-fresh", LIT / "objective-holdout-v1" / "corpus" / "codenet-fresh" / "javascript"),
        ("codenet-fresh2", LIT / "closure-holdout-v1" / "corpus" / "codenet-fresh2" / "javascript"),
    ]:
        for p in sorted(sub.glob("*.js")):
            pid = p.name.split("_")[0]
            cid = clusters.get(pid, pid)
            dev_files.append(make_entry(p, "dev", slice_name, f"cn:{cid}", pid))

    # Dev: sources-20 (with frozen behavior tests in checks.py)
    for p in sorted(src20_dir.glob("*.js")):
        pid = p.stem
        dev_files.append(make_entry(p, "dev", "sources-20", f"algo:{pid}", pid))

    # Dev: Express repository lineage
    express_dir = LIT / "objective-holdout-v1" / "corpus" / "project"
    for p in sorted(express_dir.glob("*.js")):
        dev_files.append(make_entry(p, "dev", "express", "repo:express", None))

    # Strict disjointness assertions
    train_lineages = {f["lineage"] for f in train_files}
    dev_lineages = {f["lineage"] for f in dev_files}
    shared_lineages = sorted(train_lineages & dev_lineages)
    if shared_lineages:
        raise AssertionError(f"Lineage leak between train and dev: {shared_lineages[:10]}")

    train_pids = {f["problem_id"] for f in train_files if f["problem_id"] is not None}
    dev_pids = {f["problem_id"] for f in dev_files if f["problem_id"] is not None}
    shared_pids = sorted(train_pids & dev_pids)
    if shared_pids:
        raise AssertionError(f"Problem ID leak between train and dev: {shared_pids[:10]}")

    train_sq = {f["squeezed_sha256"] for f in train_files}
    dev_sq = {f["squeezed_sha256"] for f in dev_files}
    if train_sq & dev_sq:
        raise AssertionError("Duplicate source file across train and dev")

    split_doc = {
        "schema": "gamma.bits.a2.corpus_split.v1",
        "policy": "strictly_spent_local_js_lineage_disjoint",
        "counts": {
            "train_files": len(train_files),
            "train_lineages": len(train_lineages),
            "train_raw_bytes": sum(f["raw_bytes"] for f in train_files),
            "dev_files": len(dev_files),
            "dev_lineages": len(dev_lineages),
            "dev_raw_bytes": sum(f["raw_bytes"] for f in dev_files),
            "shared_lineages": 0,
            "shared_problem_ids": 0,
            "cross_split_duplicates": 0,
        },
        "train": train_files,
        "dev": dev_files,
    }
    return split_doc


def main() -> None:
    doc = build_split()
    out_path = HERE / "corpus_split.json"
    out_path.write_text(json.dumps(doc, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(doc["counts"], indent=2))


if __name__ == "__main__":
    main()
