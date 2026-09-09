#!/usr/bin/env python3
"""Bounded complete-model comparison with exact independent restoration."""
import argparse
import json
import os
from pathlib import Path
import resource
import subprocess
import time
from fx2_weight_neighbor_model_audit_v1 import binding

ROOT = Path(__file__).resolve().parents[1]


def run(plan, output, probe, fixed):
    output = Path(output)
    output.mkdir(parents=True, exist_ok=False)
    deadline = time.monotonic() + plan['bounds']['elapsed_seconds']
    commands, arms = [], {}
    bounds = plan['bounds']
    original = binding(ROOT / plan['model']['path'])

    def phase(name, binary, mode, source, target):
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise TimeoutError('aggregate elapsed stop')
        def limits():
            for key, value in ((resource.RLIMIT_AS, bounds['address_space_bytes']),
                               (resource.RLIMIT_CPU, bounds['cpu_seconds_per_phase']),
                               (resource.RLIMIT_FSIZE, bounds['per_file_bytes'])):
                resource.setrlimit(key, (value, value))
        cmd = list(map(str, [binary, mode, source, target]))
        before = resource.getrusage(resource.RUSAGE_CHILDREN)
        started = time.monotonic()
        with (output / (name + '.stdout')).open('xb') as stdout, (output / (name + '.stderr')).open('xb') as stderr:
            child = subprocess.run(cmd, stdout=stdout, stderr=stderr, preexec_fn=limits,
                                   timeout=min(remaining, bounds['phase_elapsed_seconds']))
        after = resource.getrusage(resource.RUSAGE_CHILDREN)
        row = dict(name=name, command=cmd, returncode=child.returncode,
                   elapsed_seconds=time.monotonic()-started,
                   cpu_seconds=after.ru_utime+after.ru_stime-before.ru_utime-before.ru_stime,
                   cumulative_child_peak_rss_kib=after.ru_maxrss)
        commands.append(row)
        with (output/'commands.jsonl').open('a') as stream:
            stream.write(json.dumps(row)+'\n')
        if child.returncode:
            raise ValueError('phase failed: '+name)
        if sum(p.stat().st_blocks*512 for p in output.rglob('*') if p.is_file()) > bounds['scratch_bytes']:
            raise ValueError('scratch stop')
        return binding(target)

    for arm in ('P','K','D'):
        archive, restored, repeat = [output/(arm+suffix) for suffix in ('.model','.original','.repeat')]
        a = phase(arm+'-encode',probe,arm,original['path'],archive)
        d = phase(arm+'-restore',probe,'restore',archive,restored)
        r = phase(arm+'-repeat',probe,arm,original['path'],repeat)
        if any(original[k] != d[k] or a[k] != r[k] for k in ('bytes','sha256')):
            raise ValueError('exact inverse or repeat differs: '+arm)
        arms[arm] = dict(archive=a, restored=d, repeat=r)
    reference = phase('fixed-only-P',fixed,'P',original['path'],output/'fixed.model')
    for key in ('bytes','sha256'):
        if not (reference[key] == arms['P']['archive'][key] == arms['K']['archive'][key] == plan['selected_parent'][key]):
            raise ValueError('selected fixed parent differs')
    inventory = dict(fixed=binding(fixed), adaptive=binding(probe))
    model_saved = arms['P']['archive']['bytes'] - arms['D']['archive']['bytes']
    executable_added = inventory['adaptive']['bytes'] - inventory['fixed']['bytes']
    result = dict(schema='gamma.enwiki9.adaptive-marginal-model.v1', arms=arms, executable_inventory=inventory,
                  model_bytes_saved=model_saved, comparison_executable_added_bytes=executable_added,
                  model_plus_comparison_executable_bytes_saved=model_saved-executable_added,
                  independently_restored=True, deterministic_repeats=True, selected_parent_identity=True,
                  phase_count=len(commands), complete_package_bytes=None, full_corpus_score_bytes=None,
                  objective_credit_bytes=0)
    temporary=output/'receipt.partial'
    temporary.write_text(json.dumps(result,indent=2)+'\n')
    temporary.rename(output/'receipt.json')
    return result


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ('inputs','admission','output','probe','fixed'):
        parser.add_argument('--'+name,required=True)
    args=parser.parse_args()
    plan=json.loads((ROOT/'operations/provenance/fx2_weight_adaptive_marginal_model_v1_plan.json').read_text())
    admission=json.loads(Path(args.admission).read_text())
    if admission.get('id') != plan['id'] or admission.get('admitted') is not True:
        raise ValueError('matching admission required')
    if sorted(os.sched_getaffinity(0)) != plan['bounds']['cpu_set']:
        raise ValueError('CPU assignment differs')
    inputs=json.loads(Path(args.inputs).read_text())
    for row in inputs['inputs']+[plan['model'],plan['selected_parent']]:
        actual=binding(ROOT/row['path'])
        if any(actual[k]!=row[k] for k in ('bytes','sha256')):
            raise ValueError('changed input: '+row['path'])
    for key in ('probe','fixed'):
        actual=binding(getattr(args,key))
        if any(actual[k]!=admission[key][k] for k in ('bytes','sha256')):
            raise ValueError('changed executable: '+key)
    result=run(plan,args.output,args.probe,args.fixed)
    print(json.dumps({k:result[k] for k in ('model_bytes_saved','comparison_executable_added_bytes','model_plus_comparison_executable_bytes_saved','phase_count')}))


if __name__=='__main__':
    main()
