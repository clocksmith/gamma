"""Official NNCP preprocessing composed with the frozen B2 cmix21 backend."""

from __future__ import annotations

import gzip
import os
import pathlib
import stat
import struct
import subprocess
import tarfile
import tempfile

_DIR = pathlib.Path(__file__).resolve().parent
_CMIX_GZ = _DIR / "cmix.bin.gz"
_CMIX_DICT_GZ = _DIR / "english.dic.gz"
_NNCP_SOURCE = _DIR / "nncp_cpu_source.tar.gz"
_MAGIC = b"NPCM21\x01"
_cmix_bin: pathlib.Path | None = None
_cmix_dict: pathlib.Path | None = None
_nncp_dir: pathlib.Path | None = None


def _extract_gzip(src: pathlib.Path, prefix: str, executable: bool) -> pathlib.Path:
    fd, name = tempfile.mkstemp(prefix=prefix)
    os.close(fd)
    path = pathlib.Path(name)
    with gzip.open(src, "rb") as inp:
        path.write_bytes(inp.read())
    if executable:
        path.chmod(path.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    return path


def _cmix_binary() -> pathlib.Path:
    global _cmix_bin
    if _cmix_bin is None or not _cmix_bin.exists():
        _cmix_bin = _extract_gzip(_CMIX_GZ, "nncp-pc-cmix-bin-", True)
    return _cmix_bin


def _cmix_dictionary() -> pathlib.Path:
    global _cmix_dict
    if _cmix_dict is None or not _cmix_dict.exists():
        _cmix_dict = _extract_gzip(_CMIX_DICT_GZ, "nncp-pc-cmix-dict-", False)
    return _cmix_dict


def _nncp_binary() -> tuple[pathlib.Path, dict[str, str]]:
    global _nncp_dir
    if _nncp_dir is None or not (_nncp_dir / "nncp").is_file():
        _nncp_dir = pathlib.Path(tempfile.mkdtemp(prefix="nncp-pc-build-"))
        with tarfile.open(_NNCP_SOURCE, "r:gz") as archive:
            archive.extractall(_nncp_dir)
        subprocess.run(
            ["make", "-C", str(_nncp_dir), "-j2"],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    env = os.environ.copy()
    prior = env.get("LD_LIBRARY_PATH")
    env["LD_LIBRARY_PATH"] = str(_nncp_dir) if not prior else f"{_nncp_dir}:{prior}"
    return _nncp_dir / "nncp", env


def _cmix(args: list[str], data: bytes) -> bytes:
    with tempfile.TemporaryDirectory(prefix="nncp-pc-cmix-run-") as td_raw:
        td = pathlib.Path(td_raw)
        source = td / "in"
        destination = td / "out"
        source.write_bytes(data)
        env = os.environ.copy()
        env.setdefault("CMIX_MMAP_ALLOC", "1")
        env.setdefault("CMIX_MMAP_DIR", str(td))
        subprocess.run(
            [str(_cmix_binary()), *args, str(source), str(destination)],
            cwd=td,
            env=env,
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        return destination.read_bytes()


def _preprocess(data: bytes) -> tuple[bytes, bytes]:
    binary, env = _nncp_binary()
    with tempfile.TemporaryDirectory(prefix="nncp-pc-encode-") as td_raw:
        td = pathlib.Path(td_raw)
        source = td / "raw"
        symbols = td / "symbols"
        dictionary = td / "dictionary"
        source.write_bytes(data)
        subprocess.run(
            [
                str(binary), "--profile", "enwik9", "--preprocess", "16384,512",
                "--dict", str(dictionary), "pc", str(source), str(symbols),
            ],
            env=env,
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        return dictionary.read_bytes(), symbols.read_bytes()


def _restore(dictionary_data: bytes, symbols_data: bytes) -> bytes:
    binary, env = _nncp_binary()
    with tempfile.TemporaryDirectory(prefix="nncp-pc-decode-") as td_raw:
        td = pathlib.Path(td_raw)
        dictionary = td / "dictionary"
        symbols = td / "symbols"
        restored = td / "raw"
        dictionary.write_bytes(dictionary_data)
        symbols.write_bytes(symbols_data)
        subprocess.run(
            [str(binary), "--dict", str(dictionary), "pd", str(symbols), str(restored)],
            env=env,
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        return restored.read_bytes()


def compress(data: bytes) -> bytes:
    dictionary, symbols = _preprocess(data)
    payload = _cmix(["-n"], symbols)
    return _MAGIC + struct.pack(">II", len(dictionary), len(payload)) + dictionary + payload


def decompress(archive: bytes) -> bytes:
    header = len(_MAGIC) + 8
    if len(archive) < header or archive[: len(_MAGIC)] != _MAGIC:
        raise ValueError("invalid NNCP/cmix archive header")
    dictionary_size, payload_size = struct.unpack(">II", archive[len(_MAGIC) : header])
    expected = header + dictionary_size + payload_size
    if len(archive) != expected:
        raise ValueError("invalid NNCP/cmix archive lengths")
    dictionary = archive[header : header + dictionary_size]
    payload = archive[header + dictionary_size :]
    symbols = _cmix(["-d"], payload)
    return _restore(dictionary, symbols)
