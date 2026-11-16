#!/usr/bin/env python3
"""Check restored pilot bytes using the hash-bound original stdlib codec.

This verifies archival restoration, not historical timing, resource isolation,
new research authority or full-corpus compression. Never rewrites a receipt.
"""
import argparse
import hashlib
import json
from pathlib import Path
import types

ORIGINAL_REVISION = "88bd675cf192b70efc1a0f7cf56168b8b0104709"
PINNED_SHA256 = {
    "tools/raw_reverse_bz2_v1.py": "59612e24aa7888a66ba8eb784ca37553aee8a11d5298383712f7f011bf2311b7",
    "results/raw_reverse_bz2250k_q0_v1/artifacts.json": "5bb56a2d20f26cca52cca44ec243e4fcf6ff28ec9acd67b8f291c9e9a883a612",
    "operations/adaptive/experiments/raw_reverse_bz2250k_q0_v1.json": "b7e8f912942bd38786bf1ac83eef9a8b17c8ed5cfe1916ce5eebb078091c39d6",
    "operations/evidence/fixtures/dualstream_opening250k_v1.raw": "665fc689441b68462d88f82dc33212abe9c4824be095d03a556c9b55a2829fd3",
}


def digest(data):
    return hashlib.sha256(data).hexdigest()


def verify(project: Path, restored: Path):
    def original(relative):
        data = (project / relative).read_bytes()
        if digest(data) != PINNED_SHA256[relative]:
            raise ValueError(f"Tracked original metadata/source bytes differ: {relative}")
        return data

    experiment_bytes = original("operations/adaptive/experiments/raw_reverse_bz2250k_q0_v1.json")
    receipt_bytes = original("results/raw_reverse_bz2250k_q0_v1/artifacts.json")
    experiment = json.loads(experiment_bytes)
    receipt = json.loads(receipt_bytes)
    if receipt.get("complete") is not True:
        raise ValueError("Original artifact receipt is incomplete")
    bound = {entry["path"]: entry for entry in experiment["inputs"]}
    codec_path = project / "tools/raw_reverse_bz2_v1.py"
    codec_source = original("tools/raw_reverse_bz2_v1.py")
    codec_sha = digest(codec_source)
    if codec_sha != bound["tools/raw_reverse_bz2_v1.py"]["sha256"].removeprefix("sha256:"):
        raise ValueError("Frozen original codec source differs from its experiment binding")
    fixture_path = "operations/evidence/fixtures/dualstream_opening250k_v1.raw"
    expected_sha = bound[fixture_path]["sha256"].removeprefix("sha256:")
    population = original(fixture_path)
    if digest(population) != expected_sha:
        raise ValueError("Original indispensable population fixture differs")
    codec = types.ModuleType("original_raw_reverse_restore_codec")
    codec.__file__ = str(codec_path)
    exec(compile(codec_source, str(codec_path), "exec"), codec.__dict__)
    indexed = {entry["path"]: entry for entry in receipt["files"]}
    checked, archives = [], {}
    for arm in ("P", "K", "D"):
        for suffix in ("raw", "rbz", "repeat.rbz"):
            path = f"results/raw_reverse_bz2250k_q0_v1/{arm}.{suffix}"
            data = (restored / "projects/enwiki9" / path).read_bytes()
            expected = indexed[path]
            if len(data) != expected["bytes"] or digest(data) != expected["sha256"]:
                raise ValueError(f"Restored artifact bytes differ: {path}")
            if suffix == "raw":
                if data != population:
                    raise ValueError(f"Restored raw differs from original fixture: {path}")
            else:
                raw, _ = codec.decode(data)
                if raw != population:
                    raise ValueError(f"Original decoder inverse differs: {path}")
                repeated, _ = codec.encode(raw, mode=arm)
                if repeated != data:
                    raise ValueError(f"Original encoder bytes differ: {path}")
                archives[arm, suffix] = data
            checked.append(dict(path="projects/enwiki9/" + path, bytes=len(data), sha256=digest(data)))
    if archives["P", "rbz"] != archives["K", "rbz"]:
        raise ValueError("Original P/K identity differs")
    for arm in ("P", "K", "D"):
        if archives[arm, "rbz"] != archives[arm, "repeat.rbz"]:
            raise ValueError(f"Original repeat differs for {arm}")
    return dict(schema="gamma.enwiki9.raw-reverse-restoration-check/v1", verified=True,
                original_source_revision=ORIGINAL_REVISION, source_codec_sha256=codec_sha,
                original_receipt_sha256=digest(receipt_bytes), original_experiment_sha256=digest(experiment_bytes),
                population_sha256=expected_sha, restored_files=checked,
                original_decoder_inverses=6, original_encoder_repeats=6,
                historical_timing_reproduced=False, new_research_authorized=False)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--restored-root", type=Path, required=True, help="Restoration root containing original projects/enwiki9/... paths")
    args = parser.parse_args()
    print(json.dumps(verify(args.project_root, args.restored_root), indent=2))


if __name__ == "__main__":
    main()
