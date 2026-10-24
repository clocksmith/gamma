"""Item58 explicit shared code authority and strict JSON transport."""
import os
if not __debug__ or os.environ.get('PYTHONOPTIMIZE','') not in ('','0'):
    raise RuntimeError('Normal Python assertions required')
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
HERE=Path(__file__).resolve().parent;LIT=HERE.parent
MEMORY=8*1024**3;WORKER_SECONDS=600;WHOLE_SECONDS=1200;CLEANUP=10
FILES=('DRAFT.md','FREEZE.md','common.py','binding.py','adapter.py','decisions.py','run.py','supervise.py','make_contract.py','test_adapter.py','test_binding.py','test_run.py','test_supervise.py')
def sha(raw):return hashlib.sha256(raw).hexdigest()
def hashfile(path):return sha(Path(path).read_bytes())
def pairs(items):
    out={}
    for k,v in items:
        assert k not in out,'Duplicate JSON key';out[k]=v
    return out

def read(path):return json.loads(Path(path).read_bytes(),object_pairs_hook=pairs)
def write(path,value):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    pending=path.with_name(path.name+'.pending');pending.write_text(json.dumps(value,sort_keys=True,indent=2,allow_nan=False)+'\n');pending.replace(path)
_loaded={}
def shared(name):
    if name in _loaded:return _loaded[name]
    deps={'report':('common','ban_replay'),'test_current_best':('current_best','report')}.get(name,())
    loaded={dep:shared(dep) for dep in deps};saved={dep:sys.modules.get(dep) for dep in deps};paths=list(sys.path)
    try:
        sys.modules.update(loaded)
        spec=importlib.util.spec_from_file_location('carrier58_prior54_'+name,LIT/'persistent-spelling-stack-v1'/(name+'.py'))
        obj=importlib.util.module_from_spec(spec);sys.modules[spec.name]=obj;spec.loader.exec_module(obj);_loaded[name]=obj;return obj
    finally:
        sys.path[:]=paths
        for dep,value in saved.items():
            if value is None:sys.modules.pop(dep,None)
            else:sys.modules[dep]=value

def verify(config,active=True):
    assert config['schema']=='gamma.comparator-carrier-replay.v1'
    assert config['active'] is active and config['historical_only'] is True
    assert config['limits']=={'worker_seconds':600,'whole_seconds':1200,'cleanup_seconds':10,'address_space_bytes':MEMORY,'cores':[0,1,2,3]}
    for rel,h in config['code_hashes'].items():assert hashfile(LIT/rel)==h,rel
    for path,h in config['runtime_files'].items():assert hashfile(path)==h,path

class Reader:
    """Only declared exact carriers; reject symlinks, escapes and excess bytes."""
    def __init__(self,config):self.config=config;self.private_reads=[]
    def __call__(self,base,relative,expected):
        base=Path(base).resolve();rel=Path(relative)
        assert not rel.is_absolute() and '..' not in rel.parts
        if base==LIT.resolve():allowed=self.config['code_hashes'];limit=64*1024**2
        else:
            assert base==Path(self.config['work']).resolve();allowed=self.config['private_inputs'];limit=64*1024**2
        assert relative in allowed and allowed[relative]==expected,'Undeclared carrier'
        path=base/rel
        assert path.resolve()==path and path.is_file(),'Symlink/path escape'
        with path.open('rb') as f:raw=f.read(limit+1)
        assert len(raw)<=limit,'Carrier byte envelope'
        assert sha(raw)==expected,'Carrier digest mismatch'
        value=json.loads(raw,object_pairs_hook=pairs)
        if base!=LIT.resolve():self.private_reads.append({'path':relative,'sha256':expected,'bytes':len(raw)})
        return value
