"""Item62 strict public authority and role-specific six-file ancestral readers."""
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import platform
import subprocess
import sys
import time
HERE=Path(__file__).resolve().parent;LIT=HERE.parent
COHORTS=('R','naming');ROLES=('production','report');MAX_BYTES=64*1024**2
LIMITS={'worker_seconds':600,'production_seconds':1200,'report_seconds':1200,'cleanup_seconds':10,
        'address_space_bytes':8*1024**3,'arm_cores':{'R':[6],'naming':[7]}}
PUBLIC={'50contract':'potential-lift-certificate-v1/contract.json','50':'potential-lift-certificate-v1/evidence/results.json',
 '56contract':'support-coverage-floor-v1/contract.json','56':'support-coverage-floor-v1/evidence/results.json',
 '56production':'support-coverage-floor-v1/evidence/production-supervisor.json','56report':'support-coverage-floor-v1/evidence/supervisor.json',
 '57contract':'owner-path-cap-v1/contract.json','57':'owner-path-cap-v1/evidence/results.json',
 '57production':'owner-path-cap-v1/evidence/production-supervisor.json','57report':'owner-path-cap-v1/evidence/report-supervisor.json',
 '59':'support-budget-feasibility-v1/evidence/public-lineage.json',
 '60contract':'joint-path-cap-v1/contract.json','60':'joint-path-cap-v1/evidence/results.json',
 '60production':'joint-path-cap-v1/evidence/production-supervisor.json','60report':'joint-path-cap-v1/evidence/report-supervisor.json',
 '61contract':'required-owner-cap-v1/contract.json','61':'required-owner-cap-v1/evidence/results.json',
 '61production':'required-owner-cap-v1/evidence/production-supervisor.json','61report':'required-owner-cap-v1/evidence/report-supervisor.json'}
SOURCES={'R':'binding-descent/run-v1/control-256/fit-sources.json','naming':'binding-descent/run-v1/scope_joint-256/fit-sources.json'}
POOLS={c:'all-length-fraction/run-v1/'+('R' if c=='R' else 'naming')+'-flex256/pool.json' for c in COHORTS}
PARENTS={role:{cohort:('joint-path-cap/run-v1/'+cohort+'/results.json' if role=='production' else
 'joint-path-cap/report-v1/'+cohort+'-proof.json') for cohort in COHORTS} for role in ROLES}


def require_checks():
    if not __debug__ or sys.flags.optimize or os.environ.get('PYTHONOPTIMIZE','') not in ('','0'):raise RuntimeError('normal assertions required')

def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def digest(value):return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
def integer(value,minimum=0,maximum=None):
    assert type(value) is int and value>=minimum and (maximum is None or value<=maximum);return value

def number(value,maximum=None):
    assert type(value) in (int,float) and math.isfinite(value) and value>=0 and (maximum is None or value<=maximum);return value

def exact(a,b):
    assert type(a) is type(b)
    if type(b) is dict:
        assert a.keys()==b.keys()
        for key in b:exact(a[key],b[key])
    elif type(b) is list:
        assert len(a)==len(b)
        for x,y in zip(a,b):exact(x,y)
    else:assert a==b

def parse(raw):
    def unique(pairs):
        out={}
        for k,v in pairs:assert k not in out,'duplicate key';out[k]=v
        return out
    return json.loads(raw,object_pairs_hook=unique,parse_constant=lambda _:(_ for _ in ()).throw(ValueError('nonfinite JSON')))

def read(path):
    with Path(path).open('rb') as stream:raw=stream.read(MAX_BYTES+1)
    assert len(raw)<=MAX_BYTES,'JSON carrier limit';return parse(raw)

def write(path,value):
    path=Path(path);tmp=path.with_name(path.name+'.pending')
    encoded=(json.dumps(value,sort_keys=True,indent=2,allow_nan=False)+'\n').encode()
    assert len(encoded)<=MAX_BYTES,'JSON carrier limit'
    tmp.write_bytes(encoded);tmp.replace(path)

def module(name,rel):
    spec=importlib.util.spec_from_file_location(name,LIT/rel);obj=importlib.util.module_from_spec(spec);spec.loader.exec_module(obj);return obj

def coverage():return module('required62_coverage56','support-coverage-floor-v1/coverage.py')
def coverage_report():return module('required62_coverage_report56','support-coverage-floor-v1/report.py')


