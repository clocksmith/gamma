"""Apply the frozen depth-one scorer and verify raw fallbacks against Git blob bytes."""

import argparse
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
CARD = HERE.parent / "a2-recursive-frames-v1"
sys.path.insert(0, str(CARD))
import independent_decode
import score_depth1_sealed


def verify_freeze():
    protocol = (CARD / "PREREGISTRATION_DEPTH1.md").read_text()
    pins = re.findall(r"^\| [^|]+ \| `([^`]+)` \| (\d+) \| `([0-9a-f]{64})` \|$", protocol, re.M)
    if len(pins) != 13:
        raise ValueError("incomplete frozen artifact table")
    for name, size, expected in pins:
        data = (CARD / name).read_bytes()
        if len(data) != int(size) or hashlib.sha256(data).hexdigest() != expected:
            raise ValueError(f"freeze mismatch for {name}")


def run(manifest, root, out, *, fixture=False):
    verify_freeze()
    data = manifest.read_bytes()
    rows = json.loads(data)["files"]
    if not rows or len(set(r["path"] for r in rows)) != len(rows):
        raise ValueError("empty or duplicate manifest paths")
    if not fixture and len(set(r["lineage"] for r in rows)) < 20:
        raise ValueError("fewer than 20 repository lineages")
    sources = []
    for r in rows:
        path = (root / r["path"]).resolve()
        if not path.is_relative_to(root.resolve()):
            raise ValueError("source escapes manifest root")
        raw = path.read_bytes()
        if hashlib.sha256(raw).hexdigest() != r["sha256"]:
            raise ValueError(f"input hash mismatch for {r['path']}")
        sources.append(raw)
    out.mkdir(parents=True, exist_ok=True)
    audit = {"manifest_sha256": hashlib.sha256(data).hexdigest(), "files": len(rows),
             "scope": "spent fixture" if fixture else "sealed", "files_in_error": []}
    try:
        report = score_depth1_sealed.score_manifest(manifest, root, out)
        # The frozen scorer opens text with universal newlines. Independently build
        # the target from the original Git bytes, including CRLF and malformed UTF-8.
        targets = []
        for offset in range(0, len(sources), 64):
            batch = sources[offset:offset + 64]
            items = [{"id": str(i), "source": raw.decode("utf-8", errors="replace")} for i, raw in enumerate(batch)]
            proc = subprocess.run(["node", str(CARD / "js_normalize_ast.mjs"), "normalize"],
                                  input=json.dumps({"items": items}), capture_output=True, text=True, check=True)
            for i, (result, raw) in enumerate(zip(json.loads(proc.stdout)["results"], batch, strict=True)):
                if str(result["id"]) != str(i):
                    raise ValueError("normalizer reordered inputs")
                valid = items[i]["source"].encode("utf-8") == raw
                targets.append(result["normalized"].encode("utf-8") if valid and result["supported"] else raw)
        for arm in ("arm2_context_ast", "arm3_depth1_frames"):
            decoded = independent_decode.decode_archive((out / f"{arm}.a2bits").read_bytes())
            for row, original, recovered in zip(rows, targets, decoded["files"], strict=True):
                if original != recovered:
                    audit["files_in_error"].append({"path": row["path"], "arm": arm})
        audit["verdict"] = "KILL" if audit["files_in_error"] else report["complete_bits"]["verdict"]
    except Exception as exc:
        audit.update(verdict="KILL", error_type=type(exc).__name__, error=str(exc))
        raise
    finally:
        (out / "raw_fidelity.json").write_text(json.dumps(audit, indent=2) + "\n")
    return audit


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path)
    parser.add_argument("root", type=Path)
    parser.add_argument("out", type=Path)
    parser.add_argument("--spent-fixture", action="store_true")
    args = parser.parse_args()
    print(json.dumps(run(args.manifest, args.root, args.out, fixture=args.spent_fixture), indent=2))
