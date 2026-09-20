"""Lab-owned fixed-checkpoint numerical attribution with an original source closure."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
from gamma_enwiki9.evidence.artifacts import canonical_bytes, fingerprint, publish_immutable_artifact
from gamma_enwiki9.evidence.history import materialize
from gamma_enwiki9.execution.commands import CommandExecutor, PhaseLimits
from gamma_enwiki9.execution.memory import CgroupMemoryGuard
from gamma_enwiki9.types import BuildProfile,ExecutionContext,ResourceBudget


def run(root,output,experiment_path,closure_path,plan_path):
    experiment=json.loads(experiment_path.read_bytes());plan=json.loads(plan_path.read_bytes())
    for row in experiment['inputs']:
        if fingerprint(root/row['path'],root)['sha256']!=row['sha256'].removeprefix('sha256:'):raise ValueError('input changed: '+row['path'])
    for path,digest in plan['build_tools']:
        if hashlib.sha256(Path(path).read_bytes()).hexdigest()!=digest:raise ValueError('runtime/build tool changed')
    output.mkdir(parents=True,exist_ok=True);snapshot=output/'snapshot'
    materialize(root,json.loads(closure_path.read_bytes()),snapshot)
    workspace=output/'execution';workspace.mkdir()
    caps=plan['caps'];environment={'PATH':'/usr/bin:/bin','PYTHONPATH':str(snapshot/'src'),'PYTHONDONTWRITEBYTECODE':'1',
        'OMP_NUM_THREADS':'1','MKL_NUM_THREADS':'1','OPENBLAS_NUM_THREADS':'1','PYTHONHASHSEED':'0','LC_ALL':'C','TMPDIR':str(workspace)}
    context=ExecutionContext(experiment['experimentId'],snapshot,workspace,
        ResourceBudget(tuple(caps['cpus']),caps['memory_bytes'],caps['scratch_bytes'],caps['wall_seconds']),
        BuildProfile(tuple(plan['worker_command']),tuple(map(tuple,plan['build_tools']))),tuple(environment.items()))
    with CgroupMemoryGuard.current(caps['memory_bytes']) as guard:
        executor=CommandExecutor(context,resident_guard=guard)
        command=[*plan['worker_command'],'--root',str(snapshot),'--output',str(output/'numeric'),
                 '--plan',str(snapshot/plan_path.relative_to(root))]
        outcome,record=executor.run('fixed-checkpoint-attribution',command,
            PhaseLimits(1500,1510,plan['address_space_bytes'],caps['scratch_bytes']))
        if outcome.classification!='completed':raise RuntimeError('numeric attribution did not complete')
    comparison=json.loads((output/'numeric/comparison.json').read_bytes());comparison['execution']=record
    publish_immutable_artifact(output/'comparison.json',canonical_bytes(comparison)+b'\n')
    publish_immutable_artifact(output/'artifacts.json',canonical_bytes({'artifacts':[fingerprint(p,root) for p in sorted(output.rglob('*')) if p.is_file()]})+b'\n')
    print(json.dumps({k:{n:v[n] for n in ('delta_reference_bits','delta_native_bits','delta_mismatch_bits')} for k,v in comparison['fixtures'].items()}))


def main():
    parser=argparse.ArgumentParser()
    for name in ('root','output','experiment','closure','plan'):parser.add_argument('--'+name,type=Path,required=True)
    a=parser.parse_args();run(a.root.resolve(),a.output.resolve(),a.experiment.resolve(),a.closure.resolve(),a.plan.resolve())

if __name__=='__main__':main()
