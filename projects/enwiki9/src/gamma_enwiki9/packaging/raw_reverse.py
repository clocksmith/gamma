"""Standalone delivery of the existing raw-reversal BZip2 format."""
from pathlib import Path
from gamma_enwiki9.evidence.artifacts import canonical_bytes, fingerprint, publish_immutable_artifact


CLI = '''from pathlib import Path
import argparse
import json
from raw_reverse_bz2 import encode, decode, MAX_RAW, MAX_ARCHIVE, MAX_BLOCK

parser = argparse.ArgumentParser()
parser.add_argument("operation", choices=("encode", "decode"))
parser.add_argument("input", type=Path)
parser.add_argument("output", type=Path)
parser.add_argument("--mode", choices=("P", "K", "D"), default="D")
parser.add_argument("--block-size", type=int, default=MAX_BLOCK)
args = parser.parse_args()
bound = MAX_RAW if args.operation == "encode" else MAX_ARCHIVE
with args.input.open("rb") as stream:
    raw = stream.read(bound + 1)
if len(raw) > bound:
    raise ValueError("file input bound")
output, report = encode(raw, args.mode, args.block_size) if args.operation == "encode" else decode(raw)
with args.output.open("xb") as stream:
    stream.write(output)
print(json.dumps(report, sort_keys=True))
'''


def build(source: Path, license_path: Path, destination: Path) -> dict:
    destination.mkdir()  # Never infer membership from a reused workspace.
    for name, raw in (("raw_reverse_bz2.py", source.read_bytes()), ("codec.py", CLI.encode()),
                      ("LICENSE", license_path.read_bytes())):
        publish_immutable_artifact(destination / name, raw)
    files = [fingerprint(destination / name, destination) for name in ("LICENSE", "codec.py", "raw_reverse_bz2.py")]
    manifest = {"schema": "gamma.enwiki9.codec-delivery.v1", "kind": "standalone_codec",
        "format": "D2REVB01", "files": files, "counted_source_bytes": sum(r["bytes"] for r in files),
        "build": [], "commands": {"compress": ["python3", "codec.py", "encode", "{input}", "{archive}"],
                                   "decompress": ["python3", "codec.py", "decode", "{archive}", "{restored}"]},
        "runtime_dependencies": ["Python >=3.11 with stdlib bz2 (including its libbz2 dependency)"],
        "required_options": [], "required_option_bytes": 0,
        "experiment_dependencies": [], "observer_dependencies": [],
        "qualification_authority": False, "full_corpus_score_bytes": None}
    publish_immutable_artifact(destination / "delivery.json", canonical_bytes(manifest) + b"\n")
    return manifest
