#!/usr/bin/env python3
"""Materialize one source-bound exact-model mutation; never edit its parent."""
import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PARENT = ROOT / 'lib/fx2_weight_adaptive_marginal_v1.hpp'
PARENT_SHA256 = '3264d084d8c9d7511ec119b23500deae622eb0bb74c700d8c0ad62698674e71d'


def render(source):
    if hashlib.sha256(source).hexdigest() != PARENT_SHA256:
        raise ValueError('sealed adaptive parent differs')
    text = source.decode()
    for old, new, count in (
        ('counts reset at each tensor.', 'counts persist by decoded row width.', 1),
        ('#include "fx2_weight_format_v1.hpp"',
         '#include "fx2_weight_format_v1.hpp"\n#include <map>', 1),
        ('kAdaptive', 'kWidthCarry', 4),
        ('GFX2ADM1', 'GFX2ACW1', 1),
        ('AdaptiveCounts', 'WidthCounts', 4),
        ('inline Document decode_adaptive(const Bytes& input)',
         'using WidthWitness = void (*)(uint32_t, const Histogram&, uint8_t);\n'
         'inline Document decode_width_carry(const Bytes& input, WidthWitness witness = nullptr)', 1),
        ('inline Bytes encode_adaptive(const Document& document)',
         'inline Bytes encode_width_carry(const Document& document, WidthWitness witness = nullptr)', 1),
        ('  Models models;', '  Models models;\n  std::map<uint32_t, WidthCounts> count_bank;', 2),
        ('WidthCounts counts;',
         'WidthCounts& counts = count_bank[tensor.shape.empty() ? 1 : tensor.shape.back()];', 2),
        ('counts.observe(value);',
         'if (witness) witness(tensor.shape.empty() ? 1 : tensor.shape.back(), counts.row, value);\n'
         '          counts.observe(value);', 2),
    ):
        if text.count(old) != count:
            raise ValueError('source anchor count differs: ' + old)
        text = text.replace(old, new)
    return text


def materialize(output):
    with Path(output).open('x') as stream:
        stream.write(render(PARENT.read_bytes()))


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('output')
    materialize(parser.parse_args().output)
