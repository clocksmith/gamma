"""fx2 schema-template-only sidecar ablation.

The byte stream is unchanged. The bundled cmix/fx2 binary was built from
external/cmix21-sidecar with SIDECAR_SCHEMA_TEMPLATE_ONLY, routing exactly one
decoder-recomputed context family into the predictor:

  (template_hash << 16) ^ ((template_arg & 15) << 8) ^ (slot & 15)
"""

from __future__ import annotations

import gzip
import os
import pathlib
import resource
import stat
import subprocess
import tempfile

_DIR = pathlib.Path(__file__).resolve().parent
_BIN_GZ = _DIR / "cmix.bin.gz"
_DICT_GZ = _DIR / "english.dic.gz"
_extracted_bin: pathlib.Path | None = None
_extracted_dict: pathlib.Path | None = None


def _extract(src: pathlib.Path, prefix: str, executable: bool) -> pathlib.Path:
    fd, path = tempfile.mkstemp(prefix=prefix)
    os.close(fd)
    out = pathlib.Path(path)
    with gzip.open(src, "rb") as inp:
        out.write_bytes(inp.read())
    if executable:
        out.chmod(out.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    return out


def _binary() -> pathlib.Path:
    global _extracted_bin
    if _extracted_bin is None or not _extracted_bin.exists():
        _extracted_bin = _extract(_BIN_GZ, "fx2-schema-template-cmix-", True)
    return _extracted_bin


def _dictionary() -> pathlib.Path:
    global _extracted_dict
    if _extracted_dict is None or not _extracted_dict.exists():
        _extracted_dict = _extract(_DICT_GZ, "fx2-schema-template-dict-", False)
    return _extracted_dict


def _limit_child() -> None:
    limit = os.environ.get("FX2_SC_AS_LIMIT_BYTES")
    if not limit:
        return
    bytes_limit = int(limit)
    resource.setrlimit(resource.RLIMIT_AS, (bytes_limit, bytes_limit))


def _run(flag: str, data: bytes) -> bytes:
    with tempfile.TemporaryDirectory() as td:
        src = os.path.join(td, "in")
        dst = os.path.join(td, "out")
        with open(src, "wb") as f:
            f.write(data)
        subprocess.run(
            [str(_binary()), flag, str(_dictionary()), src, dst],
            cwd=td,
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            preexec_fn=_limit_child,
        )
        with open(dst, "rb") as f:
            return f.read()


def compress(data: bytes) -> bytes:
    return _run("-c", data)


def decompress(data: bytes) -> bytes:
    return _run("-d", data)