def public_inputs(config):
    require_checks();assert set(config['public_files'])==set(PUBLIC.values())
    values={}
    for key,rel in PUBLIC.items():
        assert sha(LIT/rel)==config['public_files'][rel];values[key]=read(LIT/rel)
    e50,e56,e57,e59=(values[k] for k in ('50','56','57','59'))
    for n in ('50','56','57','60','61'):
        e=values[n];p=values[n+'contract']
        assert p['active'] is True and e['complete'] is True and e['validation_loaded'] is False
        assert e['contract_sha256']==config['public_files'][PUBLIC[n+'contract']]
        assert e['validation_or_cases_opened'] is False
        exact(p['fit_ids'],config['fit_ids'])
    assert e50['verdicts']['all257_replayed'] is True
    assert e59['complete'] is True and e59['capacity']==256
    assert e57['feasibility59_sha256']==config['public_files'][PUBLIC['59']]
    for n in ('56','57','60','61'):
        for phase in ROLES:
            s=values[n+phase]
            assert s['complete'] is True and s['phase']==phase and s['contract_sha256']==values[n]['contract_sha256']
            exact(s['returncodes'],[0,0]);number(s['elapsed'],1200);number(s['cleanup_seconds'],10)
        assert values[n]['production_supervisor_sha256']==config['public_files'][PUBLIC[n+'production']]
    arms={n:{a['cohort']:a for a in values[n]['arms']} for n in ('50','56','57','59','60','61')}
    for n in arms:assert list(arms[n])==list(COHORTS)
    expected={role:{} for role in ROLES}
    for cohort in COHORTS:
        a50,a56,a57,a59=(arms[n][cohort] for n in ('50','56','57','59'))
        for a in (a50,a56,a57):assert a['complete'] is True and a['validation_loaded'] is False
        for key in ('all257_independently_replayed','baseline53_reconstructed','all_forward_schedule_recurrences_checked'):assert a57[key] is True
        assert a56['all_sources_independently_replayed'] is a56['all_prefix_suffix_recurrences_checked'] is True
        assert a50['all257_independently_replayed'] is a50['old_certificate_independently_replayed'] is True
        exact(config['source_hashes'][cohort],values['50contract']['source_hashes'][cohort])
        assert digest(config['source_hashes'][cohort])==a50['source_identity_sha256']==a56['source_identity_sha256']==a57['source_identity_sha256']==a59['source_identity_sha256']
        assert a50['banned_set_sha256']==a56['banned_set_sha256']==a57['banned_set_sha256']==a59['banned_set_sha256']
        assert a57['denominator']==config['denominator']==1000000 and a57['fit_problems']==300
        assert a56['coverage_floor']==a56['private_character_floor']==a59['minimum_feasible_one_owner_budget']==3
        assert a59['paid_seed_entries']==256 and a59['fit_covered']==a59['fit_qualified']==300
        exact(a59['nonempty_at_most_budget_range'],[3,256])
        for key,rel in (('sources',SOURCES[cohort]),('pool',POOLS[cohort])):
            for n in ('50','56','57'):assert values[n+'contract']['cohorts'][cohort][key]==rel
            hashes=[values[n+'contract']['private_files'][rel] for n in ('50','56','57')]
            assert len(set(hashes))==1
            assert a56['source_file_sha256' if key=='sources' else 'pool_file_sha256']==a59['source_file_sha256' if key=='sources' else 'pool_file_sha256']==hashes[0]
            for role in ROLES:expected[role][rel]=hashes[0]
        expected['production'][PARENTS['production'][cohort]]=arms['60'][cohort]['production_arm_sha256']
        expected['report'][PARENTS['report'][cohort]]=arms['60'][cohort]['independent_receipt_sha256']
        exact(a57['geometry'],a50['geometry']);assert a56['source_characters']==a57['geometry']['source_characters']
        assert a56['pool_entries']==a57['old_pool_entries']==a50['old_pool_entries']
        assert a56['occurrences']==a57['old_occurrences']==a50['old_occurrences']
        a60,a61=arms['60'][cohort],arms['61'][cohort]
        for a in (a60,a61):
            assert a['complete'] is True and a['validation_loaded'] is False
            assert a['source_identity_sha256']==a57['source_identity_sha256']
            assert a['banned_set_sha256']==a57['banned_set_sha256']
            assert a['denominator']==a57['denominator'] and a['path_numerator']==a57['path_numerator']
            exact(a['baseline57_rows'],a57['rows'])
        for key in ('all257_independently_replayed','all60_forward_recurrences_checked','all57_forward_recurrences_checked','historical57_reconstructed'):
            assert a60[key] is True
        for key in ('all257_rows_replayed','all_forward_recurrences_checked','fresh_forced_owner_replay','fresh_constrained_allocation_replay'):
            assert a61[key] is True
        assert a61['fresh_item57_full_graph_replay'] is False
        assert a60['baseline57_scientific_sha256']==a61['parent_scientific_proof_sha256']==a57['scientific_proof_sha256']
        exact(a60['geometry'],a50['geometry']);exact(a60['class_counts'],a57['class_counts'])
        exact(a60['baseline53_paired_digests'],a57['baseline53_paired_digests'])
        assert a60['old_occurrences']==a50['old_occurrences']
        assert a61['forced_source_ids_sha256']==a56['forced_source_ids_sha256']
        assert a61['owner_classes_sha256']==a56['owner_classes_sha256']
        assert a61['coverage_floor']==3 and a61['coverage_occurrences']==a56['occurrences']
        assert a61['coverage_occurrence_sha256']==a56['occurrence_sha256']
        for key,rel in (('sources',SOURCES[cohort]),('pool',POOLS[cohort])):
            assert values['60contract']['cohorts'][cohort][key]==rel
            assert values['60contract']['private_files'][rel]==expected['production'][rel]
            for role in ROLES:assert values['61contract']['role_private_files'][role][rel]==expected[role][rel]
    for n in ('60','61'):
        assert values[n]['feasibility59_sha256']==config['public_files'][PUBLIC['59']]
        assert values[n]['parent57_evidence_sha256']==config['public_files'][PUBLIC['57']]
        assert values[n]['predictions']['P1'] is True
    exact(config['role_private_files'],expected)
    assert all(len(v)==6 for v in expected.values()) and len(set().union(*(set(v) for v in expected.values())))==8
    for n in arms:exact(config['parent'+n+'_arms'],arms[n])
    return arms


