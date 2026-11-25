"""Build and load the native helper (`native/fb_native.c`, optional reference-FSST shim).

The shared library is built outside the repository: in `$FAIR_BASELINES_BUILD_DIR` if set,
otherwise in a directory under the system temporary directory. Nothing is written next to
the sources.

Environment:
  FAIR_BASELINES_BUILD_DIR  where to put the built library
  FAIR_BASELINES_FSST_SRC   directory holding a checkout of github.com/cwida/fsst
  FAIR_BASELINES_ZSTD_PREFIX  prefix with include/zstd.h and lib/libzstd.* (searched if unset)
"""
from __future__ import annotations

import ctypes
import hashlib
import math
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Sequence

HERE = Path(__file__).resolve().parent
NATIVE_DIR = HERE / 'native'
FB_ERR = ctypes.c_size_t(-1).value

ZSTD_MODE_FRAME = 0       # standard frame: magic, content size, dictionary ID, no checksum
ZSTD_MODE_LEAN_FRAME = 1  # magicless, no content size, no dictionary ID, no checksum
ZSTD_MODE_BLOCK = 2       # raw block, no frame

ZDICT_FASTCOVER = 0       # `zstd --train` defaults
ZDICT_COVER = 1           # `zstd --train-cover` defaults (parameter optimisation)


class NativeError(RuntimeError):
    pass


def _find_zstd_prefix() -> Path | None:
    cands = []
    env = os.environ.get('FAIR_BASELINES_ZSTD_PREFIX')
    if env:
        cands.append(Path(env))
    cands += [Path('/opt/homebrew'), Path('/usr/local'), Path('/usr')]
    for c in cands:
        if (c / 'include' / 'zstd.h').is_file() and (c / 'include' / 'zdict.h').is_file():
            return c
    return None


def _static_zstd(prefix: Path) -> Path | None:
    for rel in ('lib/libzstd.a', 'lib64/libzstd.a', 'lib/x86_64-linux-gnu/libzstd.a', 'lib/aarch64-linux-gnu/libzstd.a'):
        p = prefix / rel
        if p.is_file():
            return p
    return None


def default_build_dir() -> Path:
    env = os.environ.get('FAIR_BASELINES_BUILD_DIR')
    return Path(env) if env else Path(tempfile.gettempdir()) / 'fair-baselines-v1-build'


def default_fsst_src() -> Path | None:
    env = os.environ.get('FAIR_BASELINES_FSST_SRC')
    return Path(env) if env else None


def _run(cmd: Sequence[str]) -> None:
    proc = subprocess.run(list(cmd), capture_output=True, text=True)
    if proc.returncode != 0:
        raise NativeError(f'build step failed: {" ".join(Path(c).name if "/" in c else c for c in cmd)}\n{proc.stderr.strip()}')


