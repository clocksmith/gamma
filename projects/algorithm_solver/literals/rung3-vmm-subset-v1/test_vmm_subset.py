#!/usr/bin/env python3
"""Unit tests for `vmm_subset_polish.py` (Nash Fixed-Point Certifier & Variational Two-Part MM)."""
from __future__ import annotations

import subprocess
import sys
from collections import Counter
from pathlib import Path

sys.dont_write_bytecode = True

HERE = Path(__file__).resolve().parent
CODENET_DIR = HERE.parent / 'codenet-replication-v1'
sys.path.insert(0, str(CODENET_DIR))
sys.path.insert(0, str(HERE))

import byte_encode as BE  # noqa: E402
from vmm_subset_polish import (  # noqa: E402
    certify_emitted_table_optimality,
    polish_to_certified_nash_single,
    variational_two_part_mm,
)


def test_certifier_catches_suboptimal_parse_and_polishes_to_zero_gap() -> None:
    docs = [b'return value;\n' * 12, b'return count;\n' * 12]
    singles = sorted({bytes([b]) for d in docs for b in d})
    entries = singles + [b'ret', b'urn ', b'return ']

    # Deliberately construct a suboptimal 1-byte parse while building lengths that favor `return `
    good_counts = Counter({b'return ': 24, b'v': 12, b'a': 12, b'l': 12, b'u': 24, b'e': 12, b';': 24, b'\n': 24, b'c': 12, b'o': 12, b'n': 12, b't': 12, BE.EOF_SYMBOL: 2})
    for s in singles:
        if good_counts[s] == 0:
            good_counts[s] = 1
    lengths = BE.canonical_huffman_lengths(good_counts)

    # Naive 1-byte parse bits under `lengths` (ignores `return `!)
    bad_bits = sum(lengths[bytes([b])] for d in docs for b in d) + 2 * lengths[BE.EOF_SYMBOL]
    bad_cert = certify_emitted_table_optimality(docs, entries, lengths, bad_bits)
    assert bad_cert['is_certified_nash_fixed_point'] is False
    assert bad_cert['parse_suboptimality_bits'] > 50

    # Polish converges to 0-bit certified Nash fixed point
    polished = polish_to_certified_nash_single(docs, entries, good_counts)
    assert polished['certificate']['is_certified_nash_fixed_point'] is True
    assert polished['certificate']['parse_suboptimality_bits'] == 0


def test_vmm_excises_absorbed_bpe_scaffolds_and_beats_prefix_stop() -> None:
    # Construct a corpus with two high-frequency words (`return_result` and `workgroup_id`),
    # plus intermediate BPE merge scaffolds (`re`, `ret`, `retu`, `retur`, `return_`, etc.)
    # ordered so `workgroup_id` appears AFTER `200` low-count noise phrases!
    docs_1 = [b'return_result = compute(x);\n' * 20 for _ in range(10)]
    docs_2 = [b'workgroup_id = dispatch(y);\n' * 20 for _ in range(10)]
    all_docs = docs_1 + docs_2
    singles = sorted({bytes([b]) for d in all_docs for b in d})

    scaffolds = [b're', b'ret', b'retu', b'retur', b'return', b'return_', b'return_resul']
    noise = [f'#{i:03d}#'.encode('ascii') for i in range(80)]  # zero/tiny support bloat in middle of chain!
    chain = singles + scaffolds + [b'return_result = '] + noise + [b'workgroup_id = ']

    # Any prefix keeping `workgroup_id = ` at the end of `chain` MUST pay for all 80 noise entries + 7 dead scaffolds!
    full_nash = polish_to_certified_nash_single(all_docs, chain, prune_dead_multibyte=False)
    vmm_a = variational_two_part_mm(docs_1, docs_2, chain, n_tables=1)
    vmm_b = variational_two_part_mm(docs_1, docs_2, chain, n_tables=2)

    assert vmm_a['total_archive_bytes'] < full_nash['total_archive_bytes'] - 400
    assert b'return_result = ' in vmm_a['entries'] and b'workgroup_id = ' in vmm_a['entries']
    assert b'retur' not in vmm_a['entries']
    assert vmm_a['certificate']['is_certified_nash_fixed_point'] is True
    assert vmm_b['is_certified_nash_fixed_point'] is True

    # Round-trip decode verification
    codes = BE.assign_canonical_codes(vmm_a['lengths'])
    pay, _ = BE.encode_bitstream(vmm_a['pieces'], codes)
    dec = BE.decode_bitstream(pay, len(all_docs), BE.build_decode_tree(codes))
    assert dec == all_docs


def test_codenet_untouched() -> None:
    out = subprocess.check_output(['git', '-C', str(CODENET_DIR), 'status', '--porcelain', '.'], text=True).strip()
    assert out == '', f'codenet-replication-v1 dirtied: {out}'


def main() -> None:
    test_certifier_catches_suboptimal_parse_and_polishes_to_zero_gap()
    print('  [PASS] Nash fixed-point certifier catches suboptimal parse and polishes to 0-bit gap')
    test_vmm_excises_absorbed_bpe_scaffolds_and_beats_prefix_stop()
    print('  [PASS] Variational Two-Part MM excises BPE scaffolds + middle bloat and round-trips')
    test_codenet_untouched()
    print('  [PASS] codenet-replication-v1 untouched')
    print('ALL rung3-vmm-subset-v1 unit tests PASSED.')


if __name__ == '__main__':
    main()