def check_contract(config):
    require_checks();assert config['active'] is True and config['schema']=='gamma.required-joint-path-cap.contract.v2'
    exact(config['limits'],LIMITS);assert config['population']=='fixed300_fit_only'
    exact(config['k_values'],list(range(257)));integer(config['capacity'],256,256)
    assert len(config['fit_ids'])==len(set(config['fit_ids']))==300
    for pid in config['fit_ids']:integer(pid)
    assert str(Path(sys.executable).absolute())==config['python_bin'] and platform.python_version()==config['python_version']
    assert all(os.environ.get(k)=='1' for k in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS'))
    for rel,h in config['code_hashes'].items():assert sha(LIT/rel)==h,rel
    for path,h in config['runtime_files'].items():assert sha(path)==h,path
    public_inputs(config)


class Reader:
    def __init__(self,config,work,role,cohort):
        assert config['active'] is True and role in ROLES and cohort in COHORTS
        assert str(Path(work).absolute())==config['work'], 'undeclared work root'
        self.root=Path(work).resolve();assert str(self.root)==config['work'], 'work root symlink'
        self.config=config;self.role=role;self.reads=[]
        self.allowed={rel:config['role_private_files'][role][rel] for rel in (SOURCES[cohort],POOLS[cohort],PARENTS[role][cohort])}
    def read(self,rel):
        assert rel in self.allowed and not Path(rel).is_absolute() and '..' not in Path(rel).parts
        path=self.root/rel;assert path.resolve()==path and path.is_file(),'symlink or path escape'
        with path.open('rb') as stream:raw=stream.read(MAX_BYTES+1)
        assert len(raw)<=MAX_BYTES and hashlib.sha256(raw).hexdigest()==self.allowed[rel]
        value=parse(raw);self.reads.append({'path':rel,'sha256':self.allowed[rel],'bytes':len(raw)});return value


def parse_bans(texts,deadline):
    remaining=deadline-time.monotonic()
    if remaining<=0:raise TimeoutError('parser deadline')
    proc=subprocess.Popen(['/usr/bin/node',str(LIT/'tail-search-v1/structure.cjs')],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    try:out,_=proc.communicate(json.dumps(texts).encode(),timeout=remaining)
    except BaseException:
        try:proc.kill()
        except ProcessLookupError:pass
        raise
    assert proc.returncode==0;rows=parse(out);assert rows.keys()==texts.keys();banned=set(texts.values())
    for row in rows.values():
        assert type(row['bodies']) is list and row['bodies'] and all(type(w) is str and w for w in row['bodies'])
        banned.update(row['bodies'])
    return banned


def load_inputs(config,work,cohort,role,deadline):
    check_contract(config);reader=Reader(config,work,role,cohort)
    parent=reader.read(PARENTS[role][cohort]);texts=reader.read(SOURCES[cohort]);pool=reader.read(POOLS[cohort])
    assert type(texts) is dict and set(texts)==set(map(str,config['fit_ids']))
    alphabet=set(chr(i) for i in range(32,127))|{'\n'}
    assert all(type(t) is str and t and set(t)<=alphabet for t in texts.values())
    hashes={pid:hashlib.sha256(t.encode()).hexdigest() for pid,t in texts.items()};exact(hashes,config['source_hashes'][cohort])
    assert type(pool) is list and pool==sorted(set(pool)) and all(type(w) is str and w for w in pool)
    assert alphabet<=set(pool)
    banned=parse_bans(texts,deadline);assert not set(pool)&banned
    assert digest(sorted(banned))==config['parent56_arms'][cohort]['banned_set_sha256']
    assert time.monotonic()<deadline
    return {'parent':parent,'texts':texts,'pool':pool,'banned':banned,'source_hashes':hashes,'reads':reader.reads}
