"""Bound lossless weight coding, fresh offline rebuild and paid component delta."""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil

from gamma_enwiki9.adapters.lexth11c_build import sandbox, write
from gamma_enwiki9.evidence.artifacts import fingerprint
from gamma_enwiki9.execution.commands import CommandExecutor, PhaseLimits
from gamma_enwiki9.execution.memory import CgroupMemoryGuard
from gamma_enwiki9.types import BuildProfile, ExecutionContext, ResourceBudget

def run(root, output, experiment, plan):
    exp=json.loads(experiment.read_bytes());cfg=json.loads(plan.read_bytes())
    bound={'path':experiment.relative_to(root).as_posix(),
           'sha256':'sha256:'+hashlib.sha256(experiment.read_bytes()).hexdigest()}
    if json.loads(os.environ['GAMMA_ENWIKI9_EXPERIMENT_JSON'])!=bound:
        raise ValueError('lab experiment binding differs')
    for row in exp['inputs']:
        if fingerprint(root/row['path'],root)['sha256']!=row['sha256'].removeprefix('sha256:'):
            raise ValueError('input differs: '+row['path'])
    for row in cfg['files']:
        if row.get('symlink') is not None:
            if os.readlink(root/row['path'])!=row['symlink']:raise ValueError('symlink differs')
        elif fingerprint(root/row['path'],root)['sha256']!=row['sha256']:
            raise ValueError('tool/source differs: '+row['path'])
    for row in cfg['host_providers']:
        p=Path(row['path'])
        if fingerprint(p,p.parent)['sha256']!=row['sha256']:raise ValueError('host provider differs')
    caps=cfg['caps'];work=output/'work';work.mkdir()
    ctx=ExecutionContext(exp['experimentId'],root,output,
        ResourceBudget(tuple(caps['cpus']),caps['memory_bytes'],caps['scratch_bytes'],caps['wall_seconds']),
        BuildProfile((),()),(('PATH','/usr/bin:/bin'),('LC_ALL','C')))
    diagnostic=root/'src/gamma_enwiki9/adapters/lexth11c_repack_v1'
    entry=None
    def command(argv):
        cmd=sandbox(root,work,argv)
        if entry is not None:
            index=cmd.index('/entry');cmd[index-1]=str(entry)
        index=cmd.index('--')
        cmd[index:index]=['--ro-bind',str(diagnostic),'/repack']
        return cmd
    phases=[];comparisons={};component=None;ok=True
    with CgroupMemoryGuard.current(caps['memory_bytes']) as guard:
        executor=CommandExecutor(ctx,resident_guard=guard)
        def phase(name,argv,seconds=3600):
            nonlocal ok
            outcome,rec=executor.run(name,command(argv),PhaseLimits(seconds,seconds,68719476736,caps['scratch_bytes']))
            phases.append(rec);ok=ok and outcome.classification=='completed';return ok
        write(output/'launch.json',{'experiment':bound,'caps':caps,'qualification':False,
            'source_derivation':'Original source copied; only format4 compressed decoder replaced; model repacked bit-exactly.'})
        phase('encoder-build',['clang++-17','-O2','-std=c++17','-I/entry/cpp_infer/src',
            '/repack/repack.cpp','/entry/cpp_infer/src/weights_io.cpp','-o','/work/repack'])
        if ok:phase('repack',['./repack','/entry/models/lex_h1_run11.tfwc2',
            '/work/new.tfwc4','/work/original.raw','/work/repacked.raw'])
        if ok:
            ok=fingerprint(work/'original.raw',root)['sha256']==fingerprint(work/'repacked.raw',root)['sha256']
        if ok:
            entry=work/'entry'
            shutil.copytree(root/'external/lexth11c-campaign/release-source/lexth11c-src',entry)
            shutil.copyfile(diagnostic/'weights_io_compressed.cpp',entry/'cpp_infer/src/weights_io_compressed.cpp')
            shutil.copyfile(work/'new.tfwc4',entry/'models/lex_h1_run11.tfwc2')
            phase('build',['bash','/entry/build.sh'],caps['wall_seconds'])
        if ok:
            parent=root/'results/lexth11c_rebuild_control_q0_v1/work/cmix'
            shutil.copyfile(parent,work/'parent');(work/'parent').chmod(0o755)
            shutil.copyfile(root/'external/lexth11c-campaign/release-source/lexth11c-src/models/lex_h1_run11.tfwc2',work/'parent.weights')
            for arm,binary,weights in [('P','./parent','parent.weights'),('A','./cmix','new.tfwc4'),('R','./cmix','new.tfwc4')]:
                if not phase(arm,[binary,'-n','--transformer','/work/'+weights,'--save-transformer-probs',
                    '/work/'+arm+'.probs','/entry/prof_input/input','/work/'+arm+'.arc']):break
            if ok:phase('inverse',['./cmix','-d','--transformer','/work/new.tfwc4','/work/A.arc','/work/restored'])
            if ok:
                ok=fingerprint(work/'restored',root)['sha256']==fingerprint(entry/'prof_input/input',root)['sha256']
                for suffix in ['arc','probs']:
                    refs={arm:fingerprint(work/(arm+'.'+suffix),root) for arm in ['P','A','R']}
                    equal=len({r['sha256'] for r in refs.values()})==1
                    comparisons[suffix]={'files':refs,'byte_equal':equal};ok=ok and equal
            parent_run=root/'results/lexth11c_rebuild_control_q0_v1/work/src/run'
            child_run=work/'src/run'
            if (child_run/'cmix_orig').exists():
                pw=(parent_run/'comp_tfweights').stat().st_size;cw=(child_run/'comp_tfweights').stat().st_size
                ps=(parent_run/'cmix_orig').stat().st_size;cs=(child_run/'cmix_orig').stat().st_size
                component={'parent_weight_bytes':pw,'child_weight_bytes':cw,'saving_per_copy':pw-cw,
                    'parent_stub_bytes':ps,'child_stub_bytes':cs,'counted_implementation_delta_bytes':2*(cs-ps),
                    'net_component_saving_bytes':2*(pw-cw)-2*(cs-ps),
                    'full_payload_unchanged_verified':False,'full_corpus_score_bytes':None}
                for name in ['comp_dict','comp_order']:
                    component[name+'_byte_equal']=fingerprint(parent_run/name,root)['sha256']==fingerprint(child_run/name,root)['sha256']
                    ok=ok and component[name+'_byte_equal']
    artifacts={}
    for rel in ['new.tfwc4','original.raw','repacked.raw','cmix','src/run/cmix_orig','restored']:
        p=work/rel
        if p.is_file():artifacts[rel]=fingerprint(p,root)
    result={'schema':'gamma.enwiki9.lossless-repack-result.v1','experiment':bound,
        'status':'control_pass' if ok else 'failed','phases':phases,'comparisons':comparisons,
        'artifacts':artifacts,'component':component,'qualification':False,'objective_credit_bytes':0,
        'control_scope':'Complete raw50051-byte tagged profiling fixture; original tensor bits; produced packed model and both stub copies.',
        'full_corpus_score_bytes':None}
    write(output/'result.json',result);print(json.dumps(result),flush=True);return 0 if ok else 1

def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ['root','output','experiment','plan']:p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args();return run(*(getattr(a,n).resolve() for n in ['root','output','experiment','plan']))
