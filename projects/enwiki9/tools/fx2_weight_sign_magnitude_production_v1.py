#!/usr/bin/env python3
"""Reuse the measured production gate for exact sign/magnitude integration."""
import argparse
import copy
import hashlib
import json
import os
from pathlib import Path
import time
import fx2_weight_adaptive_dispatch_gate_v2 as production
from fx2_weight_adaptive_loader_gate_v1 import phase
from fx2_weight_neighbor_model_audit_v1 import binding
from fx2_weight_sign_magnitude_loader_v1 import patch

ROOT = Path(__file__).resolve().parents[1]
PLAN = ROOT / 'operations/provenance/fx2_weight_sign_magnitude_production_v1_plan.json'


def run(plan, inputs, output):
    output.mkdir(exist_ok=False)
    (output / 'tmp').mkdir()
    deadline = time.monotonic() + plan['bounds']['elapsed_seconds']
    reports = []
    for label, model in [('P', 'parent'), ('D', 'adaptive'), ('D-repeat', 'adaptive')]:
        stdout = phase(output, 'tensors-' + label,
                       [ROOT / plan['tensor_comparator']['path'],
                        ROOT / plan['models']['original']['path'],
                        ROOT / plan['models'][model]['path']],
                       plan['bounds'], deadline, ROOT)
        report = json.loads(stdout)
        if not (report['exact_byte_comparison'] and report['tensor_count'] == 434
                and report['payload_bytes'] == 39588806
                and report['reference_digest_hex'] == report['target_digest_hex']):
            raise ValueError('trained tensor comparison differs')
        if reports and report['target_digest_hex'] != reports[0]['target_digest_hex']:
            raise ValueError('trained tensor repeat differs')
        reports.append(report)
    # Reuse the immutable matched-build procedure and its failure controls.
    # The inherited interface calls the treatment model "adaptive" and names
    # parent outputs "fixed". The outer receipt records their exact SMG/ADM roles.
    remaining = deadline - time.monotonic()
    if remaining <= 0:
        raise TimeoutError('aggregate elapsed stop')
    effective = copy.deepcopy(plan)
    effective['bounds']['elapsed_seconds'] = remaining
    original_patch = production.patch
    try:
        production.patch = lambda source: patch(source, 'dispatch')
        inner = production.run(effective, inputs, output / 'production')
    finally:
        production.patch = original_patch
    production.verify(plan, inputs)
    if time.monotonic() > deadline:
        raise TimeoutError('aggregate elapsed stop')
    if sum(p.stat().st_blocks * 512 for p in output.rglob('*') if p.is_file()) > plan['bounds']['scratch_bytes']:
        raise ValueError('combined scratch stop')
    result = dict(schema='gamma.enwiki9.sign-magnitude-production.v1',
                  id=plan['id'], status='passed', tensor_reports=reports,
                  production_receipt=binding(output / 'production/receipt.json'),
                  model_roles=dict(original='FX2TFWC2', parent='GFX2ADM1', adaptive='GFX2SMG1'),
                  inherited_output_labels={'P-fixed': 'P-adaptive-parent', 'D-fixed': 'D-adaptive-parent',
                                           'D-adaptive': 'D-sign-magnitude'},
                  accounting={k: inner[k] for k in ('model_delta_per_copy', 'binary_delta_per_copy',
                              'raw_source_delta', 'runtime_pair_delta',
                              'source_compressor_plus_decoder_delta', 'option_delta_bytes')},
                  complete_package_bytes=None, full_corpus_score_bytes=None, objective_credit_bytes=0)
    with (output / 'receipt.json').open('x') as stream:
        json.dump(result, stream, indent=2)
        stream.write('\n')
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('inputs', 'admission'):
        parser.add_argument('--' + name, required=True, type=Path)
    args = parser.parse_args()
    plan = json.loads(PLAN.read_text())
    inputs = json.loads(args.inputs.read_text())
    admission = json.loads(args.admission.read_text())
    if (admission.get('id') != plan['id'] or admission.get('admitted') is not True
            or admission.get('plan_sha256') != hashlib.sha256(PLAN.read_bytes()).hexdigest()
            or admission.get('inputs_sha256') != hashlib.sha256(args.inputs.read_bytes()).hexdigest()):
        raise ValueError('matching source-bound admission required')
    if sorted(os.sched_getaffinity(0)) != plan['bounds']['cpu_set']:
        raise ValueError('CPU assignment differs')
    production.verify(plan, inputs)
    result = run(plan, inputs, ROOT / plan['output'])
    print(json.dumps(result['accounting']))


if __name__ == '__main__':
    main()
