"""Rebuild and exercise a fully counted FX2 core package in a restricted runtime."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import zipfile
from gamma_enwiki9.evidence.artifacts import canonical_bytes, fingerprint, publish_immutable_artifact
from gamma_enwiki9.evidence.history import materialize
from gamma_enwiki9.execution.commands import CommandExecutor, PhaseLimits
from gamma_enwiki9.execution.memory import CgroupMemoryGuard
from gamma_enwiki9.types import BuildProfile, ExecutionContext, ResourceBudget
from .fx2_training_capture import source_members


def write(p,v):publish_immutable_artifact(p,canonical_bytes(v)+b'\n')


def source_package(root,plan,destination):
    members={'native/'+n:b for n,b in source_members(root/plan['native_source_zip']).items()}
    members['native/models/6m-q4-fp32.tfwc2']=(root/plan['weights']).read_bytes()
    members['envelope.cpp']=(root/'src/gamma_enwiki9/packaging/fx2_envelope.cpp').read_bytes()
    members['pack.py']=(root/'src/gamma_enwiki9/packaging/fx2_envelope.py').read_bytes()+b'\nif __name__ == "__main__":\n    assemble(Path("envelope"),Path("native/cmix"),Path("native/dictionary/english.dic"),Path("native/models/6m-q4-fp32.tfwc2"),Path("comp9"))\n'
    # Exact frozen make arguments are quoted once in the counted build recipe.
    import shlex
    native=' '.join(shlex.quote(x) for x in plan['compile_command'][1:])
    members['makefile']=(f'all: comp9\n\ncomp9:\n\t$(MAKE) -C native {native}\n\t/usr/bin/g++ -std=c++17 -Os -s envelope.cpp -o envelope\n\tpython3 pack.py\n\nclean:\n\t$(MAKE) -C native clean\n\trm -f comp9 envelope\n').encode()
    members['GAMMA-LICENSE']=(root/plan['gamma_license']).read_bytes()
    for label,path in plan['notices'].items():members['notices/'+label]=(root/path).read_bytes()
    members['README']=(
        'Gamma FX2 core delivery, bounded native profile. Build: make\n'
        'Compress: ./comp9 INPUT (creates archive9). Decode: ./archive9 (creates enwik9).\n'
        'Both refuse output replacement. No external assets or command options at decoding.\n'
        'This preserves the tested native -c/-d frontend, not the upstream full-enwik9 reorder/split pipeline.\n'
        'Includes unmodified trimmed native code, selected packed weights, dictionary and Gamma envelope.\n'
        'Native source: native/LICENSE and original headers; Gamma envelope: GAMMA-LICENSE.\n'
        'Additional original attribution texts retained under notices/.\n'
        'Model permission and CUDA-derived math licensing remain unresolved; no submission eligibility claim.\n'
        'Native binary requires Linux x86-64-v3 and standard ELF runtime libraries.\n'
        'FNV-1a64 is an internal corruption check, not cryptographic authentication.\n').encode()
    with zipfile.ZipFile(destination,'x',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as archive:
        for name,data in sorted(members.items()):
            info=zipfile.ZipInfo(name,(1980,1,1,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED;info.external_attr=0o100644<<16
            archive.writestr(info,data)
    return members


def sandbox(runtime,work,command,raw=None):
    cmd=[runtime['bwrap']['resolved_path'],'--unshare-all','--die-with-parent','--new-session','--clearenv',
         '--dir','/runtime','--dir','/runtime/lib','--dir','/lib64','--proc','/proc','--dev','/dev',
         '--bind',str(work),'/work','--setenv','LD_LIBRARY_PATH','/runtime/lib','--setenv','LC_ALL','C','--chdir','/work']
    for name,row in sorted(runtime['providers'].items()):cmd+=['--ro-bind',row['resolved_path'],'/runtime/lib/'+name]
    cmd+=['--symlink','/runtime/lib/ld-linux-x86-64.so.2','/lib64/ld-linux-x86-64.so.2']
    if raw is not None:cmd+=['--ro-bind',str(raw),'/input']
    return cmd+['--',*command]


def run(root,output,experiment_path,closure_path,plan_path):
    plan=json.loads(plan_path.read_bytes());experiment=json.loads(experiment_path.read_bytes())
    for row in experiment['inputs']:
        if fingerprint(root/row['path'],root)['sha256']!=row['sha256'].removeprefix('sha256:'):raise ValueError('bound input changed')
    output.mkdir(parents=True,exist_ok=True);snapshot=output/'snapshot';materialize(root,json.loads(closure_path.read_bytes()),snapshot)
    runtime=json.loads((snapshot/plan['runtime']).read_bytes())
    for row in [runtime['bwrap'],*runtime['providers'].values()]:
        if hashlib.sha256(Path(row['resolved_path']).read_bytes()).hexdigest()!=row['sha256']:raise ValueError('runtime provider changed')
    for path,digest in plan['build_tools']:
        if hashlib.sha256(Path(path).read_bytes()).hexdigest()!=digest:raise ValueError('build tool changed')
    source=output/'comp9.zip';members=source_package(snapshot,plan,source)
    write(output/'source-members.json',{'files':{n:{'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()} for n,b in members.items()}})
    native=output/'build';native.mkdir()
    for name,data in members.items():
        p=native/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data)
    caps=plan['caps'];env={'PATH':'/usr/bin:/bin','LC_ALL':'C','TMPDIR':str(native),'PYTHONDONTWRITEBYTECODE':'1'}
    context=ExecutionContext(experiment['experimentId'],snapshot,native,
        ResourceBudget(tuple(caps['cpus']),caps['memory_bytes'],caps['scratch_bytes'],caps['wall_seconds']),
        BuildProfile(tuple(plan['compile_command']),tuple(map(tuple,plan['build_tools']))),tuple(env.items()))
    records=[]
    with CgroupMemoryGuard.current(caps['memory_bytes']) as guard:
        executor=CommandExecutor(context,resident_guard=guard)
        def phase(name,command,seconds=360):
            outcome,record=executor.run(name,command,PhaseLimits(seconds,seconds+10,plan['address_space_bytes'],caps['scratch_bytes']))
            records.append(record)
            if outcome.classification!='completed':raise RuntimeError('package phase failed: '+name)
        phase('source-build',['/usr/bin/make','-j1'])
        if fingerprint(native/'native/cmix',root)['sha256']!=fingerprint(snapshot/plan['native_binary'],root)['sha256']:
            raise ValueError('delivery rebuilt a different codec')
        shutil.copyfile(native/'comp9',output/'comp9');(output/'comp9').chmod(0o755)
        phase('source-clean',['/usr/bin/make','clean'],30);phase('source-repeat',['/usr/bin/make','-j1'])
        if (native/'comp9').read_bytes()!=(output/'comp9').read_bytes():raise ValueError('complete compressor build is nondeterministic')
        raw=snapshot/plan['raw'];expected=snapshot/plan['archive']
        for name in ('encode','decode','repeat'):
            work=output/name;work.mkdir()
            if name=='decode':
                shutil.copyfile(output/'encode/archive9',work/'archive9');(work/'archive9').chmod(0o755)
                command=sandbox(runtime,work,['./archive9'])
            else:
                shutil.copyfile(output/'comp9',work/'comp9');(work/'comp9').chmod(0o755)
                command=sandbox(runtime,work,['./comp9','/input'],raw)
            phase('isolated-'+name,command)
            if list(work.glob('.gamma-fx2-*')):raise ValueError('owned scratch not cleaned')
        if (output/'decode/enwik9').read_bytes()!=raw.read_bytes():raise ValueError('no-argument inverse differs')
        if (output/'encode/archive9').read_bytes()!=(output/'repeat/archive9').read_bytes():raise ValueError('whole archive repeat differs')
        import struct
        archived=(output/'encode/archive9').read_bytes();footer=struct.unpack('<8s8Q',archived[-72:]);h=footer[1:]
        payload=archived[sum(h[1:5]):sum(h[1:6])]
        if payload!=expected.read_bytes():raise ValueError('packaging changed the finite native archive')
        result={'schema':'gamma.enwiki9.fx2-core-delivery.v1','candidate_id':experiment['experimentId'],
            'selected_checkpoint':plan['selected_checkpoint'],'population':plan['population'],
            'source_zip':fingerprint(source,root),'compressor':fingerprint(output/'comp9',root),
            'archive':fingerprint(output/'encode/archive9',root),'raw':fingerprint(output/'decode/enwik9',root),
            'payload_bytes':len(payload),'model_bytes_per_copy':h[4],'dictionary_bytes_per_copy':h[3],
            'wrapper_bytes_per_copy':h[1],'codec_bytes_per_copy':h[2],'footer_bytes_per_copy':72,
            'executable_form_bytes':(output/'comp9').stat().st_size+len(archived),
            'source_zip_form_bytes':source.stat().st_size+len(archived),'required_extra_option_bytes':0,
            'alternative_forms_not_added':True,'source_rebuild_and_repeat_exact':True,'archive_repeat_exact':True,
            'no_argument_inverse_exact':True,'native_payload_unchanged':True,'runtime_providers':runtime['providers'],
            'decode_mounts':['archive9 in writable isolated /work','five explicitly pinned standard ELF runtime providers','kernel /proc and /dev'],
            'decode_repository_or_corpus_access':False,'commands':records,'objective_credit_bytes':0,'full_corpus_score_bytes':None,
            'eligibility_complete':False,'gaps':['Full1GB archive not produced','This measured core frontend is not the upstream split/reorder submission frontend',
                'Weights permission and CUDA-derived math license unresolved','Committee runtime-library exemption/accounting unconfirmed',
                'No isolated machine calibration or full-corpus resource certificate']}
        write(output/'comparison.json',result)
    write(output/'artifacts.json',{'artifacts':[fingerprint(p,root) for p in sorted(output.rglob('*')) if p.is_file()]})
    return result


def main():
    parser=argparse.ArgumentParser()
    for n in ('root','output','experiment','closure','plan'):parser.add_argument('--'+n,type=Path,required=True)
    a=parser.parse_args();r=run(a.root.resolve(),a.output.resolve(),a.experiment.resolve(),a.closure.resolve(),a.plan.resolve())
    print(json.dumps({k:r[k] for k in ('executable_form_bytes','source_zip_form_bytes','no_argument_inverse_exact')}))

if __name__=='__main__':main()
