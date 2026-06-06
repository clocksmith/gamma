"""fx2cmix_wrapped_v1 — score-honest wrapper around the fx2-cmix engine.

Everything required to decompress lives in this directory and is counted by
the driver: `cmix` (the fx2-cmix binary, the Oct-2024 Hutter Prize winner) and
`english.dic` (its pretraining dictionary). compress/decompress shell out to
the binary inside an isolated temp directory (cmix writes a `ppm.temp` scratch
file to its working directory).

Provenance: binary from this repo's external/fx2-cmix/ (built with the project
makefile, UPX-packed). Cross-microarchitecture portability is NOT guaranteed
if it was built with -march=native; for a contest submission rebuild with a
portable target or vendor the source and compile at decode time.
"""

from __future__ import annotations

import os
import pathlib
import subprocess
import tempfile

_HERE = pathlib.Path(__file__).resolve().parent
_BIN = _HERE / "cmix"
_DICT = _HERE / "english.dic"


def _run(args: list[str], cwd: str) -> None:
    subprocess.run(
        args,
        cwd=cwd,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=True,
    )


def compress(data: bytes) -> bytes:
    os.chmod(_BIN, 0o755)
    with tempfile.TemporaryDirectory() as d:
        src = os.path.join(d, "in")
        dst = os.path.join(d, "out")
        with open(src, "wb") as f:
            f.write(data)
        _run([str(_BIN), "-c", str(_DICT), src, dst], d)
        with open(dst, "rb") as f:
            return f.read()


def decompress(blob: bytes) -> bytes:
    os.chmod(_BIN, 0o755)
    with tempfile.TemporaryDirectory() as d:
        src = os.path.join(d, "in")
        dst = os.path.join(d, "out")
        with open(src, "wb") as f:
            f.write(blob)
        _run([str(_BIN), "-d", str(_DICT), src, dst], d)
        with open(dst, "rb") as f:
            return f.read()
