#!/usr/bin/env python3
"""Measure a lean native deployment against original source using shared guards."""
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import zipfile

ROOT=Path(__file__).resolve().parents[1]
ID='fx2_wrt_support_deploy_fixture_v1'
ENGINE='tools/fx2_compact_v26_fixture50051_q0_v1.py'
ENGINE_SHA='dad1c194b6c4fa0a6f35d9848cb0ec6550065b37ec231a6dfdd6560d0989a6be'
ADAPTER='operations/provenance/fx2_wrt_support_deploy_adapter_v1.json'
PRIOR_D='results/fx2_wrt_support_fixture50051_q0_v1/work/D/archive'


def write_bundle(path,work,files,options):
    with zipfile.ZipFile(path,'x',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as z:
        for name,data in [(str(p.relative_to(work)),p.read_bytes()) for p in files]+[('invocation-and-build.txt',options.encode())]:
            info=zipfile.ZipInfo(name,date_time=(1980,1,1,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED;info.create_system=3;info.external_attr=0o100644<<16
            z.writestr(info,data,compresslevel=9)


def engine():
    if hashlib.sha256((ROOT/ENGINE).read_bytes()).hexdigest()!=ENGINE_SHA:raise ValueError('engine source changed')
    spec=importlib.util.spec_from_file_location('deploy_engine',ROOT/ENGINE)
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);m.ID=ID
    return m


def execute(g):
    m=engine();package=json.loads(g.buffers[m.PARENT+'package.json']);raw=g.buffers[m.PARENT+'work/prof_input/input'];rows={}
    m.require(len(raw)==50051 and hashlib.sha256(raw).hexdigest()==m.RAW_SHA,'raw identity differs')
    for arm in ('P','D'):
        work=g.work/arm
        for row in package['source_members']+package['runtime_members']:
            if row['path'].endswith('/cmix'):continue
            target=work/row['path'].removeprefix(m.PARENT+'work/')
            if not target.exists():g.copy(row['path'],target)
        if arm=='D':
            g.adapter(ADAPTER,work)
            for row in json.loads(g.buffers[ADAPTER])['added_files']:g.copy(row['source']['path'],work/row['target'])
        (work/'prof_input/input').unlink()
        files=sorted(p for p in work.rglob('*') if p.is_file());sources=[g.artifact(p) for p in files]
        sealed={p:m.sha(p) for p in files}
        g.run(arm+'-compile',['/usr/bin/make','-j1','cmix','CC=/usr/bin/g++','CPPFLAGS_PART-THAT-SHOULD-BE-FAST='+m.FLAGS+' -O3','CPPFLAGS_PART-THAT-CAN-BE-SLOW='+m.FLAGS+' -Os'],180,work=work)
        binary=g.artifact(work/'cmix');g.binaries[str(work/'cmix')]=binary['sha256']
        binary_bytes=(work/'cmix').read_bytes()
        m.require(all(tag not in binary_bytes for tag in (b'Gamma WRT arm=',b'Gamma coder trace:',b'GAMMA_FX2_WRT_TRACE',b'GAMMA_FX2_CODER_TRACE')),'diagnostic code remains in deployment binary')
        g.run(arm+'-disassemble',['/usr/bin/objdump','-d','--insn-width=16','cmix'],30,work=work)
        asm=(g.result/(arm+'-disassemble.stdout')).read_text()
        m.require(not re.search(r'\b(?:v?(?:rcp|rsqrt)(?:14|28)?(?:ss|ps))\b|%zmm|%k[0-7]|\{vex\}|\t62 [0-9a-f][0-9a-f] ',asm),'nonportable arithmetic instructions')
        g.run(arm+'-dependencies',['/usr/bin/objdump','-p','cmix'],15,work=work)
        needed=re.findall(r'^\s+NEEDED\s+(\S+)',(g.result/(arm+'-dependencies.stdout')).read_text(),re.M)
        options='-c dictionary/english.dic input archive --transformer models/6m-q4-fp32.tfwc2\n-d dictionary/english.dic archive output --transformer models/6m-q4-fp32.tfwc2\n'+m.FLAGS+' -O3 -Os\n'
        bundle=g.result/(arm+'-source-binary-assets.zip')
        write_bundle(bundle,work,files+[work/'cmix'],options)
        with zipfile.ZipFile(bundle) as z:
            for p in files+[work/'cmix']:m.require(z.read(str(p.relative_to(work)))==p.read_bytes(),'delivery bundle inverse differs')
        inventory=dict(source_and_asset_files=sources,native_binary=binary,required_options=options,dynamic_libraries=needed,raw_source_and_asset_bytes=sum(r['bytes'] for r in sources),overlapping_local_inventory_bytes=sum(r['bytes'] for r in sources)+binary['bytes']+len(options.encode()),delivery_zip=g.artifact(bundle),complete_submission_package=False,complete_package_bytes=None,unresolved=package['unresolved'],scope='Source/assets plus binary and options overlap; ZIP is a reproducible delivery representation, not an approved executable package. Runtime and unpacking dependencies are not included.')
        m.require(inventory['overlapping_local_inventory_bytes']<=10000000,'local package cap exceeded');g.write(arm+'-package.json',inventory)
        (work/'input').write_bytes(raw);phases={}
        for phase,args in [('encode',['-c','dictionary/english.dic','input','archive']),('decode',['-d','dictionary/english.dic','archive','restored']),('repeat',['-c','dictionary/english.dic','restored','repeat'])]:
            phases[phase]=g.run(arm+'-'+phase,[str(work/'cmix'),*args,'--transformer','models/6m-q4-fp32.tfwc2'],120,work=work)
            if phase=='encode':
                m.require(0<(work/'archive').stat().st_size<=100000,'archive cap exceeded')
                m.exact(work/'archive',ROOT/(m.PARENT+'work/fixture.cmix' if arm=='P' else PRIOR_D));(work/'input').unlink()
            if phase=='decode':m.require((work/'restored').read_bytes()==raw,'raw inverse differs')
        m.exact(work/'archive',work/'repeat');m.require(all(m.sha(p)==h for p,h in sealed.items()),'materialized source changed')
        g.closure();scratch=work/'ppm.temp';removed=None
        if scratch.is_file():removed=dict(path=str(scratch.relative_to(g.result)),bytes=scratch.stat().st_size);scratch.unlink()
        rows[arm]=dict(archive=g.artifact(work/'archive'),restored=g.artifact(work/'restored'),repeat=g.artifact(work/'repeat'),binary=binary,package=g.artifact(g.result/(arm+'-package.json')),raw_bytes=50051,raw_sha256=m.RAW_SHA,exact_inverse=True,exact_repeat=True,prior_archive_identical=True,phases=phases,overlapping_local_inventory_bytes=inventory['overlapping_local_inventory_bytes'],delivery_zip_bytes=inventory['delivery_zip']['bytes'],transient_cleanup=removed)
        g.write(arm+'-result.json',rows[arm])
    return dict(arms=rows,correctness_pass=True,archive_saving_bytes=rows['P']['archive']['bytes']-rows['D']['archive']['bytes'],binary_delta_bytes=rows['D']['binary']['bytes']-rows['P']['binary']['bytes'],overlapping_local_inventory_delta_bytes=rows['D']['overlapping_local_inventory_bytes']-rows['P']['overlapping_local_inventory_bytes'],delivery_zip_delta_bytes=rows['D']['delivery_zip_bytes']-rows['P']['delivery_zip_bytes'],complete_package_bytes=None,larger_gate_authorized=False,prior_native_archives_preserved=True,full_predictor_state_trace='unmeasured',scope='Deployment parity/cost gate; exact prior archives and separately verified projection mapping. No new corpus gain, full hidden-state trace, source license closure or complete package qualification.')


if __name__=='__main__':
    m=engine();m.execute=execute;raise SystemExit(m.main())
