"""Verify frozen A1a inputs and rebuild deterministic Huffman tables on primary only."""

from concurrent.futures import ProcessPoolExecutor
from hashlib import sha256
import json
from pathlib import Path
import re
import subprocess
import sys

HERE = Path(__file__).resolve().parent
A1 = HERE.parent / "a1a-fixed-budget-v1"
sys.path.insert(0, str(A1))
import eval_dev as E
import headers as H
from test_headers import test_negative_controls

BASE = "89ac437fa3d1e3a433324cdd224384147f127293"
CHAINS = {
    "open": E.CL / "out/exact/exact-entry-s1-whole.txt",
    "open-byte": E.CL / "out/bundle/open-byte-ext.txt",
    "exact-closed": E.CL / "out/bundle/pair-ext.txt",
    "pair-byte": E.CHAINS_DIR / "pair-byte-exact-full.txt",
    "bpe": E.CHAINS_DIR / "bpe-ext.txt",
}
BUDGETS = {
    "dag_header_small": 878,
    "dag_header_large": 33241,
    "slots_small": 84,
    "slots_large": 3924,
}
DICTS = {
    "8k": E.OH / "frozen/zstd-train-8k.dict",
    "32k": A1 / "out/zstd/zstd-train-32k.dict",
}
RETAINED = A1 / "out/eval_dev.json"


def hashes():
    contract = A1 / "PREREGISTRATION_DAG_ENCODERS.md"
    recorded = dict(
        re.findall(r"\| `([\w.\-]+)` \| `([a-f0-9]{64})`", contract.read_text())
    )
    if len(recorded) != 5:
        raise ValueError("missing preregistered hashes")
    paths = [
        contract,
        RETAINED,
        E.OH / "frozen/sets/train.json",
        A1 / "eval_dev.py",
        A1 / "test_headers.py",
        A1 / "zstd_bench.c",
        *CHAINS.values(),
        *DICTS.values(),
        *(A1 / name for name in recorded),
        *sorted(E.CHAINS_DIR.glob("hf_bpe/*.json")),
        *sorted(E.CHAINS_DIR.glob("sentencepiece/*.model")),
    ]
    root = Path(
        subprocess.check_output(
            ["git", "rev-parse", "--show-toplevel"], cwd=HERE, text=True
        ).strip()
    )
    result = {}
    for path in paths:
        key = path.relative_to(root).as_posix()
        digest = sha256(path.read_bytes()).hexdigest()
        pinned = subprocess.check_output(["git", "show", BASE + ":" + key], cwd=root)
        if (
            sha256(pinned).hexdigest() != digest
            or recorded.get(path.name, digest) != digest
        ):
            raise ValueError(f"frozen source differs: {key}")
        result[key] = digest
    return result


def cells():
    receipt = json.loads(RETAINED.read_text())["budgets"]
    return {
        b: {arm: receipt[b]["arms"][arm]["total_entries"] for arm in CHAINS}
        for b in BUDGETS
    }


def fit_one(job):
    arm, n = job
    chain = E.parse_chain_file(CHAINS[arm])
    dag = H.build_dag_spec(
        chain["entries"][:n], explicit_pairs=chain["explicit_pairs"] or None
    )
    dictionary = H.Dictionary(dag.emitted_entries)
    primary = E.load_corpus("primary")[0]
    edges = [dictionary.edges(doc) for doc in primary]
    lengths, _, _, passes = H.fit_table(dictionary, edges)
    parses = [H.parse_bits(e, lengths, dictionary.ESC)[0] for e in edges]
    archive = H.serialize_dual_archives(dag, lengths, primary, parses)
    spent = json.loads(RETAINED.read_text())["budgets"]
    for b, sizes in cells().items():
        if sizes[arm] != n:
            continue
        old = spent[b]["arms"][arm]["archive"]
        if (
            archive["dag_complete_bytes"] != old["primary"]["dag_complete_bytes"]
            or passes != old["table_fit_passes"]
        ):
            raise ValueError(f"{arm}/{n} differs from original trained fit")
        if b.startswith("dag_header") and archive["dag_header_bytes"] > BUDGETS[b]:
            raise ValueError("header budget exceeded")
        if b.startswith("slots") and n - E.ALPHA != BUDGETS[b]:
            raise ValueError("slot budget mismatch")
    return f"{arm}@{n}", bytes(lengths).hex()


def prepare(path, jobs):
    inputs = hashes()
    negative = test_negative_controls()
    if len(negative) != 6:
        raise ValueError("expected six rejected corruptions")
    jobspecs = sorted({(a, n) for sizes in cells().values() for a, n in sizes.items()})
    with ProcessPoolExecutor(max_workers=jobs) as pool:
        tables = dict(pool.map(fit_one, jobspecs))
    result = {
        "base": BASE,
        "inputs_sha256": inputs,
        "negative_controls": negative,
        "tables": tables,
    }
    path.write_text(json.dumps(result, sort_keys=True) + "\n")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    parser.add_argument("--jobs", type=int, default=3)
    args = parser.parse_args()
    prepare(args.output, args.jobs)
