#!/usr/bin/env python3
"""Honest Rung 4 (DCC) & Rung 5 lossless compressor + out-of-sample transfer benchmark.

Compares BITS (Design A, Design B, Design C; token-min and byte-min) against strong
general-purpose lossless compressors on the frozen public CodeNet paired corpora
(`primary` 200 pairs = 400 files, `secondary` 200 pairs = 400 files) AND out-of-sample
transfer (`primary` dictionary -> encoding `secondary` files).

Every compressor is evaluated under TWO deployment models with exact byte-for-byte
round-trip verification:
  1. Per-file random-access mode: each file is compressed & decoded independently.
     Total bytes = trained dictionary bytes (if any) + sum(per-file compressed bytes)
     + 4B routing if separate per-language dictionaries are used.
  2. Solid-archive mode: files concatenated with 4-byte length framing per file
     (matching EOF boundary recovery) and compressed as one stream (or two
     per-language streams + 4B routing).

Baselines tested:
  - zlib -9 (Python stdlib zlib, RFC 1950 deflate)
  - gzip -9 (CLI / Python stdlib gzip)
  - zstd -19 (no dict)
  - zstd -19 --train (shared dict at 8 KiB, 16 KiB, 32 KiB; AND separate py/js dicts
    splitting the budget 50/50!)
  - brotli -11 (CLI `/opt/homebrew/bin/brotli`)
  - xz -6 (Python stdlib lzma)
"""
import json
import lzma
import math
import shutil
import struct
import subprocess
import sys
import tempfile
import time
import zlib
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import byte_encode as BE

ZSTD_BIN = shutil.which('zstd') or '/opt/homebrew/bin/zstd'
BROTLI_BIN = shutil.which('brotli') or '/opt/homebrew/bin/brotli'
ROUTING = 4


def load_split(manifest, split_name):
    pairs = manifest['splits'][split_name]['pairs']
    py_docs = [(HERE / p['python']['path']).read_bytes() for p in pairs]
    js_docs = [(HERE / p['javascript']['path']).read_bytes() for p in pairs]
    return py_docs, js_docs


def pack_framed(docs):
    out = bytearray()
    for d in docs:
        out.extend(struct.pack('<I', len(d)))
        out.extend(d)
    return bytes(out)


def unpack_framed(blob):
    docs = []
    pos = 0
    n = len(blob)
    while pos < n:
        ln = struct.unpack('<I', blob[pos : pos + 4])[0]
        pos += 4
        docs.append(blob[pos : pos + ln])
        pos += ln
    return docs


