#!/usr/bin/env python3
"""Unit and end-to-end equal-budget tests for `rung2-presearch-v1`.

Verifies:
  1. `raw_predictor.py` sees ONLY raw corpus bytes (no subprocess/engine/byte_encode),
     runs in milliseconds, and catches exact single-byte alphabet cliffs (`K < |Sigma_1| + |Sigma_2|`).
  2. End-to-end `evaluate_presearch_vs_oracle` with compiled `engine.c` + iterative bit-cost
     reparsing + exact canonical Huffman bitstream round-trip across all three winning regimes:
       - Regime A: small / homogeneous corpus pair -> `layout_hat == 'A'`, oracle `== 'A'`.
       - Regime B: bilingual code sharing ASCII characters & operators with divergent multi-byte
         keywords -> `layout_hat == 'B'`, oracle `== 'B'` (and outperforms naive 1-byte MI!).
       - Regime C: disjoint byte-alphabet / zero-overlap corpora at ample `K` -> `layout_hat == 'C'`,
         oracle `== 'C'` (and evaluates > 7 reparsed pairs under equal `limit_seconds` wall cap).
  3. Zero cross-layout leakage (`allow_union_floor == False`) and `codenet-replication-v1/`
     remains 100% clean.
"""
from __future__ import annotations

import ast
import json
import subprocess
import sys
from pathlib import Path

sys.dont_write_bytecode = True

HERE = Path(__file__).resolve().parent
CODENET_DIR = HERE.parent / 'codenet-replication-v1'
sys.path.insert(0, str(HERE))

import raw_predictor as RP  # noqa: E402
from equal_budget_eval import evaluate_presearch_vs_oracle  # noqa: E402


def test_raw_predictor_isolation_and_cliffs() -> None:
    # Verify via AST that raw_predictor imports neither subprocess nor byte_encode
    src = Path(RP.__file__).read_text(encoding='utf-8')
    tree = ast.parse(src)
    imported = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imported.add(alias.name.split('.')[0])
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module.split('.')[0])
    assert 'subprocess' not in imported, f'raw_predictor must never import subprocess: {imported}'
    assert 'byte_encode' not in imported, f'raw_predictor must never import byte_encode: {imported}'

    # Test CodeNet primary UTF-8 cliff (167 + 166 = 333 > 256 -> C infeasible at K=256)
    manifest = json.loads((CODENET_DIR / 'manifest.json').read_text(encoding='utf-8'))
    pairs = manifest['splits']['primary']['pairs']
    py_docs = [(CODENET_DIR / p['python']['path']).read_bytes() for p in pairs]
    js_docs = [(CODENET_DIR / p['javascript']['path']).read_bytes() for p in pairs]

    pred = RP.predict_presearch(py_docs, js_docs)
    assert pred['feasible'] is True
    assert pred['predictor_elapsed_ms'] < 250.0, f"predictor too slow: {pred['predictor_elapsed_ms']} ms"
    assert pred['layout_hat'] == 'B', pred
    assert pred['K_hat'] in (2048, 4096), pred

    c_256 = next(c for c in pred['candidates'] if c['layout'] == 'C' and c['K'] == 256)
    assert c_256['feasible'] is False
    assert '333' in str(c_256['reason'])


def test_regime_a_small_homogeneous_wins_end_to_end() -> None:
    # Homogeneous Python-like snippets split into two small groups: I(S; L) ~ 0 -> Design A wins, K=256 suffices
    base_snippets = [
        b'def compute_value(items, scale):\n    total = 0\n    for x in items:\n        total += x * scale\n    return total\n',
        b'def filter_positive(values, limit):\n    out = []\n    for v in values:\n        if 0 < v <= limit:\n            out.append(v)\n    return out\n',
        b'class Acc:\n    def __init__(self, start=0):\n        self.cur = start\n    def add(self, delta):\n        self.cur += delta\n        return self.cur\n',
    ]
    docs_1 = [base_snippets[i % 3] + f'# idx={i}\n'.encode('ascii') for i in range(12)]
    docs_2 = [base_snippets[(i + 1) % 3] + f'# idx={i}\n'.encode('ascii') for i in range(12)]

    res = evaluate_presearch_vs_oracle(
        docs_1, docs_2,
        label='regime-A-homogeneous',
        k_grid=(256, 512, 1024),
        arms=('greedy-entry', 'bpe'),
        limit_seconds=2.0,
        step=16,
    )
    assert res['prediction']['layout_hat'] == 'A', res['prediction']
    assert res['prediction']['K_hat'] == 256, res['prediction']
    assert res['oracle']['best_layout'] == 'A', res['oracle']
    assert res['metrics']['bytes_lost'] == 0, res['metrics']
    assert res['metrics']['search_seconds_saved_vs_grid'] > 0, res['metrics']
    assert res['prediction']['roundtrip_verified'] is True
    assert res['oracle']['roundtrip_verified'] is True


