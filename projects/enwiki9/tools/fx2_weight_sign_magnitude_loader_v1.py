#!/usr/bin/env python3
"""Emit isolated native GFX2SMG1 loading from authenticated adaptive sources."""
import argparse
import hashlib
import json
from pathlib import Path

LOADER_SHA256 = '7099d24019bb5aa18421f8521838ced8ffb31aef84bdb173c7ff4753e0c3834a'
DISPATCH_SHA256 = 'b03faaf7a313480523702af1f41965f1d54f3658800050377f5f06e46f7a81d3'


def replace_once(text, old, new):
    if text.count(old) != 1:
        raise ValueError('native source anchor is not unique: ' + old[:80])
    return text.replace(old, new)


def patch(source, kind='loader'):
    if kind not in ('loader', 'dispatch'):
        raise ValueError('unknown native source kind')
    expected = LOADER_SHA256 if kind == 'loader' else DISPATCH_SHA256
    if hashlib.sha256(source).hexdigest() != expected:
        raise ValueError('native ' + kind + ' parent differs')
    text = source.decode()
    if kind == 'dispatch':
        return replace_once(text,
            'std::memcmp(magic, "GFX2ADM1", 8) == 0)',
            'std::memcmp(magic, "GFX2ADM1", 8) == 0 ||\n'
            '                    std::memcmp(magic, "GFX2SMG1", 8) == 0)').encode()
    edits = [
        ('bool adaptive_counts = false) {',
         'bool adaptive_counts = false, bool sign_magnitude = false) {'),
        ('const bool track_histograms = marginal || bookkeeping || adaptive_counts;',
         'const bool track_histograms = marginal || bookkeeping || adaptive_counts || sign_magnitude;'),
        ('BinDecoder dec(r.p, r.left, marginal || adaptive_counts);',
         'BinDecoder dec(r.p, r.left, marginal || adaptive_counts || sign_magnitude);'),
        ('        uint32_t learned_total = 15;',
         '        uint32_t learned_total = 15;\n'
         '        std::array<uint32_t, 2> signs{{1, 1}};\n'
         '        if (sign_magnitude) {\n'
         '          // Even leaves embed eight magnitudes in the existing tree.\n'
         '          // Only its top three levels are decoded; odd leaves stay zero.\n'
         '          learned.fill(0);\n'
         '          learned[0] = 1;\n'
         '          for (unsigned m = 1; m < 8; ++m) learned[2 * m] = 2;\n'
         '        }'),
        ('          if (adaptive_counts) fixed = gamma_fixed_tree(learned);\n'
         '          const uint32_t symbol = dec.decode_tree((marginal || adaptive_counts) ? fixed.data() : m.int4.data(), 4, !(marginal || adaptive_counts));',
         '          uint32_t symbol;\n'
         '          if (sign_magnitude) {\n'
         '            fixed = gamma_fixed_tree(learned);\n'
         '            const unsigned magnitude = dec.decode_tree(fixed.data(), 3, false);\n'
         '            const uint32_t total = signs[0] + signs[1];\n'
         '            uint16_t probability = uint16_t(std::max<uint64_t>(1, std::min<uint64_t>(2047,\n'
         '                (uint64_t(2048) * signs[0] + total / 2) / total)));\n'
         '            const unsigned sign = magnitude ? dec.decode_bit(&probability, false) : 0;\n'
         '            symbol = sign ? 7 - magnitude : 7 + magnitude;\n'
         '          } else {\n'
         '            if (adaptive_counts) fixed = gamma_fixed_tree(learned);\n'
         '            symbol = dec.decode_tree((marginal || adaptive_counts) ? fixed.data() : m.int4.data(), 4, !(marginal || adaptive_counts));\n'
         '          }'),
        ('          if (adaptive_counts) {\n            ++learned[symbol];',
         '          if (sign_magnitude && symbol != 7) {\n'
         '            ++signs[symbol < 7];\n'
         '            if (signs[0] + signs[1] >= 65536)\n'
         '              for (auto& count : signs) count = (count + 1) / 2;\n'
         '          }\n'
         '          if (adaptive_counts || sign_magnitude) {\n'
         '            const unsigned index = sign_magnitude ? 2 * (symbol < 7 ? 7 - symbol : symbol - 7) : symbol;\n'
         '            ++learned[index];'),
        ('if (marginal || adaptive_counts) dec.gamma_check.finish();',
         'if (marginal || adaptive_counts || sign_magnitude) dec.gamma_check.finish();'),
        ("const char selected = adaptive_counts ? 'A'", "const char selected = sign_magnitude ? 'S' : adaptive_counts ? 'A'"),
        ('(marginal || adaptive_counts) ? 1 : 0)',
         '(marginal || adaptive_counts || sign_magnitude) ? 1 : 0)'),
        ('std::memcmp(prefix, "GFX2ADM1", 8) == 0)',
         'std::memcmp(prefix, "GFX2ADM1", 8) == 0 || std::memcmp(prefix, "GFX2SMG1", 8) == 0)'),
        ('  if (std::memcmp(magic, "GFX2ADM1", 8) == 0) return load_v2(r, path, false, true);',
         '  if (std::memcmp(magic, "GFX2SMG1", 8) == 0) return load_v2(r, path, false, false, true);\n'
         '  if (std::memcmp(magic, "GFX2ADM1", 8) == 0) return load_v2(r, path, false, true);'),
    ]
    for old, new in edits:
        text = replace_once(text, old, new)
    return ('// Gamma exact sign/magnitude loader successor; retain upstream GPLv3 LICENSE.\n' + text).encode()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--kind', choices=('loader', 'dispatch'), default='loader')
    parser.add_argument('--source', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    data = patch(args.source.read_bytes(), args.kind)
    with args.output.open('xb') as stream:
        stream.write(data)
    print(json.dumps(dict(path=str(args.output), bytes=len(data),
                          sha256=hashlib.sha256(data).hexdigest(), objective_credit_bytes=0)))


if __name__ == '__main__':
    main()
