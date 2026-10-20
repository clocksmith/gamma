"""Reconstruct a complete JavaScript source from a saved flat literal encoding."""
import argparse
import json
from pathlib import Path
from literals import digest, reconstruct, dictionary_bytes, program_bytes, decode_bytes


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("encoding", type=Path)
    parser.add_argument("problem", help="four-digit problem ID, e.g. 0242")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--binary-directory", type=Path)
    args = parser.parse_args()
    packet = json.loads(args.encoding.read_text())
    row = packet["programs"][args.problem]
    source = reconstruct(packet["literals"], row["sequence"])
    if digest(source.encode()) != row["source_sha256"]:
        raise ValueError("source hash mismatch")
    dictionary = dictionary_bytes(packet["literals"])
    program = program_bytes(packet["literals"], row["sequence"])
    if decode_bytes(dictionary, program) != source:
        raise ValueError("binary reconstruction mismatch")
    args.output.write_bytes(source.encode())
    if args.binary_directory:
        args.binary_directory.mkdir(parents=True, exist_ok=False)
        (args.binary_directory / "dictionary.ltd").write_bytes(dictionary)
        (args.binary_directory / f"{args.problem}.ltp").write_bytes(program)
    print(json.dumps({"source_sha256": digest(source.encode()), "selections": len(row["sequence"]),
                      "dictionary_bytes": len(dictionary), "program_bytes": len(program)}))


if __name__ == "__main__":
    main()
