#!/usr/bin/env python3
"""Complete-model magnitude/sign comparison; preserves the tested width-carry runner procedure."""
import argparse
import json
import os
from pathlib import Path
import time
from fx2_weight_adaptive_loader_gate_v1 import phase
from fx2_weight_neighbor_model_audit_v1 import binding

ROOT = Path(__file__).resolve().parents[1]
PLAN = ROOT / 'operations/provenance/fx2_weight_sign_magnitude_model_v1_plan.json'


def verify(rows):
    for row in rows:
        actual = binding(ROOT / row['path'])
        if any(actual[key] != row[key] for key in ('bytes', 'sha256')):
            raise ValueError('changed input: ' + row['path'])


def run(plan, output, bound_inputs=()):
    verify(bound_inputs)
    verify(list(plan['models'].values()) + list(plan['executables'].values()))
    output = Path(output)
    output.mkdir(parents=True, exist_ok=False)
    (output / 'tmp').mkdir()
    deadline = time.monotonic() + plan['bounds']['elapsed_seconds']
    original = ROOT / plan['models']['original']['path']
    probe = ROOT / plan['executables']['treatment']['path']
    parent = ROOT / plan['executables']['parent']['path']
    arms = {}

    def invoke(name, binary, mode, source, target):
        phase(output, name, [binary, mode, source, target], plan['bounds'], deadline)
        return binding(target)

    for arm in ('P', 'K', 'D'):
        archive, restored, repeat = [output / (arm + suffix) for suffix in ('.model', '.original', '.repeat')]
        a = invoke(arm+'-encode', probe, arm, original, archive)
        d = invoke(arm+'-restore', probe, 'restore', archive, restored)
        r = invoke(arm+'-repeat', probe, arm, original, repeat)
        if original.read_bytes() != restored.read_bytes():
            raise ValueError('exact original-model inverse differs: ' + arm)
        if archive.read_bytes() != repeat.read_bytes():
            raise ValueError('deterministic repeat differs: ' + arm)
        arms[arm] = dict(archive=a, restored=d, repeat=r)
    independent = output / 'independent-parent.model'
    reference = invoke('independent-parent', parent, 'D', original, independent)
    if independent.read_bytes() != (ROOT / plan['models']['parent']['path']).read_bytes():
        raise ValueError('selected adaptive parent differs')
    if any((output / (a+'.model')).read_bytes() != independent.read_bytes() for a in ('P', 'K')):
        raise ValueError('P/K or unchanged parent differs')
    verify(list(plan['models'].values()) + list(plan['executables'].values()))
    saved = arms['P']['archive']['bytes'] - arms['D']['archive']['bytes']
    added = plan['executables']['treatment']['bytes'] - plan['executables']['parent']['bytes']
    result = dict(schema='gamma.enwiki9.sign-magnitude-model.v1', arms=arms,
                  independent_parent=reference, model_bytes_saved=saved,
                  comparison_executable_added_bytes=added,
                  model_plus_comparison_executable_bytes_saved=saved-added,
                  selected_parent_identity=True, all_exact_inverses=True,
                  all_deterministic_repeats=True, phase_count=10,
                  scope='Complete model container restoration; no native inference or full-corpus archive.',
                  probability_streams_measured=False, complete_package_bytes=None,
                  full_corpus_score_bytes=None, objective_credit_bytes=0)
    verify(bound_inputs)
    partial=output/'receipt.partial'
    partial.write_text(json.dumps(result,indent=2)+'\n')
    partial.rename(output/'receipt.json')
    return result


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ('inputs','admission','output'):
        parser.add_argument('--'+name,required=True)
    args=parser.parse_args()
    plan=json.loads(PLAN.read_text())
    admission=json.loads(Path(args.admission).read_text())
    if admission.get('id') != plan['id'] or admission.get('admitted') is not True:
        raise ValueError('matching admission required')
    if sorted(os.sched_getaffinity(0)) != plan['bounds']['cpu_set']:
        raise ValueError('CPU assignment differs')
    if Path(args.output).resolve() != (ROOT / plan['output']).resolve():
        raise ValueError('output differs from frozen plan')
    inputs=json.loads(Path(args.inputs).read_text())
    result=run(plan,args.output,inputs['inputs'])
    print(json.dumps({k:result[k] for k in ('model_bytes_saved','comparison_executable_added_bytes','model_plus_comparison_executable_bytes_saved','phase_count')}))


if __name__ == '__main__':
    main()
