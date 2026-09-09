#!/usr/bin/env python3
"""Emit an isolated adaptive loader from its authenticated, immutable parent."""
import argparse
import hashlib
import json
from pathlib import Path

PARENT_SHA256 = 'ea32c4e69e8f630c3aac19faeb28d81ebdd51a6b712791b70669c9ca6e14e466'


def patch(source):
    if hashlib.sha256(source).hexdigest() != PARENT_SHA256:
        raise ValueError('native loader parent differs')
    text = source.decode()
    def replace(old, new):
        nonlocal text
        if text.count(old) != 1:
            raise ValueError('native loader edit is not unique: ' + old[:80])
        text = text.replace(old, new)
    replace('WeightsFile load_v2(Reader& r, const char* path, bool marginal = false) {',
            'WeightsFile load_v2(Reader& r, const char* path, bool marginal = false, bool adaptive_counts = false) {')
    replace('const bool track_histograms = marginal || bookkeeping;',
            'const bool track_histograms = marginal || bookkeeping || adaptive_counts;')
    replace('BinDecoder dec(r.p, r.left, marginal);',
            'BinDecoder dec(r.p, r.left, marginal || adaptive_counts);')
    replace('        GammaHistogram actual{};',
            '        GammaHistogram actual{}, learned{};\n        learned.fill(1);\n        uint32_t learned_total = 15;')
    replace('          const uint32_t symbol = dec.decode_tree(marginal ? fixed.data() : m.int4.data(), 4, !marginal);',
            '          if (adaptive_counts) fixed = gamma_fixed_tree(learned);\n'
            '          const uint32_t symbol = dec.decode_tree((marginal || adaptive_counts) ? fixed.data() : m.int4.data(), 4, !(marginal || adaptive_counts));')
    replace('          out[k] = int8_t(int(symbol) - 7);',
            '          if (adaptive_counts) {\n'
            '            ++learned[symbol];\n'
            '            if (++learned_total >= 65536) {\n'
            '              learned_total = 0;\n'
            '              for (auto& count : learned) { count = (count + 1) / 2; learned_total += count; }\n'
            '            }\n'
            '          }\n'
            '          out[k] = int8_t(int(symbol) - 7);')
    replace('    dec.gamma_check.finish();\n  }\n  const char selected = marginal',
            '  }\n  if (marginal || adaptive_counts) dec.gamma_check.finish();\n  const char selected = adaptive_counts ? \'A\' : marginal')
    replace('marginal ? size_t(65) + gamma.records.size() * 64 : size_t(0), marginal ? 1 : 0)',
            'marginal ? size_t(65) + gamma.records.size() * 64 : size_t(0), (marginal || adaptive_counts) ? 1 : 0)')
    replace('if (std::memcmp(prefix, "GFX2MAR1", 8) == 0) die("%s: marginal file exceeds bound", path);',
            'if (std::memcmp(prefix, "GFX2MAR1", 8) == 0 || std::memcmp(prefix, "GFX2ADM1", 8) == 0) die("%s: Gamma model file exceeds bound", path);')
    replace('  if (std::memcmp(magic, "GFX2MAR1", 8) == 0) return load_v2(r, path, true);',
            '  if (std::memcmp(magic, "GFX2ADM1", 8) == 0) return load_v2(r, path, false, true);\n'
            '  if (std::memcmp(magic, "GFX2MAR1", 8) == 0) return load_v2(r, path, true);')
    return ('// Gamma adaptive marginal successor. Preserve upstream GPLv3 LICENSE.\n'
            '// Only per-tensor INT4 counts and new-format admission change.\n' + text).encode()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', required=True)
    parser.add_argument('--output', required=True)
    args = parser.parse_args()
    output = patch(Path(args.source).read_bytes())
    with Path(args.output).open('xb') as stream:
        stream.write(output)
    print(json.dumps(dict(path=args.output, bytes=len(output), sha256=hashlib.sha256(output).hexdigest(),
                          parent_sha256=PARENT_SHA256, objective_credit_bytes=0)))


if __name__ == '__main__':
    main()