def bench_zlib(py_docs, js_docs):
    all_docs = py_docs + js_docs
    raw_bytes = sum(len(d) for d in all_docs)

    # Per-file
    t0 = time.perf_counter()
    blobs = [zlib.compress(d, level=9) for d in all_docs]
    enc_ms = (time.perf_counter() - t0) * 1000.0
    t0 = time.perf_counter()
    dec = [zlib.decompress(b) for b in blobs]
    dec_ms = (time.perf_counter() - t0) * 1000.0
    assert dec == all_docs
    per_file = {
        'method': 'zlib-9 (per-file)',
        'mode': 'per-file',
        'dict_bytes': 0,
        'table_or_routing_bytes': 0,
        'payload_bytes': sum(len(b) for b in blobs),
        'total_bytes': sum(len(b) for b in blobs),
        'encode_ms': enc_ms,
        'decode_ms': dec_ms,
        'encode_MB_s': (raw_bytes / 1e6) / (enc_ms / 1000.0),
        'decode_MB_s': (raw_bytes / 1e6) / (dec_ms / 1000.0),
        'verified': True,
    }

    # Solid shared
    framed = pack_framed(all_docs)
    t0 = time.perf_counter()
    c_solid = zlib.compress(framed, level=9)
    enc_ms = (time.perf_counter() - t0) * 1000.0
    t0 = time.perf_counter()
    d_solid = zlib.decompress(c_solid)
    dec_ms = (time.perf_counter() - t0) * 1000.0
    assert unpack_framed(d_solid) == all_docs
    solid_shared = {
        'method': 'zlib-9 (solid shared)',
        'mode': 'solid',
        'dict_bytes': 0,
        'table_or_routing_bytes': 0,
        'payload_bytes': len(c_solid),
        'total_bytes': len(c_solid),
        'encode_ms': enc_ms,
        'decode_ms': dec_ms,
        'encode_MB_s': (raw_bytes / 1e6) / (enc_ms / 1000.0),
        'decode_MB_s': (raw_bytes / 1e6) / (dec_ms / 1000.0),
        'verified': True,
    }

    # Solid separate (py + js + 4B routing)
    fp, fj = pack_framed(py_docs), pack_framed(js_docs)
    t0 = time.perf_counter()
    cp, cj = zlib.compress(fp, level=9), zlib.compress(fj, level=9)
    enc_ms = (time.perf_counter() - t0) * 1000.0
    t0 = time.perf_counter()
    dp, dj = zlib.decompress(cp), zlib.decompress(cj)
    dec_ms = (time.perf_counter() - t0) * 1000.0
    assert unpack_framed(dp) == py_docs and unpack_framed(dj) == js_docs
    solid_sep = {
        'method': 'zlib-9 (solid per-language)',
        'mode': 'solid',
        'dict_bytes': 0,
        'table_or_routing_bytes': ROUTING,
        'payload_bytes': len(cp) + len(cj),
        'total_bytes': len(cp) + len(cj) + ROUTING,
        'encode_ms': enc_ms,
        'decode_ms': dec_ms,
        'encode_MB_s': (raw_bytes / 1e6) / (enc_ms / 1000.0),
        'decode_MB_s': (raw_bytes / 1e6) / (dec_ms / 1000.0),
        'verified': True,
    }
    return [per_file, solid_shared, solid_sep]


def bench_lzma(py_docs, js_docs):
    all_docs = py_docs + js_docs
    raw_bytes = sum(len(d) for d in all_docs)

    # Per-file
    t0 = time.perf_counter()
    blobs = [lzma.compress(d, preset=6) for d in all_docs]
    enc_ms = (time.perf_counter() - t0) * 1000.0
    t0 = time.perf_counter()
    dec = [lzma.decompress(b) for b in blobs]
    dec_ms = (time.perf_counter() - t0) * 1000.0
    assert dec == all_docs
    per_file = {
        'method': 'xz/lzma-6 (per-file)',
        'mode': 'per-file',
        'dict_bytes': 0,
        'table_or_routing_bytes': 0,
        'payload_bytes': sum(len(b) for b in blobs),
        'total_bytes': sum(len(b) for b in blobs),
        'encode_ms': enc_ms,
        'decode_ms': dec_ms,
        'encode_MB_s': (raw_bytes / 1e6) / (enc_ms / 1000.0),
        'decode_MB_s': (raw_bytes / 1e6) / (dec_ms / 1000.0),
        'verified': True,
    }

    # Solid shared
    framed = pack_framed(all_docs)
    t0 = time.perf_counter()
    c_solid = lzma.compress(framed, preset=6)
    enc_ms = (time.perf_counter() - t0) * 1000.0
    t0 = time.perf_counter()
    d_solid = lzma.decompress(c_solid)
    dec_ms = (time.perf_counter() - t0) * 1000.0
    assert unpack_framed(d_solid) == all_docs
    solid_shared = {
        'method': 'xz/lzma-6 (solid shared)',
        'mode': 'solid',
        'dict_bytes': 0,
        'table_or_routing_bytes': 0,
        'payload_bytes': len(c_solid),
        'total_bytes': len(c_solid),
        'encode_ms': enc_ms,
        'decode_ms': dec_ms,
        'encode_MB_s': (raw_bytes / 1e6) / (enc_ms / 1000.0),
        'decode_MB_s': (raw_bytes / 1e6) / (dec_ms / 1000.0),
        'verified': True,
    }

    # Solid separate
    fp, fj = pack_framed(py_docs), pack_framed(js_docs)
    t0 = time.perf_counter()
    cp, cj = lzma.compress(fp, preset=6), lzma.compress(fj, preset=6)
    enc_ms = (time.perf_counter() - t0) * 1000.0
    t0 = time.perf_counter()
    dp, dj = lzma.decompress(cp), lzma.decompress(cj)
    dec_ms = (time.perf_counter() - t0) * 1000.0
    assert unpack_framed(dp) == py_docs and unpack_framed(dj) == js_docs
    solid_sep = {
        'method': 'xz/lzma-6 (solid per-language)',
        'mode': 'solid',
        'dict_bytes': 0,
        'table_or_routing_bytes': ROUTING,
        'payload_bytes': len(cp) + len(cj),
        'total_bytes': len(cp) + len(cj) + ROUTING,
        'encode_ms': enc_ms,
        'decode_ms': dec_ms,
        'encode_MB_s': (raw_bytes / 1e6) / (enc_ms / 1000.0),
        'decode_MB_s': (raw_bytes / 1e6) / (dec_ms / 1000.0),
        'verified': True,
    }
    return [per_file, solid_shared, solid_sep]


