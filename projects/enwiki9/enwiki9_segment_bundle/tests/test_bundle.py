from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
PROGRAM = ROOT / "enwiki9_bundle.py"

CODEC = r'''#!/usr/bin/env python3
import sys, zlib
from pathlib import Path
op, src, dst = sys.argv[1], Path(sys.argv[2]), Path(sys.argv[3])
if op == "compress":
    dst.write_bytes(zlib.compress(src.read_bytes(), 9))
elif op == "decompress":
    dst.write_bytes(zlib.decompress(src.read_bytes()))
else:
    raise SystemExit(2)
'''


def run(*args: str, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(PROGRAM), *args],
        cwd=cwd,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=True,
    )


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_end_to_end() -> None:
    with tempfile.TemporaryDirectory() as name:
        temp = Path(name)
        packages = []
        for index in range(5):
            source = temp / f"codec-{index}"
            source.mkdir()
            (source / "codec.py").write_text(CODEC, encoding="utf-8")
            (source / "codec.json").write_text(
                json.dumps(
                    {
                        "schema": "enwiki9_segment_codec/v1",
                        "codec_id": f"test-codec-{index}",
                        "segment_index": index,
                        "prepare": [],
                        "compress": ["python3", "codec.py", "compress", "{input}", "{output}"],
                        "decompress": ["python3", "codec.py", "decompress", "{input}", "{output}"],
                        "environment": {},
                    },
                    sort_keys=True,
                ),
                encoding="utf-8",
            )
            package = temp / f"codec-{index}.zip"
            run("pack-directory", "--source", str(source), "--output", str(package))
            packages.append(package)

        outer_source = temp / "outer"
        outer_source.mkdir()
        (outer_source / "enwiki9_bundle.py").write_bytes(PROGRAM.read_bytes())
        outer = temp / "outer.zip"
        run("pack-directory", "--source", str(outer_source), "--output", str(outer))

        raw_size = 5 * 10_000
        raw = bytes((i * 31 + (i >> 3)) & 255 for i in range(raw_size))
        input_path = temp / "input.raw"
        input_path.write_bytes(raw)

        manifest = {
            "schema": "enwiki9_segment_bundle/v1",
            "profile": "test-5x10k-v1",
            "raw_size": raw_size,
            "segment_size": 10_000,
            "segment_count": 5,
            "segment_budget_bytes": 100_000,
            "outer_budget_bytes": 100_000,
            "target_bytes": 1_000_000,
            "outer_package": {
                "path": outer.name,
                "bytes": outer.stat().st_size,
                "sha256": sha(outer),
            },
            "segments": [
                {
                    "index": i,
                    "codec_id": f"test-codec-{i}",
                    "package": {
                        "path": packages[i].name,
                        "bytes": packages[i].stat().st_size,
                        "sha256": sha(packages[i]),
                    },
                }
                for i in range(5)
            ],
        }
        manifest_path = temp / "manifest.json"
        manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")

        archive = temp / "archive.ew9"
        certificate = temp / "certificate.json"
        run(
            "certify",
            "--manifest",
            str(manifest_path),
            "--input",
            str(input_path),
            "--archive",
            str(archive),
            "--certificate",
            str(certificate),
        )
        restored = temp / "restored.raw"
        run(
            "decompress",
            "--manifest",
            str(manifest_path),
            "--archive",
            str(archive),
            "--output",
            str(restored),
        )
        assert restored.read_bytes() == raw
        cert = json.loads(certificate.read_text("utf-8"))
        assert cert["proof"]["full_roundtrip"] is True
        assert cert["score"]["overall_pass"] is True


if __name__ == "__main__":
    test_end_to_end()
    print("ok")
