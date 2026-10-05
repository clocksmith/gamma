"""Offline tagged donor rebuild with an isolated, pinned compiler overlay."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import os
import shutil

from gamma_enwiki9.evidence.artifacts import fingerprint, canonical_bytes, publish_immutable_artifact
from gamma_enwiki9.execution.commands import CommandExecutor, PhaseLimits
from gamma_enwiki9.execution.memory import CgroupMemoryGuard
from gamma_enwiki9.types import BuildProfile, ExecutionContext, ResourceBudget

def sandbox(root: Path, work: Path, command: list[str]) -> list[str]:
    base = root / 'external/lexth11c-campaign'
    return ['/usr/bin/bwrap', '--unshare-all', '--die-with-parent', '--new-session', '--clearenv',
            '--ro-bind', '/usr', '/usr', '--ro-bind', '/etc', '/etc',
            '--ro-bind', '/usr/bin', '/host-bin', '--ro-bind', '/usr/lib', '/host-usrlib',
            '--ro-bind', '/usr/lib/x86_64-linux-gnu', '/host-libs',
            '--ro-bind', str(base/'toolchain'), '/toolchain',
            '--ro-bind', str(base/'overlay'), '/overlay',
            '--ro-bind', str(base/'overlay/bin'), '/usr/bin',
            '--ro-bind', str(base/'overlay/usrlib'), '/usr/lib',
            '--ro-bind', str(base/'toolchain/usr/include/c++'), '/usr/include/c++',
            '--ro-bind', str(base/'toolchain/usr/include/x86_64-linux-gnu/c++'), '/usr/include/x86_64-linux-gnu/c++',
            '--ro-bind', str(base/'toolchain/usr/local/bin'), '/usr/local/bin',
            '--symlink', 'usr/bin', '/bin', '--symlink', 'usr/lib', '/lib', '--symlink', 'usr/lib64', '/lib64',
            '--ro-bind', str(base/'release-source/lexth11c-src'), '/entry',
            '--ro-bind', str(root/'external/lexth11c-release-assets/cmix'), '/released-cmix',
            '--bind', str(work), '/work', '--proc', '/proc', '--dev', '/dev', '--tmpfs', '/tmp',
            '--setenv', 'PATH', '/usr/local/bin:/usr/bin:/bin',
            '--setenv', 'LD_LIBRARY_PATH', '/usr/lib/x86_64-linux-gnu',
            '--setenv', 'LC_ALL', 'C', '--setenv', 'MAKEFLAGS', '-l4', '--chdir', '/work', '--', *command]

def write(path: Path, value):
    publish_immutable_artifact(path, canonical_bytes(value)+b'\n')

def run(root, output, experiment, plan):
    exp = json.loads(experiment.read_bytes())
    bound = {'path': experiment.relative_to(root).as_posix(),
             'sha256': 'sha256:'+hashlib.sha256(experiment.read_bytes()).hexdigest()}
    if json.loads(os.environ['GAMMA_ENWIKI9_EXPERIMENT_JSON']) != bound:
        raise ValueError('lab experiment binding differs')
    for row in exp['inputs']:
        if fingerprint(root/row['path'], root)['sha256'] != row['sha256'].removeprefix('sha256:'):
            raise ValueError('input differs: '+row['path'])
    cfg = json.loads(plan.read_bytes())
    for row in cfg['files']:
        if row.get('symlink') is not None:
            if os.readlink(root/row['path']) != row['symlink']: raise ValueError('symlink differs')
        elif fingerprint(root/row['path'], root)['sha256'] != row['sha256']:
            raise ValueError('tool/source differs: '+row['path'])
    for row in cfg['host_providers']:
        p = Path(row['path'])
        if fingerprint(p, p.parent)['sha256'] != row['sha256']: raise ValueError('host provider differs')
    caps = cfg['caps']
    ctx = ExecutionContext(exp['experimentId'], root, output,
        ResourceBudget(tuple(caps['cpus']), caps['memory_bytes'], caps['scratch_bytes'], caps['wall_seconds']),
        BuildProfile((), ()), (('PATH','/usr/bin:/bin'), ('LC_ALL','C')))
    phases = []
    work = output/'work';work.mkdir()
    with CgroupMemoryGuard.current(caps['memory_bytes']) as guard:
        executor = CommandExecutor(ctx, resident_guard=guard)
        shutil.copyfile(root/'external/lexth11c-release-assets/cmix',work/'released-cmix')
        (work/'released-cmix').chmod(0o755)
        built=root/'results/lexth11c_rebuild_control_q0_v1/work/cmix'
        shutil.copyfile(built,work/'cmix');(work/'cmix').chmod(0o755)
        write(output/'launch.json', {'experiment':bound,'caps':caps,'qualification':False,
              'reuse_build':'results/lexth11c_rebuild_control_q0_v1/result.json'})
        ok=True
        for arm,binary in [('released','./released-cmix'),('rebuilt','./cmix'),('repeat','./cmix')]:
            command=sandbox(root,work,[binary,'-n','--transformer','/entry/models/lex_h1_run11.tfwc2',
                '--save-transformer-probs',f'/work/{arm}.probs','/entry/prof_input/input',f'/work/{arm}.arc'])
            outcome,rec=executor.run(arm,command,PhaseLimits(3600,3600,68719476736,caps['scratch_bytes']))
            phases.append(rec);ok=ok and outcome.classification=='completed'
            if not ok:break
        if ok:
            command=sandbox(root,work,['./cmix','-d','--transformer','/entry/models/lex_h1_run11.tfwc2',
                '/work/rebuilt.arc','/work/restored'])
            outcome,rec=executor.run('inverse',command,PhaseLimits(3600,3600,68719476736,caps['scratch_bytes']))
            phases.append(rec)
            fixture=root/'external/lexth11c-campaign/release-source/lexth11c-src/prof_input/input'
            ok=outcome.classification=='completed' and fingerprint(work/'restored',root)['sha256']==fingerprint(fixture,root)['sha256']
        comparisons = {}
        if ok:
            for suffix in ['probs','arc']:
                refs = {arm:fingerprint(work/f'{arm}.{suffix}',root) for arm in ['released','rebuilt','repeat']}
                comparisons[suffix] = {'files':refs,'byte_equal':len({r['sha256'] for r in refs.values()})==1}
                ok = ok and comparisons[suffix]['byte_equal']
    comp = fingerprint(work/'cmix',root) if (work/'cmix').exists() else None
    result = {'schema':'gamma.enwiki9.external-donor-build.v1','experiment':bound,
              'status':'control_pass' if ok else 'failed','compressor':comp,'phases':phases,'comparisons':comparisons,
              'released_binary_equal':bool(comp and comp['sha256']=='e77c9a659b31c1358368da0ef49a8683080197b9b14a11b1e6e80a43c94cb463'),
              'complete_score_reproduced':False,'full_corpus_score_bytes':None,'objective_credit_bytes':0,
              'qualification':False,'control_scope':'Tagged raw50KB profiling fixture; full1G recompression remains unexecuted.'}
    write(output/'result.json',result)
    print(json.dumps(result),flush=True)
    return 0 if ok else 1

def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ['root','output','experiment','plan']:p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args();return run(*(getattr(a,n).resolve() for n in ['root','output','experiment','plan']))
