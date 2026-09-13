#!/usr/bin/env python3
"""Create an exact source adapter for one fixed KDA reset experiment."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PARENT = 'results/fx2_cmix_transformer_static_vocab_fixture50051_q0_v1/'

def build():
    changes = {
        'cpp_infer/src/opt/model_opt.cpp': [
            ('#include "model_opt.h"', '#include "model_opt.h"\n#include "gamma-kda-carry.h"'),
            ('  void begin(int64_t rope_position_offset) {\n    for (int i = 0; i < 9; i++) kda_layer_reset(kst[i]);',
             '  void begin(int64_t rope_position_offset) {\n    const char selected = gamma_kda_carry::arm();\n    for (int i = 0; i < 9; i++) gamma_kda_carry::reset(kst[i], selected);'),
            ('    rope_off = rope_position_offset;\n  }',
             '    rope_off = rope_position_offset;\n    gamma_kda_carry::audit(kst, t, rope_off);\n  }')]
    }
    coder = json.loads((ROOT/'operations/provenance/public_fx2_argmax_native_adapter_v1.json').read_text())
    for row in coder['files']:
        if row['source_path'] in ('src/coder/encoder.cpp', 'src/coder/decoder.cpp'):
            changes[row['source_path']] = [(r['before'], r['after']) for r in row['replacements']]
    package = json.loads((ROOT/PARENT/'package.json').read_text())
    expected = {r['path']: r['sha256'].removeprefix('sha256:') for r in package['source_members']}
    files = []
    for name, replacements in changes.items():
        path = PARENT+'work/'+name
        raw = (ROOT/path).read_bytes()
        digest = hashlib.sha256(raw).hexdigest()
        if digest != expected[path]: raise ValueError('preimage differs: '+name)
        text = raw.decode()
        for before, after in replacements:
            if text.count(before) != 1: raise ValueError('ambiguous anchor: '+name)
            text = text.replace(before, after)
        files.append(dict(source_path=name, source_sha256=digest, source_bytes=len(raw),
                          patched_sha256=hashlib.sha256(text.encode()).hexdigest(), patched_bytes=len(text.encode()),
                          replacements=[dict(before=a, after=b) for a,b in replacements]))
    added=[]
    for source,target in [('lib/fx2_kda_carry_v1.hpp','cpp_infer/src/opt/gamma-kda-carry.h'),
                          ('tools/fx2_coder_trace_v1.hpp','src/coder/gamma-coder-trace.h')]:
        raw=(ROOT/source).read_bytes()
        added.append(dict(source=dict(path=source,bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest()),target=target))
    return dict(schema='gamma.enwiki9.exact-source-adapter-multi.v1',files=files,added_files=added,
                scope='Only KDA article/piece reset law changes. All other model updates, weights, frontend and coder remain fixed.')

if __name__ == '__main__':
    import argparse
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True)
    args=p.parse_args()
    with args.output.open('x') as f: json.dump(build(),f,indent=2);f.write('\n')
