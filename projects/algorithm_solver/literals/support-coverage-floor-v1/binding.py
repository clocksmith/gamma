"""Item56 public authority and exactly four private source/pool files; no q."""
import hashlib
import json
import math
import os
from pathlib import Path
import platform
import subprocess
import sys
import time

HERE=Path(__file__).resolve().parent; LIT=HERE.parent
COHORTS=('R','naming')
LIMITS={'worker_seconds':600,'production_seconds':1200,'report_seconds':1200,
        'cleanup_seconds':10,'address_space_bytes':8*1024**3,'arm_cores':{'R':[6],'naming':[7]}}


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def digest(value):return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def number(value,maximum=None):
    assert type(value) in (int,float) and math.isfinite(value) and value>=0
    assert maximum is None or value<=maximum
    return value


def exact(actual,expected):
    assert type(actual) is type(expected)
    if type(expected) is dict:
        assert actual.keys()==expected.keys()
        for key in expected:exact(actual[key],expected[key])
    elif type(expected) is list:
        assert len(actual)==len(expected)
        for a,b in zip(actual,expected):exact(a,b)
    else:assert actual==expected


def read(path):
    def unique(pairs):
        out={}
        for k,v in pairs:assert k not in out;out[k]=v
        return out
    return json.loads(Path(path).read_text(),object_pairs_hook=unique,
        parse_constant=lambda x:(_ for _ in ()).throw(ValueError('nonfinite JSON')))


def write(path,value):
    path=Path(path);temporary=path.with_name(path.name+'.tmp')
    with temporary.open('w') as stream:
        json.dump(value,stream,sort_keys=True,indent=2,allow_nan=False);stream.write('\n');stream.flush();os.fsync(stream.fileno())
    temporary.replace(path)


def require_checks():
    if not __debug__ or sys.flags.optimize or os.environ.get('PYTHONOPTIMIZE','') not in ('','0'):
        raise RuntimeError('normal assertions required')


