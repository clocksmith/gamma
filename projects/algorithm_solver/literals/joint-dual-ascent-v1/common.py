"""Public activation/pins and fit-only source loading; never loads a parent q."""
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import platform
import sys
import prototype as p

HERE=Path(__file__).resolve().parent;LIT=HERE.parent
_path=list(sys.path);sys.path.insert(0,str(LIT/'joint-quantile-fraction-v1'))
try:
    _spec=importlib.util.spec_from_file_location('ascent_parent42_common',LIT/'joint-quantile-fraction-v1/common.py')
    inherited=importlib.util.module_from_spec(_spec);_spec.loader.exec_module(inherited)
finally:sys.path[:]=_path
sha=lambda path:hashlib.sha256(Path(path).read_bytes()).hexdigest()
digest=lambda value:hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':')).encode()).hexdigest()
read=lambda path:json.loads(Path(path).read_text())
write=inherited.write


class HardDeadline(BaseException):pass


def number(value,maximum):
    assert type(value) in (int,float) and math.isfinite(value) and 0<=value<=maximum
    return value


def check(contract):
    p.dual.require_checks();assert contract['active'] is True
    assert contract['population']=='fixed300_fit_only' and len(contract['fit_ids'])==len(set(contract['fit_ids']))==300
    assert str(Path(sys.executable).absolute())==contract['python_bin']
    import numpy
    assert contract['versions']=={'python':platform.python_version(),'numpy':numpy.__version__}
    assert all(os.environ.get(k)=='1' for k in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS'))
    for rel,h in contract['code_hashes'].items():assert sha(LIT/rel)==h,rel
    for path,h in contract['runtime_files'].items():assert sha(path)==h,path


def load(contract,work,cohort):
    assert contract['active'] is True and cohort in ('R','naming')
    rel=contract['sources'][cohort];assert sha(work/rel)==contract['private_files'][rel]
    texts=read(work/rel);assert set(texts)==set(map(str,contract['fit_ids']))
    assert all(type(text) is str and text and set(text)<=set(inherited.backend.dual.ALPHABET) for text in texts.values())
    qualification=read(LIT/contract['qualification'])
    source=next(a for a in qualification['arms'] if a['width']==8 and a['arm']==('control' if cohort=='R' else 'scope_joint'))
    for pid,text in texts.items():
        assert source['qualification'][pid]['passed'] is True
        assert hashlib.sha256(text.encode()).hexdigest()==source['per_problem'][pid]['source_sha256']
    public=read(LIT/contract['parent_evidence'])
    assert public['complete'] is True and public['validation_loaded'] is False
    assert public['contract_sha256']==contract['parent_contract_sha256']
    prior=next(a for a in public['arms'] if a['cohort']==cohort)
    assert prior['independent_cardinality_assignment_and_pool_replay'] is True
    assert prior['source_sha256']==contract['private_files'][rel]
    banned=inherited.backend.dual.sel.forbidden_strings(texts)
    index=p.dual.Index(texts,banned)
    counts={'pool_entries':index.distinct_allowed_entries,'implicit_groups':len(index.base.groups),
            'length_pieces':len(index.pieces),'source_characters':len(index.base.positions),
            'exact_ban_occurrences':sum(len(s) for rows in index.base.banned_ends.values() for s in rows)}
    assert counts==prior['counts']
    zero=next(point for point in prior['points'] if point['scale']==[0,1])
    assert zero['joint_numerator']==contract['baseline_numerators'][cohort]
    return index,counts
