"""Lab-owned P/A/J complete development trajectories; no optimization or selection."""
from __future__ import annotations
import argparse
from dataclasses import replace
import hashlib
import json
from pathlib import Path
from gamma_enwiki9.evidence.artifacts import canonical_bytes, fingerprint, publish_immutable_artifact
from gamma_enwiki9.evidence.history import materialize
from gamma_enwiki9.execution.commands import CommandExecutor, PhaseLimits
from gamma_enwiki9.execution.memory import CgroupMemoryGuard
from gamma_enwiki9.types import BuildProfile, ExecutionContext, ResourceBudget
from .fx2_trajectory_native_v1 import adapt
from .fx2_trajectory_costs_v1 import analyze, differences, target_mask


def write(path, value):
    publish_immutable_artifact(path, canonical_bytes(value)+b'\n')


def same(left, right):
    return fingerprint(left, left.parent)['sha256'] == fingerprint(right, right.parent)['sha256']


def run(root, output, experiment_path, closure_path, plan_path):
    experiment = json.loads(experiment_path.read_bytes())
    plan = json.loads(plan_path.read_bytes())
    for row in experiment['inputs']:
        if fingerprint(root/row['path'], root)['sha256'] != row['sha256'].removeprefix('sha256:'):
            raise ValueError('bound input changed: '+row['path'])
    for path, digest in plan['build_tools']:
        if hashlib.sha256(Path(path).read_bytes()).hexdigest() != digest:
            raise ValueError('build tool changed: '+path)
    output.mkdir(parents=True, exist_ok=True)
    snapshot = output/'snapshot'
    materialize(root, json.loads(closure_path.read_bytes()), snapshot)
    native = output/'native'; native.mkdir()
    members, receipt = adapt(snapshot/plan['source_zip'], snapshot/plan['observer'])
    write(output/'adapter.json', {'changes': receipt})
    for name, data in members.items():
        path = native/name; path.parent.mkdir(parents=True, exist_ok=True); path.write_bytes(data)
    tokens = (snapshot/plan['tokens']).read_bytes()
    selected = target_mask(tokens, plan['window_starts'])
    if len(selected) != 512:
        raise ValueError('frozen training mask differs')
    write(output/'mask.json', {'tokens': fingerprint(snapshot/plan['tokens'], root),
        'target_ranges': [[s+513,s+641] for s in plan['window_starts']],
        'prediction_ranges': [[s+512,s+640] for s in plan['window_starts']],
        'target_count': len(selected), 'coordinate': 'Zero-based modeled token targets, paired to preceding neural prediction row; no partition resets.'})
    caps = plan['caps']
    env = {'PATH':'/usr/bin:/bin','PYTHONPATH':str(snapshot/'src'),'PYTHONDONTWRITEBYTECODE':'1',
           'OMP_NUM_THREADS':'1','OPENBLAS_NUM_THREADS':'1','LC_ALL':'C','TMPDIR':str(native)}
    context = ExecutionContext(experiment['experimentId'], snapshot, native,
        ResourceBudget(tuple(caps['cpus']),caps['memory_bytes'],caps['scratch_bytes'],caps['wall_seconds']),
        BuildProfile(tuple(plan['compile_command']),tuple(map(tuple,plan['build_tools']))),tuple(env.items()))
    commands = []; measurements = {}; archives = {}; identities = {}
    with CgroupMemoryGuard.current(caps['memory_bytes']) as guard:
        def phase(name, argv, capture=None):
            current = replace(context, environment=tuple({**env, **({'GAMMA_ATTRIBUTION_CAPTURE':str(capture)} if capture else {})}.items()))
            executor = CommandExecutor(current, resident_guard=guard)
            timed = ['/usr/bin/time','-f','{"maximum_process_rss_kib":%M,"user_seconds":%U,"system_seconds":%S,"exit_status":%x}',
                     '-o',str(native/(name+'.rusage.json')),*argv]
            outcome, record = executor.run(name,timed,PhaseLimits(240,260,plan['address_space_bytes'],caps['scratch_bytes']))
            commands.append(record); write(output/(name+'.command.json'),record)
            scratch = native/'ppm.temp'
            if scratch.exists():
                if scratch.is_symlink() or not scratch.is_file():
                    raise ValueError('unexpected scratch ownership')
                scratch.unlink()
            if outcome.classification != 'completed':
                raise RuntimeError('phase failed: '+name)
            print(json.dumps({'phase':name,'elapsed_seconds':record['elapsed_seconds']}),flush=True)
        phase('build',plan['compile_command'])
        for arm in ('P','A','J'):
            model = snapshot/plan['models'][arm]
            raw = snapshot/plan['raw']; archive = native/(arm+'.arc')
            restored = native/(arm+'.raw'); repeat = native/(arm+'.repeat.arc')
            for action, mode, source, destination in [('encode','-c',raw,archive),('decode','-d',archive,restored),('repeat','-c',restored,repeat)]:
                capture = native/(arm+'-'+action)
                phase(arm+'-'+action,[str(native/'cmix'),mode,str(native/'dictionary/english.dic'),str(source),str(destination),'--transformer',str(model)],capture)
                if action != 'encode':
                    for suffix in ('.bits','.neural','.tokens','.priors'):
                        if not same(Path(str(capture)+suffix),native/(arm+'-encode'+suffix)):
                            raise ValueError('encode/decode/repeat capture differs: '+arm+suffix)
            if not same(archive,repeat) or not same(raw,restored):
                raise ValueError('native inverse or repeat differs')
            if not same(archive,snapshot/plan['archives'][arm]):
                raise ValueError('observer changed retained native archive: '+arm)
            calls = native/(arm+'-window-reference');calls.mkdir()
            for wi, source in enumerate(plan['training_predictions'][arm]):
                (calls/f'w{wi}.f32').write_bytes((snapshot/source).read_bytes())
            measurements[arm] = analyze(native/(arm+'-encode'),tokens,plan['window_starts'],250000,calls)
            measurements[arm]['priors_equal_retained_training_capture'] = same(native/(arm+'-encode.priors'),snapshot/plan['priors'])
            archives[arm] = archive.stat().st_size
            identities[arm] = {'archive':fingerprint(archive,root),'raw':fingerprint(restored,root),
                'repeat':fingerprint(repeat,root),'model':fingerprint(model,root),
                'original_archive_exact':True,'inverse_exact':True,'repeat_exact':True,'capture_repeat_exact':True}
        result = {'schema':'gamma.enwiki9.training-trajectory-attribution.v1','candidate_id':experiment['experimentId'],
            'measurements':measurements,'differences':differences(measurements,archives),'archives':identities,
            'commands':commands,'attribution_complete':True,'training_performed':False,'checkpoint_selection_performed':False,
            'objective_credit_bytes':0,'full_corpus_score_bytes':None,'limits':plan['limits'],
            'neural_semantics':'Actual native FP32 truth probabilities before output half-rounding and guard; no neural cost assigned to targets without a prior native step.',
            'final_semantics':'Actual integer p at arithmetic coder input, truth cost -log2(p/65536) or -log2((65536-p)/65536).',
            'residual_semantics':'8*(archive_X-archive_P)-DeltaF(all); measured coding/framing residual, not a universal bound or mixer causal loss.'}
        write(output/'comparison.json',result)
    write(output/'artifacts.json',{'artifacts':[fingerprint(p,root) for p in sorted(output.rglob('*')) if p.is_file()]})
    return result


def main():
    parser=argparse.ArgumentParser()
    for key in ('root','output','experiment','closure','plan'):
        parser.add_argument('--'+key,type=Path,required=True)
    a=parser.parse_args()
    run(*(getattr(a,k).resolve() for k in ('root','output','experiment','closure','plan')))


if __name__=='__main__':
    main()
