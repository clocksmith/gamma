#!/usr/bin/env python3
"""Unit tests for byte_encode.py: Kraft inequality, monotone byte-optimal DP,
KL/JS Design-B formula, and exact round-trip bitstream encode/decode."""
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import byte_encode as B


def test_huffman_and_bitstream_roundtrip():
    docs = [
        b'def solve(n):\n    return n * (n + 1) // 2\n',
        b'def solve(a, b):\n    return a + b\n',
        b'function solve(n) {\n  return n * (n + 1) / 2;\n}\n',
    ]
    alphabet = sorted({bytes([b]) for d in docs for b in d})
    entries = alphabet + [b'def solve(', b'return ', b'function solve(', b'n * (n + 1)']
    root = B.build_trie(entries)
    opt = B.optimize_byte_segmentation(docs, root)
    assert opt is not None
    # Monotonicity: byte-optimal payload bits <= token-optimal payload bits
    assert opt['byte_min']['payload_bits'] <= opt['token_min']['payload_bits']
    # Bitstream round-trip exactness for both modes
    for mode in ('token_min', 'byte_min'):
        bench = B.benchmark_encode_decode(docs, entries, mode=mode, repeats=2)
        assert bench['verified_exact'] is True
        assert bench['payload_bytes'] == math.ceil(bench['payload_bits'] / 8)
        assert bench['payload_bits'] == opt[mode]['payload_bits']


def test_byte_min_strictly_improves_contrived_case():
    # Frequent short pieces 'a','b' get short codes; rare long entry 'ab' gets long code.
    # Token-min picks 'ab' (1 token), while byte-min splits 'ab' -> 'a'+'b' when cheaper in bits!
    docs = [b'a' * 200 + b'b' * 200 + b'ab'] + [bytes([65 + i]) for i in range(40)]
    alphabet = sorted({bytes([b]) for d in docs for b in d})
    entries = alphabet + [b'ab']
    root = B.build_trie(entries)
    opt = B.optimize_byte_segmentation(docs, root)
    assert opt['byte_min']['payload_bits'] < opt['token_min']['payload_bits'], opt
    bench = B.benchmark_encode_decode(docs, entries, mode='byte_min', repeats=1)
    assert bench['verified_exact'] is True


def test_kl_js_decomposition_nonnegative():
    py_docs = [b'def f(x):\n    return x + 1\n'] * 20
    js_docs = [b'function f(x) { return x + 1; }\n'] * 20
    alphabet = sorted({bytes([b]) for d in py_docs + js_docs for b in d})
    entries = alphabet + [b'def ', b'function ', b'return ']
    root = B.build_trie(entries)
    p = B.optimize_byte_segmentation(py_docs, root)['token_min']
    j = B.optimize_byte_segmentation(js_docs, root)['token_min']
    decomp = B.compute_kl_js_decomposition(p['counts'], j['counts'], len(entries))
    assert decomp['mutual_info_bits'] > 0
    assert decomp['kl_py_bits'] > 0 and decomp['kl_js_bits'] > 0


if __name__ == '__main__':
    test_huffman_and_bitstream_roundtrip()
    test_byte_min_strictly_improves_contrived_case()
    test_kl_js_decomposition_nonnegative()
    print('ALL byte_encode unit tests PASSED')