def build_library(fsst_src: Path | None = None, build_dir: Path | None = None) -> tuple[Path, dict]:
    """Compile the helper if needed. Returns (library path, build facts for the results file)."""
    build_dir = build_dir or default_build_dir()
    fsst_src = fsst_src if fsst_src is not None else default_fsst_src()
    prefix = _find_zstd_prefix()
    if prefix is None:
        raise NativeError('zstd headers not found; set FAIR_BASELINES_ZSTD_PREFIX')
    have_fsst = bool(fsst_src) and all((Path(fsst_src) / f).is_file() for f in ('fsst.h', 'libfsst.cpp', 'fsst_avx512.cpp'))
    sources = [NATIVE_DIR / 'fb_native.c', NATIVE_DIR / 'fb_native.h']
    if have_fsst:
        sources += [NATIVE_DIR / 'fb_fsst_shim.cpp', Path(fsst_src) / 'fsst.h', Path(fsst_src) / 'libfsst.cpp',
                    Path(fsst_src) / 'libfsst.hpp', Path(fsst_src) / 'fsst_avx512.cpp']
    h = hashlib.sha256()
    for s in sources:
        h.update(s.name.encode())
        h.update(s.read_bytes())
    h.update(str(prefix).encode())
    h.update(sys.platform.encode())
    key = h.hexdigest()[:16]
    ext = 'dylib' if sys.platform == 'darwin' else 'so'
    lib_path = build_dir / f'libfbnative-{key}.{ext}'
    facts = {
        'fsst_reference_built': have_fsst,
        'zstd_linkage': None,
        'source_sha256_16': key,
    }
    static = _static_zstd(prefix)
    facts['zstd_linkage'] = 'static libzstd.a' if static else 'shared libzstd'
    if lib_path.is_file():
        return lib_path, facts
    build_dir.mkdir(parents=True, exist_ok=True)
    work = Path(tempfile.mkdtemp(prefix='fb-obj-', dir=str(build_dir)))
    cc = os.environ.get('CC', 'cc')
    cxx = os.environ.get('CXX', 'c++')
    objs = [str(work / 'fb_native.o')]
    cflags = ['-O3', '-std=c11', '-fPIC', '-Wall', '-Wextra', f'-I{prefix / "include"}', f'-I{NATIVE_DIR}']
    if not have_fsst:
        cflags.append('-DFB_NO_FSST')
    _run([cc, *cflags, '-c', str(NATIVE_DIR / 'fb_native.c'), '-o', objs[0]])
    if have_fsst:
        cxxflags = ['-std=c++17', '-fPIC', '-DNDEBUG', '-w']
        _run([cxx, '-O3', *cxxflags, '-c', str(Path(fsst_src) / 'libfsst.cpp'), '-o', str(work / 'libfsst.o')])
        _run([cxx, '-O1', *cxxflags, '-c', str(Path(fsst_src) / 'fsst_avx512.cpp'), '-o', str(work / 'fsst_avx512.o')])
        _run([cxx, '-O3', '-std=c++17', '-fPIC', '-Wall', f'-I{fsst_src}', f'-I{NATIVE_DIR}', '-c',
              str(NATIVE_DIR / 'fb_fsst_shim.cpp'), '-o', str(work / 'fb_fsst_shim.o')])
        objs += [str(work / 'libfsst.o'), str(work / 'fsst_avx512.o'), str(work / 'fb_fsst_shim.o')]
    linker = cxx if have_fsst else cc
    tmp_lib = work / lib_path.name
    link_static = [linker, '-shared', '-o', str(tmp_lib), *objs, str(static), '-lz'] if static else None
    link_shared = [linker, '-shared', '-o', str(tmp_lib), *objs, f'-L{prefix / "lib"}', '-lzstd', '-lz']
    try:
        _run(link_static or link_shared)
    except NativeError:
        if not link_static:
            raise
        facts['zstd_linkage'] = 'shared libzstd'
        _run(link_shared)
    os.replace(tmp_lib, lib_path)
    for p in work.iterdir():
        p.unlink()
    work.rmdir()
    return lib_path, facts


def _concat(records: Sequence[bytes]):
    n = len(records)
    sizes = (ctypes.c_size_t * max(n, 1))(*[len(r) for r in records])
    return b''.join(records), sizes, n


def percentile(sorted_vals: Sequence[float], q: float) -> float:
    """Nearest-rank percentile of an already sorted sequence."""
    if not sorted_vals:
        return float('nan')
    k = max(1, math.ceil(q * len(sorted_vals)))
    return float(sorted_vals[k - 1])