def accepted_parent(config):
    """Public-only accepted completeness and exact lineage before private opens."""
    for pin in (config['parent50_contract'],config['parent50_evidence']):
        assert set(pin)=={'path','sha256'}
        assert sha(LIT/pin['path'])==pin['sha256']
    parent=read(LIT/config['parent50_contract']['path']);evidence=read(LIT/config['parent50_evidence']['path'])
    assert parent['active'] is True and parent['population']=='fixed300_fit_only'
    exact(parent['fit_ids'],config['fit_ids'])
    assert evidence['schema']=='gamma.potential-lift.report.v1' and evidence['complete'] is True
    assert evidence['contract_sha256']==config['parent50_contract']['sha256']
    assert evidence['validation_loaded'] is False and evidence['validation_or_cases_opened'] is False
    assert evidence['verdicts']['all257_replayed'] is evidence['verdicts']['k0_preserves_old_bound'] is True
    assert [a['cohort'] for a in evidence['arms']]==list(COHORTS)
    arms={a['cohort']:a for a in evidence['arms']};exact(arms,config['parent50_arms'])
    expected_private={}
    for cohort in COHORTS:
        a=arms[cohort];old=parent['old_arms'][cohort];paths=parent['cohorts'][cohort]
        assert a['complete'] is True and a['validation_loaded'] is False
        for flag in ('all257_independently_replayed','old_certificate_independently_replayed','suffix_potential_proof_checked'):assert a[flag] is True
        assert a['contract_sha256']==config['parent50_contract']['sha256'] and a['fit_problems']==300
        exact(config['cohorts'][cohort],{key:paths[key] for key in ('sources','pool')})
        exact(config['source_hashes'][cohort],parent['source_hashes'][cohort])
        assert digest(config['source_hashes'][cohort])==a['source_identity_sha256']
        assert a['old_pool_entries']==old['pool_entries'] and a['old_occurrences']==old['occurrences']
        for key in ('sources','pool'):expected_private[paths[key]]=parent['private_files'][paths[key]]
        assert type(a['class_counts']['2']) is int and 0<=a['class_counts']['2']<=a['old_pool_entries']
        assert len(a['rows'])==257
        for k,row in enumerate(a['rows']):
            assert set(row)=={'k','charge','numerator','integer_lower_bound','one_owner_slots','shared_slots'}
            assert all(type(v) is int for v in row.values()) and row['k']==k
            assert row['numerator']==a['path_numerator']-row['charge']
            assert row['integer_lower_bound']==-(-row['numerator']//a['denominator'])
        assert a['largest_positive_k']==max((r['k'] for r in a['rows'] if r['integer_lower_bound']>0),default=None)
    exact(config['private_files'],expected_private);assert len(expected_private)==4
    return parent,arms


def check_contract(config):
    require_checks();assert config['active'] is True and config['schema']=='gamma.support-coverage-floor.contract.v1'
    exact(config['limits'],LIMITS);assert config['population']=='fixed300_fit_only'
    assert type(config['fit_ids']) is list and len(set(config['fit_ids']))==len(config['fit_ids'])==300
    assert all(type(pid) is int for pid in config['fit_ids'])
    assert str(Path(sys.executable).absolute())==config['python_bin'] and platform.python_version()==config['python_version']
    assert all(os.environ.get(k)=='1' for k in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS'))
    for rel,h in config['code_hashes'].items():assert sha(LIT/rel)==h,rel
    for path,h in config['runtime_files'].items():assert sha(path)==h,path
    accepted_parent(config)


def checked_bytes(config,work,relative):
    assert config['active'] is True and relative in config['private_files']
    assert not Path(relative).is_absolute() and '..' not in Path(relative).parts
    data=(Path(work)/relative).read_bytes()
    assert hashlib.sha256(data).hexdigest()==config['private_files'][relative]
    return data


def parse_bans(texts,deadline):
    remaining=deadline-time.monotonic()
    if remaining<=0:raise TimeoutError('parser deadline')
    # The process inherits its worker group; outer supervision owns descendants.
    proc=subprocess.Popen(['/usr/bin/node',str(LIT/'tail-search-v1/structure.cjs')],
        stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    try:out,_=proc.communicate(json.dumps(texts).encode(),timeout=remaining)
    except BaseException:
        # Kill is nonblocking; do not wait or start another I/O after a one-shot
        # deadline. The enclosing supervisor kills/reaps the complete group.
        try:proc.kill()
        except ProcessLookupError:pass
        raise
    assert proc.returncode==0,'source/body parser failed'
    parsed=json.loads(out);assert set(parsed)==set(texts);banned=set(texts.values())
    for row in parsed.values():
        assert type(row) is dict and type(row['bodies']) is list and row['bodies']
        assert all(type(w) is str and w for w in row['bodies']);banned.update(row['bodies'])
    return banned


def load_inputs(config,work,cohort,deadline):
    check_contract(config);assert cohort in COHORTS
    paths=config['cohorts'][cohort]
    texts=json.loads(checked_bytes(config,work,paths['sources']))
    pool=json.loads(checked_bytes(config,work,paths['pool']))
    assert type(texts) is dict and set(texts)==set(map(str,config['fit_ids']))
    assert all(type(t) is str and t and set(t)<=set(chr(i) for i in range(32,127))|{'\n'} for t in texts.values())
    hashes={pid:hashlib.sha256(t.encode()).hexdigest() for pid,t in texts.items()}
    exact(hashes,config['source_hashes'][cohort])
    assert type(pool) is list and all(type(w) is str and w for w in pool) and pool==sorted(set(pool))
    # Accepted50 includes every paid alphabet singleton; needed for the exact
    # equality between the shared-only floor and private-character sources.
    assert set(chr(i) for i in range(32,127))|{'\n'} <= set(pool)
    expected=config['parent50_arms'][cohort]
    assert len(pool)==expected['old_pool_entries']
    banned=parse_bans(texts,deadline)
    assert not set(pool)&banned and digest(sorted(banned))==expected['banned_set_sha256']
    assert digest(hashes)==expected['source_identity_sha256']
    assert time.monotonic()<deadline
    bindings={'source_sha256':config['private_files'][paths['sources']],
        'pool_sha256':config['private_files'][paths['pool']], 'source_identity_sha256':digest(hashes),
        'banned_set_sha256':digest(sorted(banned)), 'banned_entries':len(banned),
        'parent50_evidence_sha256':config['parent50_evidence']['sha256']}
    return {'texts':texts,'pool':pool,'banned':banned,'source_hashes':hashes,'bindings':bindings}
