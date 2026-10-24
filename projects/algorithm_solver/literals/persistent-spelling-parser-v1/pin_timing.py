"""Public-code/runtime inventory only; never executes timing fixtures."""
import hashlib
import json
import os
from pathlib import Path
import platform
import sys
import fixtures

HERE = Path(__file__).resolve().parent
LIT = HERE.parent
PYTHON = '/home/x/deco/gamma/.venv_rocm/bin/python'
MEASURED_FILES = ('DRAFT.md', 'TIMING-SPEC.md', 'client.py', 'logic.cjs',
                  'service.cjs', 'test_service.py', 'fixtures.py', 'pin_timing.py',
                  'timing.py', 'timing_worker.py', 'test_timing.py')


def require_checks():
    if not __debug__ or sys.flags.optimize or 'PYTHONOPTIMIZE' in os.environ:
        raise RuntimeError('Normal Python assertions required')


def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def build():
    require_checks()
    parent=json.loads((LIT/'postfit-spelling-stack-v1/contract.json').read_text())
    code=dict(parent['code_hashes']);runtime=dict(parent['runtime_files'])
    for rel,digest in code.items(): assert sha(LIT/rel)==digest,rel
    for path,digest in runtime.items(): assert sha(path)==digest,path
    for name in MEASURED_FILES:
        path=HERE/name;code[str(path.relative_to(LIT))]=sha(path)
    # Import no research loader while collecting the harness's standard library.
    import subprocess, selectors, threading, signal, resource, ctypes, argparse, statistics
    modules=[subprocess,selectors,threading,signal,resource,ctypes,argparse,statistics,json]
    for module in modules:
        path=getattr(module,'__file__',None)
        if path:runtime[str(Path(path).resolve())]=sha(path)
    runtime[str(Path(PYTHON).resolve())]=sha(Path(PYTHON).resolve())
    return {'schema':'gamma.synthetic-parser-timing-pins.v1','synthetic_only':True,
            'launch_authority':'Separate root review required; pinning is not launch approval',
            'python_bin':PYTHON,'python_version':platform.python_version(),
            'code_hashes':code,'runtime_files':runtime,'fixture_sha256':fixtures.digest(fixtures.specification()),
            'blocks':list(fixtures.BLOCKS),'seconds':120,'failure_cleanup_seconds':10,
            'core':4,'per_process_address_space_bytes':8*1024**3,
            'aggregate_memory_cap_claim':False,'private_inputs':False}


def verify(expected):
    require_checks();path=HERE/'timing-pins.json'
    assert sha(path)==expected,'Reviewed pin digest mismatch'
    saved=json.loads(path.read_text())
    assert str(Path(sys.executable).absolute())==saved['python_bin']
    assert saved==build(),'Code/runtime/fixture drift'
    return saved


if __name__=='__main__':
    value=build();path=HERE/'timing-pins.json'
    path.write_text(json.dumps(value,sort_keys=True,indent=2)+'\n')
    print(json.dumps({'path':str(path),'sha256':sha(path),'measurement_run':False}))