class Native:
    def __init__(self, lib_path: Path, facts: dict | None = None):
        self.lib_path = lib_path
        self.facts = dict(facts or {})
        lib = ctypes.CDLL(str(lib_path))
        self.lib = lib
        vp, sz, u8p = ctypes.c_void_p, ctypes.c_size_t, ctypes.c_char_p
        szp = ctypes.POINTER(ctypes.c_size_t)
        lib.fb_last_error.restype = ctypes.c_char_p
        lib.fb_zstd_version.restype = ctypes.c_char_p
        lib.fb_zlib_version.restype = ctypes.c_char_p
        lib.fb_has_fsst.restype = ctypes.c_int
        lib.fb_open.restype = vp
        lib.fb_open.argtypes = [u8p, sz]
        lib.fb_close.argtypes = [vp]
        lib.fb_count.restype = ctypes.c_uint32
        lib.fb_count.argtypes = [vp]
        lib.fb_decode.restype = sz
        lib.fb_decode.argtypes = [vp, ctypes.c_uint32, vp, sz]
        lib.fb_reader_decode_fn.restype = vp
        lib.fb_reader_decode_fn.argtypes = [vp]
        lib.fb_reader_heap_peak.restype = sz
        lib.fb_reader_heap_peak.argtypes = [vp]
        lib.fb_zdict_train.restype = sz
        lib.fb_zdict_train.argtypes = [ctypes.c_int, u8p, szp, ctypes.c_uint, vp, sz, ctypes.c_int, ctypes.c_uint]
        lib.fb_zdict_header_size.restype = sz
        lib.fb_zdict_header_size.argtypes = [u8p, sz]
        lib.fb_zenc_create.restype = vp
        lib.fb_zenc_create.argtypes = [u8p, sz, ctypes.c_int, ctypes.c_int, ctypes.c_int, sz]
        lib.fb_zenc_free.argtypes = [vp]
        lib.fb_zenc_compress_many.restype = sz
        lib.fb_zenc_compress_many.argtypes = [vp, u8p, szp, sz, vp, sz, szp]
        lib.fb_zstd_compress_bound.restype = sz
        lib.fb_zstd_compress_bound.argtypes = [sz]
        lib.fb_zstd_frame_account.restype = ctypes.c_int
        lib.fb_zstd_frame_account.argtypes = [u8p, sz, ctypes.c_int, ctypes.POINTER(ctypes.c_uint32)]
        lib.fb_timer_probe.argtypes = [ctypes.POINTER(ctypes.c_double), ctypes.POINTER(ctypes.c_double)]
        lib.fb_time_lookups.restype = ctypes.c_int
        lib.fb_time_lookups.argtypes = [vp, vp, ctypes.c_uint32, ctypes.c_uint64, ctypes.c_uint64, ctypes.c_uint64, sz,
                                        vp, vp, vp, ctypes.POINTER(ctypes.c_uint64),
                                        ctypes.POINTER(ctypes.c_uint64), ctypes.POINTER(ctypes.c_uint64),
                                        ctypes.POINTER(ctypes.c_uint64)]
        self.has_fsst = bool(lib.fb_has_fsst())
        if self.has_fsst:
            lib.fb_fsst_train.restype = vp
            lib.fb_fsst_train.argtypes = [u8p, szp, sz]
            lib.fb_fsst_max_header.restype = sz
            lib.fb_fsst_export.restype = sz
            lib.fb_fsst_export.argtypes = [vp, vp]
            lib.fb_fsst_destroy.argtypes = [vp]
            lib.fb_fsst_compress.restype = sz
            lib.fb_fsst_compress.argtypes = [vp, u8p, szp, sz, vp, sz, szp]
        self.zstd_version = lib.fb_zstd_version().decode()
        self.zlib_version = lib.fb_zlib_version().decode()

    def _err(self) -> str:
        return self.lib.fb_last_error().decode(errors='replace')

    # ---- zstd ----
    def zdict_train(self, kind: int, samples: Sequence[bytes], max_bytes: int, level: int, steps: int = 0) -> bytes:
        concat, sizes, n = _concat(samples)
        buf = ctypes.create_string_buffer(max_bytes)
        rc = self.lib.fb_zdict_train(kind, concat, sizes, n, buf, max_bytes, level, steps)
        if rc == FB_ERR:
            raise NativeError(self._err())
        return buf.raw[:rc]

    def zdict_header_size(self, dict_bytes: bytes) -> int:
        rc = self.lib.fb_zdict_header_size(dict_bytes, len(dict_bytes))
        if rc == FB_ERR:
            raise NativeError('not a zstd-format dictionary')
        return rc

    def zstd_encode_many(self, records: Sequence[bytes], *, dict_bytes: bytes, dict_is_raw: bool, level: int,
                         mode: int) -> list[bytes]:
        """One output per record. In raw-block mode an empty output means "store this record raw"."""
        if not records:
            return []
        max_src = max(len(r) for r in records)
        enc = self.lib.fb_zenc_create(dict_bytes, len(dict_bytes), int(dict_is_raw), level, mode, max_src)
        if not enc:
            raise NativeError(self._err())
        try:
            concat, sizes, n = _concat(records)
            cap = sum(self.lib.fb_zstd_compress_bound(len(r)) + 32 for r in records)
            out = ctypes.create_string_buffer(cap)
            out_sizes = (ctypes.c_size_t * n)()
            total = self.lib.fb_zenc_compress_many(enc, concat, sizes, n, out, cap, out_sizes)
            if total == FB_ERR:
                raise NativeError(self._err())
            raw = out.raw[:total]
            res, pos = [], 0
            for i in range(n):
                res.append(raw[pos:pos + out_sizes[i]])
                pos += out_sizes[i]
            return res
        finally:
            self.lib.fb_zenc_free(enc)

    def zstd_frame_account(self, frame: bytes, magicless: bool) -> tuple[int, int, int, int]:
        """(frame header bytes incl. magic, block header bytes, checksum bytes, block content bytes)."""
        out = (ctypes.c_uint32 * 4)()
        if self.lib.fb_zstd_frame_account(frame, len(frame), int(magicless), out) != 0:
            raise NativeError('could not parse zstd frame for accounting')
        return out[0], out[1], out[2], out[3]

    # ---- FSST (reference) ----
    def fsst_train(self, records: Sequence[bytes]) -> 'FsstEncoder':
        if not self.has_fsst:
            raise NativeError('reference FSST was not built into the helper')
        concat, sizes, n = _concat(records)
        enc = self.lib.fb_fsst_train(concat, sizes, n)
        if not enc:
            raise NativeError('fsst_create failed')
        return FsstEncoder(self, enc)

    # ---- reader / timing ----
    def open(self, archive: bytes) -> 'NativeReader':
        h = self.lib.fb_open(archive, len(archive))
        if not h:
            raise NativeError(self._err())
        return NativeReader(self, h)

    def timer_probe(self) -> dict:
        tick, cost = ctypes.c_double(), ctypes.c_double()
        self.lib.fb_timer_probe(ctypes.byref(tick), ctypes.byref(cost))
        return {'timer_step_ns': round(tick.value, 2), 'timer_read_cost_ns': round(cost.value, 2)}

    def time_lookups(self, fn_addr: int, ctx_addr: int, n_records: int, *, n_lookups: int, warmup: int, seed: int,
                     out_cap: int) -> dict:
        samples = (ctypes.c_uint32 * n_lookups)()
        rec_sum = (ctypes.c_double * n_records)()
        rec_cnt = (ctypes.c_uint32 * n_records)()
        total, nbytes, csum, cut = ctypes.c_uint64(), ctypes.c_uint64(), ctypes.c_uint64(), ctypes.c_uint64()
        rc = self.lib.fb_time_lookups(fn_addr, ctx_addr, n_records, n_lookups, warmup, seed, out_cap,
                                      samples, rec_sum, rec_cnt, ctypes.byref(total), ctypes.byref(nbytes),
                                      ctypes.byref(csum), ctypes.byref(cut))
        if rc != 0:
            raise NativeError('a lookup failed inside the timing loop')
        s = sorted(samples)
        per_rec = sorted(rec_sum[i] / rec_cnt[i] for i in range(n_records) if rec_cnt[i])
        return {
            'lookups': n_lookups,
            'loop_mean_ns': round(total.value / n_lookups, 2),
            'decoded_mib_per_sec': round((nbytes.value / (1024 * 1024)) / (total.value * 1e-9), 2) if total.value else None,
            'single_lookup_median_ns': percentile(s, 0.50),
            'single_lookup_p95_ns': percentile(s, 0.95),
            'single_lookup_p99_ns': percentile(s, 0.99),
            'per_record_mean_median_ns': round(percentile(per_rec, 0.50), 2),
            'per_record_mean_p95_ns': round(percentile(per_rec, 0.95), 2),
            'records_visited': len(per_rec),
            'interrupted_samples_left_out_of_per_record_means': cut.value,
        }


