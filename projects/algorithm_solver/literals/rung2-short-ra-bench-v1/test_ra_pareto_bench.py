#!/usr/bin/env python3
"""Unit tests for all 4 random-access containers (`BIT3`, `FSST`, `DFL3`, `ZST3`) and native C decoders."""
from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

sys.dont_write_bytecode = True

HERE = Path(__file__).resolve().parent
CODENET_DIR = HERE.parent / 'codenet-replication-v1'
RUNG2_DIR = HERE.parent / 'rung2-presearch-v1'

sys.path.insert(0, str(CODENET_DIR))
sys.path.insert(0, str(RUNG2_DIR))
sys.path.insert(0, str(HERE))

from fsst255_codec import serialize_fsst255_archive, train_fsst255_table  # noqa: E402
from run_completed_chain_and_regime_eval import serialize_and_verify_bit3_archive  # noqa: E402
from run_ra_pareto_bench import (  # noqa: E402
    build_tuned_zst3_and_dfl3,
    compile_c_bench,
    run_c_bench,
    write_raw_verify_blob,
)


def test_all_four_native_c_decoders_roundtrip() -> None:
    docs_1 = [
        f'{{"id":{i},"kind":"alpha","values":[1,2,3],"active":true}}\n'.encode('ascii') * (1 + (i % 3))
        for i in range(24)
    ]
    docs_2 = [
        f'@compute @workgroup_size(64) fn kernel_{i}(@builtin(global_invocation_id) gid: vec3<u32>) {{}}\n'.encode('ascii')
        for i in range(24)
    ]
    all_docs = docs_1 + docs_2

    # Build dictionary containing all single bytes + several frequent phrases
    singles = sorted({bytes([b]) for d in all_docs for b in d})
    phrases = [b'{"id":', b',"kind":"alpha",', b'@compute ', b'@workgroup_size(64)']
    entries = singles + [p for p in phrases if p not in singles]

    with tempfile.TemporaryDirectory(prefix='test-ra-c-') as tmp:
        wdir = Path(tmp)
        c_bin = compile_c_bench(wdir)
        raw_v = wdir / 'raw.bin'
        write_raw_verify_blob(all_docs, raw_v)

        # 1. BIT3 (both 1-table Design A and 2-table Design B)
        for n_tbl in (1, 2):
            b_blob, _ = serialize_and_verify_bit3_archive(entries, docs_1, docs_2, n_tables=n_tbl)
            bp = wdir / f't_{n_tbl}.bit3'
            bp.write_bytes(b_blob)
            res = run_c_bench(c_bin, 'BIT3', bp, raw_v, num_seeks=5000)
            assert res['verified_docs'] == len(all_docs), res
            assert res['ns_per_seek'] > 0.0 and res['decoded_mib_per_sec'] > 0.0, res

        # 2. FSST-255
        syms = train_fsst255_table(all_docs)
        f_blob = serialize_fsst255_archive(syms, all_docs)
        fp = wdir / 't.fsst'
        fp.write_bytes(f_blob)
        f_res = run_c_bench(c_bin, 'FSST', fp, raw_v, num_seeks=5000)
        assert f_res['verified_docs'] == len(all_docs), f_res

        # 3 & 4. ZST3 & DFL3
        _, zp, _, dp = build_tuned_zst3_and_dfl3(all_docs[:24], all_docs, wdir / 'zd')
        z_res = run_c_bench(c_bin, 'ZST3', zp, raw_v, num_seeks=5000)
        d_res = run_c_bench(c_bin, 'DFL3', dp, raw_v, num_seeks=5000)
        assert z_res['verified_docs'] == len(all_docs), z_res
        assert d_res['verified_docs'] == len(all_docs), d_res

    out = subprocess.check_output(
        ['git', '-C', str(CODENET_DIR), 'status', '--porcelain', '.'],
        text=True,
    ).strip()
    assert out == '', f'codenet-replication-v1 dirtied: {out}'


def main() -> None:
    test_all_four_native_c_decoders_roundtrip()
    print('ALL rung2-short-ra-bench-v1 native C random-access roundtrip & speed tests PASSED.')


if __name__ == '__main__':
    main()
