"""Activation-gated item40 bindings and shared codec utilities."""
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import platform
import sys

HERE=Path(__file__).resolve().parent;LIT=HERE.parent
sha=lambda path:hashlib.sha256(Path(path).read_bytes()).hexdigest()
digest=lambda obj:hashlib.sha256(json.dumps(obj,sort_keys=True,separators=(',',':')).encode()).hexdigest()


def module(name,path):
    spec=importlib.util.spec_from_file_location(name,path);value=importlib.util.module_from_spec(spec);saved=list(sys.path)
    try:spec.loader.exec_module(value)
    finally:sys.path[:]=saved
    return value


backend=module('canonical_fraction_backend40',LIT/'fraction-primal-repair-v1/backend.py')
pool_builder=module('canonical_fraction_pool40',LIT/'fraction-primal-repair-v1/pool.py')
write=backend.write


def require_checks():
    if not __debug__ or sys.flags.optimize or 'PYTHONOPTIMIZE' in os.environ:raise RuntimeError('assertions required')


def number(value,maximum=None):
    assert type(value) in (int,float) and math.isfinite(value) and value>=0
    assert maximum is None or value<=maximum
    return value


def check_contract(c,work=None):
    require_checks();assert c['active'] is True and c['population']=='fixed300_fit_only'
    assert len(c['fit_ids'])==len(set(c['fit_ids']))==300
    assert str(Path(sys.executable).absolute())==c['python_bin']
    import numpy,scipy
    assert c['versions']=={'python':platform.python_version(),'numpy':numpy.__version__,'scipy':scipy.__version__}
    assert all(os.environ.get(k)=='1' for k in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS'))
    for rel,h in c['code_hashes'].items():assert sha(LIT/rel)==h,rel
    for path,h in c['runtime_files'].items():assert sha(path)==h,path
    if work is not None:
        for rel,h in c['private_files'].items():assert sha(work/rel)==h,rel


def load_cohort(c,work,cohort):
    assert c['active'] is True and cohort in ('R','naming')
    parent_contract=json.loads((LIT/c['parent_contract']).read_text())
    assert sha(LIT/c['parent_contract'])==c['parent_contract_sha256']
    public=json.loads((LIT/c['parent_evidence']).read_text());raw=json.loads((work/c['parent_private_results']).read_text())
    assert public['complete'] is raw['complete'] is True and public['validation_loaded'] is raw['validation_loaded'] is False
    assert public['contract_sha256']==raw['contract_sha256']==c['parent_contract_sha256']
    assert sha(work/c['parent_private_results'])==public['private_results_sha256']==c['private_files'][c['parent_private_results']]
    parent=next(a for a in public['arms'] if a['cohort']==cohort);private=next(a for a in raw['arms'] if a['cohort']==cohort)
    texts,seed,q,parent35=backend.inputs(parent_contract,work,cohort)
    assert parent['fit_source_sha256']==private['fit_source_sha256']==parent35['fit_source_sha256']
    bans=backend.dual.sel.forbidden_strings(texts);index=pool_builder.implicit.Index(texts,bans)
    rebuilt,info=pool_builder.build(index,q,seed,c['pool']['denominator'],c['pool']['capacity'],c['pool']['entries'])
    counts={k:v for k,v in info.items() if k!='provenance'}
    assert counts==parent['pool_counts']==private['pool_counts']
    poolpath=work/c['parent_pool'][cohort]
    assert sha(poolpath)==parent['pool_sha256']==private['pool_sha256']==c['private_files'][c['parent_pool'][cohort]]
    assert json.loads(poolpath.read_text())==rebuilt==sorted(set(rebuilt))
    references={};hashes={}
    for name in ('seed',):
        rel=c['parent_references'][cohort][name];path=work/rel;original=json.loads(path.read_text())
        assert sha(path)==parent['witnesses'][name]['dictionary_sha256']==private['witnesses'][name]['dictionary_sha256']==c['private_files'][rel]
        assert len(original)==len(set(original))<=256 and set(original)<=set(rebuilt) and not set(original)&bans
        references[name]=sorted(original);hashes[name]=sha(path)
    assert references['seed']==sorted(seed) and len(seed)==c['expected_seed_entries'][cohort]
    assert c['pool']['capacity']-len(seed)==c['search']['expected_free_slots']
    return {'texts':texts,'candidates':rebuilt,'seed':references['seed'],'references':references,'bans':bans,
            'parent_arm':parent,'pool_counts':counts,'original_reference_hashes':hashes,
            'bindings':{'source_sha256':parent['fit_source_sha256'],'parent_q_sha256':parent['parent_q_sha256'],
                        'pool_sha256':sha(poolpath),'parent_private_results_sha256':sha(work/c['parent_private_results'])}}