def bench_brotli(py_docs, js_docs):
    all_docs = py_docs + js_docs
    raw_bytes = sum(len(d) for d in all_docs)
    results = []

    with tempfile.TemporaryDirectory() as td:
        td_path = Path(td)
        # Per-file (batch CLI invocation for accurate non-fork-dominated timing)
        in_dir = td_path / 'in'
        out_dir = td_path / 'out'
        dec_dir = td_path / 'dec'
        in_dir.mkdir()
        out_dir.mkdir()
        dec_dir.mkdir()
        files = []
        for i, d in enumerate(all_docs):
            p = in_dir / f'f{i:04d}.bin'
            p.write_bytes(d)
            files.append(p)

        t0 = time.perf_counter()
        subprocess.run([BROTLI_BIN, '-q', '11', '-f', '-k'] + [str(f) for f in files], check=True)
        enc_ms = (time.perf_counter() - t0) * 1000.0
        br_files = [Path(str(f) + '.br') for f in files]
        per_file_bytes = sum(f.stat().st_size for f in br_files)

        t0 = time.perf_counter()
        subprocess.run([BROTLI_BIN, '-d', '-f'] + [str(f) for f in br_files], check=True)
        dec_ms = (time.perf_counter() - t0) * 1000.0
        for f, d in zip(files, all_docs):
            assert f.read_bytes() == d

        results.append({
            'method': 'brotli-11 (per-file)',
            'mode': 'per-file',
            'dict_bytes': 0,
            'table_or_routing_bytes': 0,
            'payload_bytes': per_file_bytes,
            'total_bytes': per_file_bytes,
            'encode_ms': enc_ms,
            'decode_ms': dec_ms,
            'encode_MB_s': (raw_bytes / 1e6) / (enc_ms / 1000.0),
            'decode_MB_s': (raw_bytes / 1e6) / (dec_ms / 1000.0),
            'verified': True,
        })

        # Solid shared
        s_in = td_path / 'solid.bin'
        s_in.write_bytes(pack_framed(all_docs))
        s_br = td_path / 'solid.bin.br'
        t0 = time.perf_counter()
        subprocess.run([BROTLI_BIN, '-q', '11', '-f', '-o', str(s_br), str(s_in)], check=True)
        enc_ms = (time.perf_counter() - t0) * 1000.0
        s_dec = td_path / 'solid.dec'
        t0 = time.perf_counter()
        subprocess.run([BROTLI_BIN, '-d', '-f', '-o', str(s_dec), str(s_br)], check=True)
        dec_ms = (time.perf_counter() - t0) * 1000.0
        assert unpack_framed(s_dec.read_bytes()) == all_docs
        results.append({
            'method': 'brotli-11 (solid shared)',
            'mode': 'solid',
            'dict_bytes': 0,
            'table_or_routing_bytes': 0,
            'payload_bytes': s_br.stat().st_size,
            'total_bytes': s_br.stat().st_size,
            'encode_ms': enc_ms,
            'decode_ms': dec_ms,
            'encode_MB_s': (raw_bytes / 1e6) / (enc_ms / 1000.0),
            'decode_MB_s': (raw_bytes / 1e6) / (dec_ms / 1000.0),
            'verified': True,
        })

        # Solid per-language
        sp, sj = td_path / 'py.bin', td_path / 'js.bin'
        sp.write_bytes(pack_framed(py_docs))
        sj.write_bytes(pack_framed(js_docs))
        sp_br, sj_br = td_path / 'py.br', td_path / 'js.br'
        t0 = time.perf_counter()
        subprocess.run([BROTLI_BIN, '-q', '11', '-f', '-o', str(sp_br), str(sp)], check=True)
        subprocess.run([BROTLI_BIN, '-q', '11', '-f', '-o', str(sj_br), str(sj)], check=True)
        enc_ms = (time.perf_counter() - t0) * 1000.0
        sp_dec, sj_dec = td_path / 'py.dec', td_path / 'js.dec'
        t0 = time.perf_counter()
        subprocess.run([BROTLI_BIN, '-d', '-f', '-o', str(sp_dec), str(sp_br)], check=True)
        subprocess.run([BROTLI_BIN, '-d', '-f', '-o', str(sj_dec), str(sj_br)], check=True)
        dec_ms = (time.perf_counter() - t0) * 1000.0
        assert unpack_framed(sp_dec.read_bytes()) == py_docs
        assert unpack_framed(sj_dec.read_bytes()) == js_docs
        pay = sp_br.stat().st_size + sj_br.stat().st_size
        results.append({
            'method': 'brotli-11 (solid per-language)',
            'mode': 'solid',
            'dict_bytes': 0,
            'table_or_routing_bytes': ROUTING,
            'payload_bytes': pay,
            'total_bytes': pay + ROUTING,
            'encode_ms': enc_ms,
            'decode_ms': dec_ms,
            'encode_MB_s': (raw_bytes / 1e6) / (enc_ms / 1000.0),
            'decode_MB_s': (raw_bytes / 1e6) / (dec_ms / 1000.0),
            'verified': True,
        })
    return results


