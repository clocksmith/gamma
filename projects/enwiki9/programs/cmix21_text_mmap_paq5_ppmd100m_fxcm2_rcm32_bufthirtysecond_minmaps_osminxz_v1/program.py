from __future__ import annotations

import lzma
import os
import pathlib
import subprocess
import tempfile

D = pathlib.Path(__file__).resolve().parent
BIN = D / "cmix.bin.xz"
DIC = D / "english.dic.xz"
_bin = None
_dic = None


def _extract(path, prefix, exe=False):
    fd, name = tempfile.mkstemp(prefix=prefix)
    os.close(fd)
    out = pathlib.Path(name)
    out.write_bytes(lzma.decompress(path.read_bytes()))
    if exe:
        out.chmod(out.stat().st_mode | 0o111)
    return out


def _binary():
    global _bin
    if _bin is None or not _bin.exists():
        _bin = _extract(BIN, "cmix21-mmap-bin-", True)
    return _bin


def _dictionary():
    global _dic
    if _dic is None or not _dic.exists():
        _dic = _extract(DIC, "cmix21-mmap-dict-")
    return _dic


def _run(args, data):
    with tempfile.TemporaryDirectory() as td:
        src = os.path.join(td, "in")
        dst = os.path.join(td, "out")
        open(src, "wb").write(data)
        env = os.environ.copy()
        env.setdefault("CMIX_MMAP_ALLOC", "1")
        env.setdefault("CMIX_MMAP_DIR", td)
        subprocess.run(
            [str(_binary()), *args, str(_dictionary()), src, dst],
            cwd=td,
            env=env,
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        return open(dst, "rb").read()


def compress(data):
    return _run(["-t"], data)


def decompress(data):
    return _run(["-d"], data)
