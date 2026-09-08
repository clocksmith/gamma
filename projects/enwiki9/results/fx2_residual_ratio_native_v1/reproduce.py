"""Retain native component checks without opening corpus or loading weights."""
import hashlib
import json
import os
from pathlib import Path
import resource
import shlex
import subprocess
import sys
import time

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT.parents[1]))
os.sched_setaffinity(0,{3})
resource.setrlimit(resource.RLIMIT_AS,(536870912,)*2)
resource.setrlimit(resource.RLIMIT_CPU,(120,)*2)
resource.setrlimit(resource.RLIMIT_FSIZE,(67108864,)*2)
os.environ['PYTHONDONTWRITEBYTECODE']='1'


def write(path,data):
    with path.open('xb') as f:f.write(data)
def document(path,data):write(path,(json.dumps(data,indent=2,sort_keys=True)+'\n').encode())
def ref(path):
    data=path.read_bytes()
    return dict(path=str(path.relative_to(ROOT)) if path.is_relative_to(ROOT) else str(path),
                bytes=len(data),sha256=hashlib.sha256(data).hexdigest())


if sys.argv[1]=='phase':
    from projects.enwiki9.tests.test_fx2_residual_ratio_native_v1 import load_library,NativeFixture
    from projects.enwiki9.lib import predictor
    library,arm,action,inp,out=sys.argv[2:]
    data=Path(inp).read_bytes()
    if len(data)>8192:raise ValueError('synthetic input limit')
    model=NativeFixture(load_library(library),arm);started=time.monotonic()
    output=predictor.decode(data,model,maximum_bytes=4096) if action=='decode' else predictor.encode(data,model)
    elapsed=time.monotonic()-started;usage=resource.getrusage(resource.RUSAGE_SELF)
    out=Path(out);write(out,output)
    document(out.with_suffix('.json'),dict(output=ref(out),input=ref(Path(inp)),arm=arm,action=action,
        probability_sha256=model.probabilities.hexdigest(),boundary_sha256=model.boundaries.hexdigest(),
        bit_boundaries=model.position,state=model.serialize().decode(),
        codec_elapsed_seconds=elapsed,process_user_seconds=usage.ru_utime,process_system_seconds=usage.ru_stime,
        peak_rss_bytes=usage.ru_maxrss*1024,cpu_affinity=sorted(os.sched_getaffinity(0))))
    model.native.close()
