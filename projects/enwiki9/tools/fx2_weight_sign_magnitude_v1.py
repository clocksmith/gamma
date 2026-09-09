#!/usr/bin/env python3
"""Materialize a separate exact weight factorization from an authenticated parent."""
import hashlib
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
PARENT=ROOT/'lib/fx2_weight_adaptive_marginal_v1.hpp'
PARENT_SHA256='3264d084d8c9d7511ec119b23500deae622eb0bb74c700d8c0ad62698674e71d'


def render(source):
    if hashlib.sha256(source).hexdigest()!=PARENT_SHA256:
        raise ValueError('sealed adaptive parent differs')
    text=source.decode()
    start=text.index('struct AdaptiveCounts {')
    end=text.index('\ninline Document decode_adaptive',start)
    text=text[:start]+text[end:]
    edits=[
        ('#include "fx2_weight_format_v1.hpp"','#include "fx2_weight_sign_magnitude_v1.hpp"',1),
        ('kAdaptive','kSignMagnitude',4),('GFX2ADM1','GFX2SMG1',1),
        ('inline Document decode_adaptive(const Bytes& input)',
         'inline Document decode_sign_magnitude(const Bytes& input, SignMagnitudeWitness witness=nullptr)',1),
        ('inline Bytes encode_adaptive(const Document& document)',
         'inline Bytes encode_sign_magnitude(const Document& document, SignMagnitudeWitness witness=nullptr)',1),
        ('AdaptiveCounts counts;','SignMagnitudeCounts counts;',2),
        ('          auto tree = fixed_tree(counts.row);\n'
         '          const auto value = uint8_t(decoder.tree(tree.data(), 4, false));',
         '          auto mt=SignMagnitudeCounts::tree(counts.magnitude);\n'
         '          const unsigned m=decoder.tree(mt.data(),3,false);\n'
         '          auto st=SignMagnitudeCounts::tree(counts.sign);\n'
         '          const unsigned s=m ? decoder.tree(st.data(),1,false) : 0;\n'
         '          const auto value=uint8_t(s ? 7-m : 7+m);',1),
        ('        auto tree = fixed_tree(counts.row);\n'
         '        encoder.tree(tree.data(), 4, value, false);',
         '        const unsigned m=value<7 ? 7-value : value-7;\n'
         '        auto mt=SignMagnitudeCounts::tree(counts.magnitude);\n'
         '        encoder.tree(mt.data(),3,m,false);\n'
         '        auto st=SignMagnitudeCounts::tree(counts.sign);\n'
         '        if (m) encoder.tree(st.data(),1,value<7,false);',1),
        ('counts.observe(value);','if (witness) witness(counts,value);\n          counts.observe(value);',2),
    ]
    for old,new,count in edits:
        if text.count(old)!=count:raise ValueError('source anchor differs: '+old)
        text=text.replace(old,new)
    return text


def materialize(output):
    with Path(output).open('x') as stream:stream.write(render(PARENT.read_bytes()))


if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('output')
    materialize(p.parse_args().output)
