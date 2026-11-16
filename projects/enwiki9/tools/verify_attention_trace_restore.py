#!/usr/bin/env python3
"""Recheck restored recorded streams with the original CPU comparison only.

No Git, network, native build, encoder, training or model execution is needed.
All original metadata/source files must match the candidate's pinned identities.
"""
import argparse
import ast
import hashlib
import json
from pathlib import Path
import struct


def sha(path):
    result = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            result.update(block)
    return result.hexdigest()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def original_comparison(source: bytes, name: str, rows: int):
    """Extract just the hash-bound comparison function; never import its driver."""
    syntax = ast.parse(source, filename=name)
    selected = [node for node in syntax.body if isinstance(node, ast.FunctionDef) and node.name == "neural_compare"]
    require(len(selected) == 1, "Original comparison function absent or ambiguous")
    declared_rows = [node.value.value for node in syntax.body if isinstance(node, ast.Assign)
                     and any(isinstance(target, ast.Name) and target.id == "N" for target in node.targets)]
    require(declared_rows == [rows], "Original row-count declaration differs")
    module = ast.Module(body=selected, type_ignores=[])
    namespace = dict(struct=struct, require=require, sha=sha, N=rows)
    exec(compile(module, name, "exec"), namespace)
    return namespace["neural_compare"]


def verify(candidate: dict, source_root: Path, restored_root: Path):
    require(len(candidate.get("families", [])) == 2 and
            {family["family"] for family in candidate["families"]} ==
            {"fx2_attention_anchor250k_v1", "fx2_attention_anchor250k_v2"},
            "Candidate must contain both reviewed trace families")
    results = []
    for family in candidate["families"]:
        require(len(family["files"]) == 8 and family["row_count"] == 151210,
                "Candidate trace population is incomplete")
        bindings = {entry["path"]: entry for entry in family["bindings"]}
        for path, entry in bindings.items():
            actual = source_root / path
            require(actual.stat().st_size == entry["bytes"] and sha(actual) == entry["sha256"],
                    f"Original metadata/source bytes differ: {path}")
        for entry in family["files"]:
            actual = restored_root / entry["path"]
            require(actual.stat().st_size == entry["bytes"] and sha(actual) == entry["expected_sha256"],
                    f"Restored trace bytes differ: {entry['path']}")
        expected = json.loads((source_root / family["comparison_receipt"]).read_bytes())
        starts = json.loads((source_root / family["validity_input"]).read_bytes())["missing_feature_byte_coordinates"]
        compare = original_comparison((source_root / family["producer"]).read_bytes(),
                                      family["producer"], family["row_count"])
        base = restored_root / f"projects/enwiki9/results/{family['family']}/work/native"
        observed = {}
        for arm in "KDS":
            observed[arm] = compare(base / "P-encode.probs", base / f"{arm}-encode.probs", starts)
            require(observed[arm] == expected[arm], f"Recorded neural comparison differs: {family['family']}/{arm}")
        # Exact recorded hashes establish each encode/repeat identity too.
        identities = {Path(entry["path"]).name: entry["expected_sha256"] for entry in family["files"]}
        require(identities["P-encode.probs"] == identities["K-encode.probs"], "P/K identity differs")
        for arm in "PKDS":
            require(identities[f"{arm}-encode.probs"] == identities[f"{arm}-repeat.probs"], "Repeat identity differs")
        results.append(dict(family=family["family"], verified=True, restored_files=len(family["files"]),
                            rows=family["row_count"], original_comparison=observed))
    return dict(schema="gamma.enwiki9.attention-trace-restoration-check/v1", verified=True,
                families=results, model_executed=False, historical_execution_reproduced=False,
                scientific_verdicts_modified=False)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidate", type=Path, default=Path(__file__).resolve().parents[1] /
                        "docs/archive-maintenance/attention-trace-candidate.json")
    parser.add_argument("--source-root", type=Path, default=Path(__file__).resolve().parents[3],
                        help="Root containing the kept original projects/enwiki9 metadata/source paths")
    parser.add_argument("--restored-root", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(verify(json.loads(args.candidate.read_bytes()), args.source_root, args.restored_root), indent=2))


if __name__ == "__main__":
    main()
