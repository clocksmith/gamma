"""Pinned utilities and activation-gated source loading for item 42."""
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import platform
import sys

import mechanism
import proof

HERE=Path(__file__).resolve().parent;LIT=HERE.parent
SCALES=((0,1),(1,4),(1,2),(1,1),(2,1),(4,1))
sha=lambda path:hashlib.sha256(Path(path).read_bytes()).hexdigest()
digest=lambda obj:hashlib.sha256(json.dumps(obj,sort_keys=True,separators=(',',':')).encode()).hexdigest()
_spec=importlib.util.spec_from_file_location('joint_quantile_backend',LIT/'length-sensitive-fraction-v1/backend.py')
backend=importlib.util.module_from_spec(_spec);_import_path=list(sys.path)
try:_spec.loader.exec_module(backend)
finally:sys.path[:]=_import_path
write=backend.write


def number(value,maximum=None):
    assert type(value) in (int,float) and math.isfinite(value) and value>=0
    assert maximum is None or value<=maximum
    return value


def check_contract(c,work=None):
    mechanism.parent.require_checks()
    assert c['active'] is True and c['scales']==[list(s) for s in SCALES]
    assert c['population']=='fixed300_fit_only' and len(c['fit_ids'])==len(set(c['fit_ids']))==300
    assert str(Path(sys.executable).absolute())==c['python_bin']
    import numpy
    assert c['versions']=={'python':platform.python_version(),'numpy':numpy.__version__}
    assert all(os.environ.get(k)=='1' for k in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS'))
    for rel,h in c['code_hashes'].items():assert sha(LIT/rel)==h,rel
    for path,h in c['runtime_files'].items():assert sha(path)==h,path
    if work is not None:
        for rel,h in c['private_files'].items():assert sha(work/rel)==h,rel


def load_cohort(c,work,cohort):
    # Caller must activate and check all pins before this function opens inputs.
    assert c['active'] is True and cohort in ('R','naming')
    source=c['sources'][cohort];qfile=c['parent_q'][cohort]
    assert sha(work/source)==c['private_files'][source] and sha(work/qfile)==c['private_files'][qfile]
    texts=json.loads((work/source).read_text());q=json.loads((work/qfile).read_text())
    assert set(texts)==set(map(str,c['fit_ids']))
    assert all(type(t) is str and t for t in texts.values())
    assert set(''.join(texts.values()))<=set(backend.dual.ALPHABET)
    qualification=json.loads((LIT/c['qualification']).read_text())
    receipt=next(a for a in qualification['arms'] if a['width']==8 and a['arm']==('control' if cohort=='R' else 'scope_joint'))
    for pid,text in texts.items():
        assert receipt['qualification'][pid]['passed'] is True
        assert receipt['per_problem'][pid]['source_sha256']==hashlib.sha256(text.encode()).hexdigest()
    public=json.loads((LIT/c['parent_evidence']).read_text())
    assert public['complete'] is True and public['validation_loaded'] is False
    assert public['contract_sha256']==c['parent_contract_sha256']
    prior=next(a for a in public['arms'] if a['cohort']==cohort)
    assert prior['fit_source_sha256']==sha(work/source) and prior['certificate']['q_sha256']==sha(work/qfile)
    assert prior['certificate']['independent_partition_and_integer_replay'] is True
    mechanism.parent.validate_q(texts,q,256,c['denominator'])
    assert prior['certificate']['denominator']==c['denominator']
    banned=backend.dual.sel.forbidden_strings(texts)
    index=mechanism.parent.Index(texts,banned)
    counts={'pool_entries':index.distinct_allowed_entries,'implicit_groups':len(index.base.groups),
            'length_pieces':len(index.pieces),'source_characters':len(index.base.positions),
            'exact_ban_occurrences':sum(len(s) for rows in index.base.banned_ends.values() for s in rows)}
    for key,value in counts.items():assert prior[key]==value
    return index,q,prior,counts


def scaled(q,scale):
    n,d=scale;assert (n,d) in SCALES
    return {pid:[[v*n//d for v in row] for row in rows] for pid,rows in q.items()}


def scalar_result(scale,q,caps,unrestricted,assignments,top,D):
    necessary,exact=proof.verify_assignments(caps,unrestricted,assignments)
    path=sum(unrestricted.values());ceil=lambda n:-(-n//D)
    return {'scale':list(scale),'scaled_q_sha256':digest(q),'denominator':D,
            'unrestricted_path_numerator':path,'top_capacity_numerator':top,
            'unrestricted_numerator':path-top,'unrestricted_integer_lower_bound':ceil(path-top),
            'necessary_path_numerator':necessary,'necessary_integer_lower_bound':None if necessary is None else ceil(necessary-top),
            'joint_path_numerator':exact,'joint_numerator':None if exact is None else exact-top,
            'joint_integer_lower_bound':None if exact is None else ceil(exact-top),
            'joint_path_increase':None if exact is None else exact-path,
            'quantiles_feasible_in_relaxed_pool':exact is not None,
            'excludes_fixed300_joint_target':exact is None or exact-top>0,
            'feasible_median_cases':sum(r['feasible'] for r in assignments['median_cases'])}


def check_parent_point(summary,unrestricted,prior):
    cert=prior['certificate']
    assert summary['scale']==[1,1]
    assert unrestricted==cert['path_numerators']
    assert summary['top_capacity_numerator']==cert['top_capacity_numerator']
    assert summary['unrestricted_numerator']==cert['numerator']
    assert summary['unrestricted_integer_lower_bound']==cert['integer_lower_bound']
