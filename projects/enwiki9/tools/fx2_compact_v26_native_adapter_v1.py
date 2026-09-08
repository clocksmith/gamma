#!/usr/bin/env python3
"""Exact source adapter selecting original, copy-control or compact FXCM."""
import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PARENT = 'results/fx2_cmix_transformer_static_vocab_fixture50051_q0_v1/'
FORGE = 'results/forge_parent_source_audit_v1/source-tree/'
EXPECTED = {
    'src/predictor.cpp': '0b79f43644daee942c9cb6da18fa464f0eb0185b6fc7ffc43cde703808fe537e',
    'src/predictor.h': '348d3924fc4e1f4890d0332b0f33ba9591afa6ee06971b9a9bdeaa376b41f458',
}
ADDITIONS = {
    'lib/forge_fxcm_raw_adapter_v2.hpp': 'src/forge_fxcm_raw_adapter_v2.hpp',
    'lib/fxcm_model_bridge_v1.hpp': 'src/fxcm_model_bridge_v1.hpp',
    FORGE+'src/models/fxcm_v26.cpp': 'src/models/fxcm_v26.cpp',
    FORGE+'src/models/fxcm_v26.h': 'src/models/fxcm_v26.h',
    FORGE+'src/profile-timer.h': 'src/profile-timer.h',
    FORGE+'LICENSE': 'FORGE-LICENSE',
    FORGE+'THIRD-PARTY-NOTICES.md': 'FORGE-THIRD-PARTY-NOTICES.md',
}


def digest(data):
    return hashlib.sha256(data).hexdigest()


def build_adapter(root=ROOT):
    rows = []
    replacements = {
        'src/predictor.h': [
            ('#include "models/fxcmv1.h"', '''#include "fxcm_model_bridge_v1.hpp"
#if GAMMA_FXCM_ARM == 2
#include "models/fxcm_v26.h"
using GammaFxcmModel = gamma_fxcm_bridge::Raw<FXCMV26,403>;
#elif GAMMA_FXCM_ARM == 1
#include "models/fxcmv1.h"
using GammaFxcmModel = gamma_fxcm_bridge::Copy<FXCM>;
#elif GAMMA_FXCM_ARM == 0
#include "models/fxcmv1.h"
using GammaFxcmModel = FXCM;
#else
#error "GAMMA_FXCM_ARM must be 0, 1 or 2"
#endif'''),
            ('std::optional<FXCM> fxcm_model_', 'std::optional<GammaFxcmModel> fxcm_model_')],
        'src/predictor.cpp': [
            ('  fxcm_model_.emplace();', '''  fxcm_model_.emplace();
  constexpr unsigned gamma_outputs = GAMMA_FXCM_ARM == 2 ? 403 : 431;
  if (fxcm_model_->NumOutputs() != gamma_outputs) Fail("Gamma FXCM output count differs");
  std::fprintf(stderr, "Gamma FXCM arm=%c outputs=%u\\n", "PKD"[GAMMA_FXCM_ARM], gamma_outputs);''')],
    }
    for name, changes in replacements.items():
        raw = (root / PARENT / 'work' / name).read_bytes()
        if digest(raw) != EXPECTED[name]:
            raise ValueError('native preimage changed: ' + name)
        text = raw.decode()
        for before, after in changes:
            if text.count(before) != 1:
                raise ValueError('ambiguous adapter anchor: ' + name)
            text = text.replace(before, after)
        rows.append(dict(source_path=name, source_sha256=digest(raw), source_bytes=len(raw),
                         patched_sha256=digest(text.encode()), patched_bytes=len(text.encode()),
                         replacements=[dict(before=a, after=b) for a,b in changes]))
    added = []
    audit = json.loads((root / 'operations/provenance/forge_parent_source_audit_v1_plan.json').read_text())
    pinned = {row['path']: row['sha256'] for row in audit['source_tree']}
    for source, target in ADDITIONS.items():
        raw = (root / source).read_bytes()
        if source.startswith(FORGE) and digest(raw) != pinned[source]:
            raise ValueError('forge source changed: ' + source)
        added.append(dict(source=dict(path=source, bytes=len(raw), sha256=digest(raw)), target=target))
    return dict(schema='gamma.enwiki9.exact-source-adapter-multi.v1',
                adapter_id='fx2_compact_v26_native_v1', files=rows, added_files=added,
                boundary='P keeps FXCM; K copies the same floats; D maps compact403 raw outputs exactly. Transformer/frontend/update order stay unchanged.',
                scope='Source materialization only; native inversion and full predictor state remain unproved.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    value = build_adapter()
    with args.output.open('x') as stream:
        json.dump(value, stream, indent=2)
        stream.write('\n')


if __name__ == '__main__':
    main()