def test_regime_b_bilingual_shared_ascii_beats_naive_byte_mi() -> None:
    # Construct two languages with identical character frequencies (anagrammed keyword sets!)
    # so textbook 1-byte MI is ~0 (`naive_byte_mi_ablation` picks 'A'), while 4-byte keyword
    # divergence is large and shared operators/numbers favor shared dictionary + 2 tables ('B')!
    lang1_keywords = [b'def ', b'elif', b'self', b'None', b'pass', b'from', b'with', b'yield']
    # Exact character-multiset permutations / shared ASCII letters arranged into distinct keywords
    lang2_keywords = [b'fed ', b'file', b'fles', b'enoN', b'ssap', b'morf', b'htiw', b'dleiy']
    shared_ops = [b' = (x0 + y1) * 42;\n', b'    if (idx >= 16) { total += 1; }\n']

    docs_1 = []
    docs_2 = []
    for i in range(45):
        body1 = b''.join(
            lang1_keywords[(i + j) % len(lang1_keywords)] + shared_ops[(i + j) % 2]
            for j in range(16)
        )
        body2 = b''.join(
            lang2_keywords[(i + j) % len(lang2_keywords)] + shared_ops[(i + j) % 2]
            for j in range(16)
        )
        docs_1.append(body1)
        docs_2.append(body2)

    res = evaluate_presearch_vs_oracle(
        docs_1, docs_2,
        label='regime-B-anagram-keywords',
        k_grid=(256, 512, 1024),
        arms=('greedy-entry', 'bpe'),
        limit_seconds=3.0,
        step=16,
    )
    # Naive 1-byte MI sees near-zero single-byte divergence and falsely picks 'A'!
    assert res['naive_byte_mi_ablation']['layout_hat'] == 'A', res['naive_byte_mi_ablation']
    assert res['naive_byte_mi_ablation']['bytes_lost_vs_oracle'] > 50, res['naive_byte_mi_ablation']

    # Multi-scale raw predictor sees 4-gram divergence + shared operators and picks 'B', matching oracle!
    assert res['prediction']['layout_hat'] == 'B', res['prediction']
    assert res['oracle']['best_layout'] == 'B', res['oracle']
    assert abs(res['metrics']['pct_regret']) < 0.5, res['metrics']


def test_regime_c_disjoint_alphabets_wins_end_to_end() -> None:
    # Language 1 uses printable ASCII [0x20..0x7A]; Language 2 uses disjoint high bytes [0x80..0xDA]
    # Zero shared single bytes and zero shared substrings -> Design B wastes |D_1|+|D_2| dead table
    # slots while saving 0 shared dict bytes -> Design C strictly wins!
    ascii_phrases = [
        b'module alpha_kernel(input_stream, output_buffer) { return transform(input_stream); }\n',
        b'for (size_t idx = 0; idx < count; ++idx) { output_buffer[idx] = input_stream[idx] ^ 7; }\n',
    ]
    docs_1 = [
        b''.join(ascii_phrases[(i + j) % 2] for j in range(8)) + f'// {i}\n'.encode('ascii')
        for i in range(30)
    ]
    # Map every byte b in docs_1 into [0x80..0xFF] so alphabets are 100% disjoint
    docs_2 = [bytes(((b - 0x0A) % 96) + 0x80 for b in d) for d in docs_1]

    res = evaluate_presearch_vs_oracle(
        docs_1, docs_2,
        label='regime-C-disjoint-alphabets',
        k_grid=(256, 512, 1024),
        arms=('greedy-entry', 'bpe'),
        limit_seconds=3.0,
        step=16,
    )
    assert res['prediction']['layout_hat'] == 'C', res['prediction']
    assert res['oracle']['best_layout'] == 'C', res['oracle']
    assert res['oracle']['shared_wall_cap_sec'] == res['oracle']['separate_wall_cap_sec']
    assert res['oracle']['allow_union_floor'] is False
    # Verify exhaustive Design C Pareto evaluation checked >> 7 pairs!
    c_cells = [c for c in res['oracle_cells'] if c['layout'] == 'C' and c.get('feasible')]
    assert any(c['reparsed_pairs_evaluated'] > 7 for c in c_cells), c_cells
    assert abs(res['metrics']['pct_regret']) < 0.5, res['metrics']


def test_codenet_replication_dir_untouched() -> None:
    out = subprocess.check_output(
        ['git', '-C', str(CODENET_DIR), 'status', '--porcelain', '.'],
        text=True,
    ).strip()
    assert out == '', f'codenet-replication-v1 was dirtied: {out}'


def main() -> None:
    test_raw_predictor_isolation_and_cliffs()
    print('  [PASS] raw_predictor isolation and UTF-8 feasibility cliffs')
    test_regime_a_small_homogeneous_wins_end_to_end()
    print('  [PASS] Regime A (small/homogeneous -> Design A + compact K_hat) verified end-to-end')
    test_regime_b_bilingual_shared_ascii_beats_naive_byte_mi()
    print('  [PASS] Regime B (shared-ASCII divergent keywords -> Design B beats naive 1-byte MI) verified')
    test_regime_c_disjoint_alphabets_wins_end_to_end()
    print('  [PASS] Regime C (disjoint alphabets -> Design C wins under equal search budget, >7 pairs) verified')
    test_codenet_replication_dir_untouched()
    print('  [PASS] codenet-replication-v1 directory untouched')
    print('ALL rung2-presearch-v1 tests PASSED.')


if __name__ == '__main__':
    main()
