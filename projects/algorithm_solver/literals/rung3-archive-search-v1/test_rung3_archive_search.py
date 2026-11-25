#!/usr/bin/env python3
"""Unit tests for `rung3-archive-search-v1` (`archive_search.c` & `indexed_archive.py`)."""
from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
CODENET_DIR = HERE.parent / 'codenet-replication-v1'
sys.path.insert(0, str(HERE))

from evaluate_rung3 import compile_binaries, evaluate_pair_benchmark  # noqa: E402
from indexed_archive import (  # noqa: E402
    decode_random_access_file,
    serialize_design_b_random_access_archive,
    unpack_index_and_trees,
)


def test_serialized_random_access_every_file() -> None:
    d1 = [f'def fn_{i}(x):\n    return x * {i} + 42\n'.encode('ascii') for i in range(15)]
    d2 = [f'function fn_{i}(x) {{ return x * {i} + 42; }}\n'.encode('ascii') for i in range(15)]
    alphabet = sorted({ bytes([b]) for d in (d1 + d2) for b in d })
    entries = alphabet + [b'return ', b'function ', b'def ', b' + 42']
    blob = serialize_design_b_random_access_archive(entries, d1, d2)
    hdr = unpack_index_and_trees(blob)
    combined = d1 + d2
    # Decode in reverse order to prove zero sequential state dependence
    for idx in reversed(range(len(combined))):
        got = decode_random_access_file(blob, idx, hdr)
        assert got == combined[idx], f'mismatch at file {idx}'


def test_mdl_archive_prune_beats_greedy_byte_and_keeps_codenet_clean() -> None:
    d1 = [
        (b'def calculate_total(items):\n    acc = 0\n    for v in items:\n        acc += v\n    return acc\n'
         + f'# unique_singleton_long_tag_{i:04d}\n'.encode('ascii'))
        for i in range(20)
    ]
    d2 = [
        (b'export function calculateTotal(items) {\n  let acc = 0;\n  for (const v of items) acc += v;\n  return acc;\n}\n'
         + f'// unique_js_singleton_{i:04d}\n'.encode('ascii'))
        for i in range(20)
    ]
    with tempfile.TemporaryDirectory(prefix='test-rung3-') as tmp:
        eng_bin, arc_bin = compile_binaries(Path(tmp))
        res = evaluate_pair_benchmark(
            eng_bin, arc_bin,
            label='unit-check',
            train_1=d1[:10], train_2=d2[:10],
            test_1=d1[10:], test_2=d2[10:],
            k_max=512, limit_sec=3.0,
        )
    assert res['methods']['mdl-archive-prune']['random_access_verified'] is True
    assert res['comparisons']['prune_gain_over_greedy_byte_in_sample_bytes'] > 0

    status = subprocess.check_output(
        ['git', '-C', str(CODENET_DIR), 'status', '--porcelain', '.'],
        text=True,
    ).strip()
    assert status == '', f'codenet-replication-v1 dirtied: {status}'


if __name__ == '__main__':
    test_serialized_random_access_every_file()
    print('  [PASS] BIT3 4B/file random-access seek verified in reverse order')
    test_mdl_archive_prune_beats_greedy_byte_and_keeps_codenet_clean()
    print('  [PASS] archive_search.c mdl-archive-prune compiled and verified')
    print('ALL rung3-archive-search-v1 unit tests PASSED.')