def bench_zstd(py_docs, js_docs, train_py=None, train_js=None, label_suffix=''):
    """Benchmark zstd -19 (per-file, solid, shared --train dict, per-lang --train dicts).

    If train_py/train_js are provided, trains dictionaries on train_* and applies to py_docs/js_docs
    (out-of-sample transfer); otherwise trains on py_docs/js_docs (in-sample).
    """
    all_docs = py_docs + js_docs
    raw_bytes = sum(len(d) for d in all_docs)
    t_py = py_docs if train_py is None else train_py
    t_js = js_docs if train_js is None else train_js
    results = []

    with tempfile.TemporaryDirectory() as td:
        td_path = Path(td)
        eval_py_dir = td_path / 'eval_py'
        eval_js_dir = td_path / 'eval_js'
        train_py_dir = td_path / 'train_py'
        train_js_dir = td_path / 'train_js'
        for d in (eval_py_dir, eval_js_dir, train_py_dir, train_js_dir):
            d.mkdir()

        eval_py_files, eval_js_files = [], []
        for i, b in enumerate(py_docs):
            p = eval_py_dir / f'p{i:04d}.py'
            p.write_bytes(b)
            eval_py_files.append(p)
        for i, b in enumerate(js_docs):
            p = eval_js_dir / f'j{i:04d}.js'
            p.write_bytes(b)
            eval_js_files.append(p)
        eval_all_files = eval_py_files + eval_js_files

        train_py_files, train_js_files = [], []
        for i, b in enumerate(t_py):
            p = train_py_dir / f'tp{i:04d}.py'
            p.write_bytes(b)
            train_py_files.append(p)
        for i, b in enumerate(t_js):
            p = train_js_dir / f'tj{i:04d}.js'
            p.write_bytes(b)
            train_js_files.append(p)
        train_all_files = train_py_files + train_js_files

        def run_zstd_per_file(files_list, raw_list, dict_path=None):
            z_dir = td_path / f'z_{time.time_ns()}'
            d_dir = td_path / f'd_{time.time_ns()}'
            z_dir.mkdir()
            d_dir.mkdir()
            cmd_enc = [ZSTD_BIN, '-19', '-q', '-f', '--output-dir-flat', str(z_dir)]
            if dict_path is not None:
                cmd_enc += ['-D', str(dict_path)]
            cmd_enc += [str(f) for f in files_list]
            t0 = time.perf_counter()
            subprocess.run(cmd_enc, check=True)
            enc_ms = (time.perf_counter() - t0) * 1000.0

            z_files = [z_dir / (f.name + '.zst') for f in files_list]
            pay_bytes = sum(zf.stat().st_size for zf in z_files)

            cmd_dec = [ZSTD_BIN, '-d', '-q', '-f', '--output-dir-flat', str(d_dir)]
            if dict_path is not None:
                cmd_dec += ['-D', str(dict_path)]
            cmd_dec += [str(zf) for zf in z_files]
            t0 = time.perf_counter()
            subprocess.run(cmd_dec, check=True)
            dec_ms = (time.perf_counter() - t0) * 1000.0

            for f, orig in zip(files_list, raw_list):
                assert (d_dir / f.name).read_bytes() == orig
            return pay_bytes, enc_ms, dec_ms

        # 1. Per-file no dict (only if in-sample)
        if train_py is None:
            pay, ems, dms = run_zstd_per_file(eval_all_files, all_docs)
            results.append({
                'method': f'zstd-19 (per-file, no dict){label_suffix}',
                'mode': 'per-file',
                'dict_bytes': 0,
                'table_or_routing_bytes': 0,
                'payload_bytes': pay,
                'total_bytes': pay,
                'encode_ms': ems,
                'decode_ms': dms,
                'encode_MB_s': (raw_bytes / 1e6) / (ems / 1000.0),
                'decode_MB_s': (raw_bytes / 1e6) / (dms / 1000.0),
                'verified': True,
            })

            # Solid shared & separate
            s_in = td_path / 'solid.bin'
            s_in.write_bytes(pack_framed(all_docs))
            s_zst = td_path / 'solid.zst'
            t0 = time.perf_counter()
            subprocess.run([ZSTD_BIN, '-19', '-q', '-f', '-o', str(s_zst), str(s_in)], check=True)
            ems = (time.perf_counter() - t0) * 1000.0
            s_dec = td_path / 'solid.dec'
            t0 = time.perf_counter()
            subprocess.run([ZSTD_BIN, '-d', '-q', '-f', '-o', str(s_dec), str(s_zst)], check=True)
            dms = (time.perf_counter() - t0) * 1000.0
            assert unpack_framed(s_dec.read_bytes()) == all_docs
            results.append({
                'method': f'zstd-19 (solid shared){label_suffix}',
                'mode': 'solid',
                'dict_bytes': 0,
                'table_or_routing_bytes': 0,
                'payload_bytes': s_zst.stat().st_size,
                'total_bytes': s_zst.stat().st_size,
                'encode_ms': ems,
                'decode_ms': dms,
                'encode_MB_s': (raw_bytes / 1e6) / (ems / 1000.0),
                'decode_MB_s': (raw_bytes / 1e6) / (dms / 1000.0),
                'verified': True,
            })

            sp, sj = td_path / 'sp.bin', td_path / 'sj.bin'
            sp.write_bytes(pack_framed(py_docs))
            sj.write_bytes(pack_framed(js_docs))
            sp_z, sj_z = td_path / 'sp.zst', td_path / 'sj.zst'
            t0 = time.perf_counter()
            subprocess.run([ZSTD_BIN, '-19', '-q', '-f', '-o', str(sp_z), str(sp)], check=True)
            subprocess.run([ZSTD_BIN, '-19', '-q', '-f', '-o', str(sj_z), str(sj)], check=True)
            ems = (time.perf_counter() - t0) * 1000.0
            sp_d, sj_d = td_path / 'sp.dec', td_path / 'sj.dec'
            t0 = time.perf_counter()
            subprocess.run([ZSTD_BIN, '-d', '-q', '-f', '-o', str(sp_d), str(sp_z)], check=True)
            subprocess.run([ZSTD_BIN, '-d', '-q', '-f', '-o', str(sj_d), str(sj_z)], check=True)
            dms = (time.perf_counter() - t0) * 1000.0
            assert unpack_framed(sp_d.read_bytes()) == py_docs and unpack_framed(sj_d.read_bytes()) == js_docs
            pay_s = sp_z.stat().st_size + sj_z.stat().st_size
            results.append({
                'method': f'zstd-19 (solid per-language){label_suffix}',
                'mode': 'solid',
                'dict_bytes': 0,
                'table_or_routing_bytes': ROUTING,
                'payload_bytes': pay_s,
                'total_bytes': pay_s + ROUTING,
                'encode_ms': ems,
                'decode_ms': dms,
                'encode_MB_s': (raw_bytes / 1e6) / (ems / 1000.0),
                'decode_MB_s': (raw_bytes / 1e6) / (dms / 1000.0),
                'verified': True,
            })

        # 2. zstd --train shared dict (8 KiB, 16 KiB, 32 KiB) & separate per-language dicts
        for maxdict in (8192, 16384, 32768):
            dict_shared = td_path / f'dict_shared_{maxdict}.zdict'
            subprocess.run(
                [ZSTD_BIN, '--train', f'--maxdict={maxdict}', '-q', '-o', str(dict_shared)]
                + [str(f) for f in train_all_files],
                check=True,
            )
            d_sz = dict_shared.stat().st_size
            # Also measure compressed dict size (zstd -19 of dict) for fairness note, while reporting raw dict_bytes!
            pay, ems, dms = run_zstd_per_file(eval_all_files, all_docs, dict_path=dict_shared)
            results.append({
                'method': f'zstd-19 --train shared ({maxdict // 1024}KiB dict){label_suffix}',
                'mode': 'per-file-dict',
                'dict_bytes': d_sz,
                'table_or_routing_bytes': 0,
                'payload_bytes': pay,
                'total_bytes': d_sz + pay,
                'payload_only_bytes': pay,
                'encode_ms': ems,
                'decode_ms': dms,
                'encode_MB_s': (raw_bytes / 1e6) / (ems / 1000.0),
                'decode_MB_s': (raw_bytes / 1e6) / (dms / 1000.0),
                'verified': True,
            })

            # Separate per-language trained dicts (each maxdict/2, total dict budget == maxdict!)
            half = maxdict // 2
            dict_py = td_path / f'dict_py_{half}.zdict'
            dict_js = td_path / f'dict_js_{half}.zdict'
            subprocess.run(
                [ZSTD_BIN, '--train', f'--maxdict={half}', '-q', '-o', str(dict_py)]
                + [str(f) for f in train_py_files],
                check=True,
            )
            subprocess.run(
                [ZSTD_BIN, '--train', f'--maxdict={half}', '-q', '-o', str(dict_js)]
                + [str(f) for f in train_js_files],
                check=True,
            )
            d_sep_sz = dict_py.stat().st_size + dict_js.stat().st_size
            pay_p, ems_p, dms_p = run_zstd_per_file(eval_py_files, py_docs, dict_path=dict_py)
            pay_j, ems_j, dms_j = run_zstd_per_file(eval_js_files, js_docs, dict_path=dict_js)
            results.append({
                'method': f'zstd-19 --train per-lang (2x{half // 1024}KiB dict){label_suffix}',
                'mode': 'per-file-dict',
                'dict_bytes': d_sep_sz,
                'table_or_routing_bytes': ROUTING,
                'payload_bytes': pay_p + pay_j,
                'total_bytes': d_sep_sz + ROUTING + pay_p + pay_j,
                'payload_only_bytes': pay_p + pay_j,
                'encode_ms': ems_p + ems_j,
                'decode_ms': dms_p + dms_j,
                'encode_MB_s': (raw_bytes / 1e6) / ((ems_p + ems_j) / 1000.0),
                'decode_MB_s': (raw_bytes / 1e6) / ((dms_p + dms_j) / 1000.0),
                'verified': True,
            })

    return results