else:
    from projects.enwiki9.tools import fx2_residual_ratio_native_adapter_v1 as adapter
    target=Path(__file__).resolve().parent/sys.argv[1];target.mkdir(exist_ok=False)
    (target/'tmp').mkdir();work=target/'source';work.mkdir()
    env=dict(os.environ,PYTHONPATH=str(ROOT.parents[1]),TMPDIR=str(target/'tmp'))
    commands=[];started=time.monotonic()
    def run(name,argv,cwd=ROOT,cap=30):
        remaining=180-(time.monotonic()-started)
        if remaining<=0:raise RuntimeError('aggregate elapsed stop')
        before=resource.getrusage(resource.RUSAGE_CHILDREN);start=time.monotonic()
        r=subprocess.run(argv,cwd=cwd,env=env,capture_output=True,timeout=min(cap,remaining))
        after=resource.getrusage(resource.RUSAGE_CHILDREN)
        record=dict(name=name,argv=argv,cwd=str(cwd),returncode=r.returncode,stdout=r.stdout.decode(errors='replace'),
                    stderr=r.stderr.decode(errors='replace'),elapsed_seconds=time.monotonic()-start,
                    user_seconds=after.ru_utime-before.ru_utime,system_seconds=after.ru_stime-before.ru_stime,
                    cumulative_child_peak_rss_bytes=after.ru_maxrss*1024)
        document(target/(name+'.execution.json'),record);commands.append(record)
        if r.returncode:raise RuntimeError(name+' failed; retained execution receipt')
    spec=adapter.build_adapter();document(target/'adapter.json',spec)
    package=json.loads((adapter.PARENT.parent/'package.json').read_text())
    for item in package['source_members']:
        original=ROOT/item['path'];assert ref(original)['sha256']==item['sha256']
        destination=work/original.relative_to(adapter.PARENT);destination.parent.mkdir(parents=True,exist_ok=True)
        write(destination,original.read_bytes())
    for row in spec['files']:
        path=work/row['source_path'];text=path.read_text()
        for change in row['replacements']:
            assert text.count(change['before'])==1;text=text.replace(change['before'],change['after'])
        path.write_text(text);assert ref(path)['sha256']==row['patched_sha256']
    for row in spec['added_files']:write(work/row['target'],(ROOT/row['source']['path']).read_bytes())
    run('syntax',['/usr/bin/g++','-std=c++17','-DSEED=923','-DUPDATE_LIMIT=3000','-include','cstdint',
                  '-march=x86-64-v3','-mrecip=none','-fno-fast-math','-ffp-contract=off','-fno-exceptions',
                  '-fsyntax-only','-MD','-MF',str(target/'syntax.d'),'src/predictor.cpp'],work,60)
    library=target/'ratio.so'
    run('compile',['/usr/bin/g++','-std=c++17','-O2','-fno-fast-math','-ffp-contract=off','-fno-exceptions',
                   '-shared','-fPIC',str(ROOT/'tests/fx2_residual_ratio_native_bridge_v1.cpp'),'-o',str(library)])
    env['GAMMA_RATIO_TEST_LIBRARY']=str(library)
    run('tests',[sys.executable,'-m','unittest','tests.test_fx2_residual_ratio_native_v1',
                 'tests.test_fx2_residual_ratio_native_adapter_v1','-v'],cap=45)
    rows=[]
    for name,raw in [('constant',b'A'*1024),('balanced',bytes(range(256))*4)]:
        inp=target/(name+'.raw');write(inp,raw);arms={}
        for arm in ('P','K','D','S'):
            phases=[]
            for action in ('encode','decode','repeat'):
                stem=name+'-'+arm+'-'+action;out=target/(stem+'.bin')
                source=target/(name+'-'+arm+'-encode.bin') if action=='decode' else inp
                run(stem,[sys.executable,str(Path(__file__).resolve()),'phase',str(library),arm,action,str(source),str(out)],cap=15)
                phases.append(json.loads(out.with_suffix('.json').read_text()))
            assert (ROOT/phases[1]['output']['path']).read_bytes()==raw
            assert phases[0]['output']['sha256']==phases[2]['output']['sha256']
            for key in ('probability_sha256','boundary_sha256','state','bit_boundaries'):
                assert len({p[key] for p in phases})==1,key
            arms[arm]=dict(archive_bytes=phases[0]['output']['bytes'],phases=phases)
        assert arms['P']['phases'][0]['output']['sha256']==arms['K']['phases'][0]['output']['sha256']
        rows.append(dict(fixture=ref(inp),arms=arms))
    deps=shlex.split((target/'syntax.d').read_text().replace('\\\n',' ').partition(':')[2])
    dependency_paths=sorted({(work/d).resolve() for d in deps})
    sources=[ROOT/p for p in ('lib/fx2_residual_ratio_v1.hpp','lib/predictor.py',
        'tests/fx2_residual_ratio_native_bridge_v1.cpp','tests/test_fx2_residual_ratio_native_v1.py',
        'tests/test_fx2_residual_ratio_native_adapter_v1.py','tools/fx2_residual_ratio_native_adapter_v1.py',
        'results/fx2_residual_ratio_native_v1/reproduce.py')]
    files=[p for p in target.rglob('*') if p.is_file()];scratch=sum(p.stat().st_size for p in files)
    assert scratch<67108864
    document(target/'receipt.json',dict(schema='gamma.enwiki9.native-residual-ratio-synthetic.v1',
        objective_bytes=90000000,objective_credit_bytes=0,corpus_bytes=0,unit_tests_passed=7,codec_phases=24,
        rows=rows,commands=commands,source_inventory=[ref(p) for p in sources],
        syntax_dependencies=[ref(p) for p in dependency_paths],compiler=ref(Path('/usr/bin/g++').resolve()),
        adapter=ref(target/'adapter.json'),artifacts=[ref(p) for p in sorted(files)],scratch_bytes=scratch,
        prior_infrastructure_failure='unit01/default-tmp.stderr records compiler temporary-file EDQUOT; owned TMPDIR resolves it.',
        complete_package_bytes=None,native_fx2_roundtrip=False,
        next_action='Freeze and publish a canonical native FX2 fixture experiment before execution.'))
    print(json.dumps(dict(receipt=ref(target/'receipt.json'),sizes=[{a:x['arms'][a]['archive_bytes'] for a in x['arms']} for x in rows])))