class FsstEncoder:
    def __init__(self, native: Native, handle: int):
        self.native, self.handle = native, handle

    def export(self) -> bytes:
        lib = self.native.lib
        buf = ctypes.create_string_buffer(lib.fb_fsst_max_header() + 16)
        n = lib.fb_fsst_export(self.handle, buf)
        return buf.raw[:n]

    def compress(self, records: Sequence[bytes]) -> list[bytes]:
        if not records:
            return []
        concat, sizes, n = _concat(records)
        cap = 7 * n + 2 * len(concat) + 64
        out = ctypes.create_string_buffer(cap)
        out_sizes = (ctypes.c_size_t * n)()
        total = self.native.lib.fb_fsst_compress(self.handle, concat, sizes, n, out, cap, out_sizes)
        if total == FB_ERR:
            raise NativeError('fsst_compress did not encode every record')
        raw = out.raw[:total]
        res, pos = [], 0
        for i in range(n):
            res.append(raw[pos:pos + out_sizes[i]])
            pos += out_sizes[i]
        return res

    def close(self) -> None:
        if self.handle:
            self.native.lib.fb_fsst_destroy(self.handle)
            self.handle = None

    def __del__(self):
        try:
            self.close()
        except Exception:
            pass


class NativeReader:
    """Reader over the serialized archive bytes; every lookup is independent."""

    def __init__(self, native: Native, handle: int):
        self.native, self.handle = native, handle
        self.count = native.lib.fb_count(handle)
        self._cap = 0
        self._buf = None

    def decode(self, i: int, cap: int = 1 << 16) -> bytes:
        lib = self.native.lib
        while True:
            if self._buf is None or self._cap < cap:
                self._buf, self._cap = ctypes.create_string_buffer(cap + 64), cap
            n = lib.fb_decode(self.handle, i, self._buf, self._cap)
            if n != FB_ERR:
                return self._buf.raw[:n]
            if cap >= (1 << 30):
                raise NativeError(f'record {i} could not be decoded')
            cap *= 4

    @property
    def decode_fn_addr(self) -> int:
        return self.native.lib.fb_reader_decode_fn(self.handle)

    @property
    def heap_peak_bytes(self) -> int:
        return self.native.lib.fb_reader_heap_peak(self.handle)

    def close(self) -> None:
        if self.handle:
            self.native.lib.fb_close(self.handle)
            self.handle = None

    def __del__(self):
        try:
            self.close()
        except Exception:
            pass


_CACHE: dict[tuple, Native] = {}


def load_native(fsst_src: Path | None = None, build_dir: Path | None = None) -> Native:
    key = (str(fsst_src) if fsst_src else str(default_fsst_src()), str(build_dir) if build_dir else None)
    if key not in _CACHE:
        lib_path, facts = build_library(fsst_src, build_dir)
        _CACHE[key] = Native(lib_path, facts)
    return _CACHE[key]