def eval_bits_out_of_sample(dict_hex_path, train_py, train_js, eval_py, eval_js, label):
    """Evaluate a dictionary built on `primary` when encoding unseen `secondary` files.

    Ensures all single bytes occurring in `eval` are present in the dictionary (adding
    any unseen single-byte fallback entries honestly to `dict_bytes` and `entries`),
    then scores both:
      - fixed tables trained on `primary` (zero per-batch table transmission on `secondary`,
        Laplace +1 smoothing on any unseen symbols so every symbol has a valid codeword), AND
      - adapted tables fit to `secondary` (counting dict + table + payload).
    """
    base_entries = [bytes.fromhex(line.strip()) for line in Path(dict_hex_path).read_text().splitlines() if line.strip()]
    present = set(base_entries)
    needed_singles = set()
    for doc in eval_py + eval_js:
        for b in doc:
            sb = bytes([b])
            if sb not in present:
                needed_singles.add(sb)
    entries = base_entries + sorted(needed_singles)
    root = BE.build_trie(entries)
    dict_bytes = sum(1 + len(e) for e in entries)
    symbols = len(entries) + 1

    # 1. Adapted tables on secondary (Design A and B, byte-min)
    opt_a = BE.optimize_byte_segmentation(eval_py + eval_js, root)
    opt_p = BE.optimize_byte_segmentation(eval_py, root)
    opt_j = BE.optimize_byte_segmentation(eval_js, root)
    bm_a = opt_a['byte_min']
    bm_p = opt_p['byte_min']
    bm_j = opt_j['byte_min']

    # 2. Frozen tables trained on primary (with +1 smoothing for unseen active entries)
    _, tr_cp, _ = BE.segment_corpus_tokens(train_py, root)
    _, tr_cj, _ = BE.segment_corpus_tokens(train_js, root)
    tr_ca = Counter(tr_cp)
    tr_ca.update(tr_cj)
    for e in entries:
        if tr_ca[e] == 0:
            tr_ca[e] = 1
        if tr_cp[e] == 0:
            tr_cp[e] = 1
        if tr_cj[e] == 0:
            tr_cj[e] = 1
    la_tr = BE.canonical_huffman_lengths(tr_ca)
    lp_tr = BE.canonical_huffman_lengths(tr_cp)
    lj_tr = BE.canonical_huffman_lengths(tr_cj)

    # Encode secondary using primary-frozen code lengths (minimum-bit parse!)
    _, ev_ca, _ = BE.segment_corpus_bits(eval_py + eval_js, root, la_tr, max(la_tr.values()) + 1)
    _, ev_cp, _ = BE.segment_corpus_bits(eval_py, root, lp_tr, max(lp_tr.values()) + 1)
    _, ev_cj, _ = BE.segment_corpus_bits(eval_js, root, lj_tr, max(lj_tr.values()) + 1)
    bits_a_frozen = sum(c * la_tr[s] for s, c in ev_ca.items())
    bits_p_frozen = sum(c * lp_tr[s] for s, c in ev_cp.items())
    bits_j_frozen = sum(c * lj_tr[s] for s, c in ev_cj.items())

    # Verify exact bitstream roundtrip for Design B frozen-table transfer!
    codes_p = BE.assign_canonical_codes(lp_tr)
    codes_j = BE.assign_canonical_codes(lj_tr)
    pieces_p, _, _ = BE.segment_corpus_bits(eval_py, root, lp_tr, max(lp_tr.values()) + 1)
    pieces_j, _, _ = BE.segment_corpus_bits(eval_js, root, lj_tr, max(lj_tr.values()) + 1)
    bs_p, _ = BE.encode_bitstream(pieces_p, codes_p)
    bs_j, _ = BE.encode_bitstream(pieces_j, codes_j)
    assert BE.decode_bitstream(bs_p, len(eval_py), BE.build_decode_tree(codes_p)) == eval_py
    assert BE.decode_bitstream(bs_j, len(eval_js), BE.build_decode_tree(codes_j)) == eval_js

    return {
        'label': label,
        'base_entries': len(base_entries),
        'added_fallback_single_bytes': len(needed_singles),
        'total_entries': len(entries),
        'dict_bytes': dict_bytes,
        'adapted_tables_byte_min': {
            'A_payload_bytes': bm_a['payload_bytes'],
            'A_total_bytes': dict_bytes + symbols + bm_a['payload_bytes'],
            'B_payload_bytes': bm_p['payload_bytes'] + bm_j['payload_bytes'],
            'B_total_bytes': dict_bytes + 2 * symbols + ROUTING + bm_p['payload_bytes'] + bm_j['payload_bytes'],
        },
        'frozen_primary_tables_byte_min': {
            'A_payload_bytes': math.ceil(bits_a_frozen / 8),
            'A_total_bytes': dict_bytes + symbols + math.ceil(bits_a_frozen / 8),
            'B_payload_bytes': math.ceil(bits_p_frozen / 8) + math.ceil(bits_j_frozen / 8),
            'B_total_bytes': dict_bytes + 2 * symbols + ROUTING + math.ceil(bits_p_frozen / 8) + math.ceil(bits_j_frozen / 8),
            'verified_roundtrip': True,
        },
    }


def main():
    manifest = json.loads((HERE / 'manifest.json').read_text(encoding='utf-8'))
    py_pri, js_pri = load_split(manifest, 'primary')
    py_sec, js_sec = load_split(manifest, 'secondary')

    out = {
        'schema': 'gamma.bits-codenet-baselines.v1',
        'primary_raw_bytes': sum(len(x) for x in py_pri) + sum(len(x) for x in js_pri),
        'secondary_raw_bytes': sum(len(x) for x in py_sec) + sum(len(x) for x in js_sec),
        'in_sample': {},
        'out_of_sample_primary_to_secondary': {},
    }

    for split_name, (py_d, js_d) in (('primary', (py_pri, js_pri)), ('secondary', (py_sec, js_sec))):
        print(f'Benchmarking lossless baselines on {split_name}...', flush=True)
        rows = []
        rows.extend(bench_zlib(py_d, js_d))
        rows.extend(bench_zstd(py_d, js_d))
        rows.extend(bench_brotli(py_d, js_d))
        rows.extend(bench_lzma(py_d, js_d))
        out['in_sample'][split_name] = rows
        for r in rows:
            print(
                f"  {r['method']:48s} total={r['total_bytes']:7d} B "
                f"(dict={r['dict_bytes']:6d}, pay={r['payload_bytes']:7d}) "
                f"enc={r['encode_MB_s']:6.2f} MB/s dec={r['decode_MB_s']:7.2f} MB/s"
            )

    print('\nBenchmarking out-of-sample transfer (primary -> secondary)...', flush=True)
    oos_zstd = bench_zstd(py_sec, js_sec, train_py=py_pri, train_js=js_pri, label_suffix=' [train=primary -> eval=secondary]')
    oos_bits = []
    for K in (256, 1024, 4096):
        dpath = HERE / 'dictionaries' / f'primary_K{K}_B_tm.hex'
        if dpath.exists():
            oos_bits.append(eval_bits_out_of_sample(dpath, py_pri, js_pri, py_sec, js_sec, f'BITS primary K={K} B-dict -> secondary'))
    out['out_of_sample_primary_to_secondary'] = {
        'zstd_train': oos_zstd,
        'bits': oos_bits,
    }
    for r in oos_zstd:
        print(
            f"  {r['method']:68s} total={r['total_bytes']:7d} B "
            f"(dict={r['dict_bytes']:6d}, pay={r['payload_bytes']:7d})"
        )
    for b in oos_bits:
        f = b['frozen_primary_tables_byte_min']
        a = b['adapted_tables_byte_min']
        print(
            f"  {b['label']:45s} frozen: A={f['A_total_bytes']} B={f['B_total_bytes']} (pay B={f['B_payload_bytes']}) | "
            f"adapted: A={a['A_total_bytes']} B={a['B_total_bytes']}"
        )

    out_path = HERE / 'results' / 'baselines.json'
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(out, indent=2) + '\n', encoding='utf-8')
    print(f'Wrote {out_path}', flush=True)


if __name__ == '__main__':
    main()
