"""Independent integer and packet replay; publish an explicit metadata allowlist."""
import argparse
import json
import math
from pathlib import Path
import sys
HERE=Path(__file__).resolve().parent;LIT=HERE.parent
sys.path.insert(0,str(HERE))
import implicit
import optimize
from backend import analyze,dual,module,sha,write
# Reuse only the independently audited packet/header/cost verifier, not its
# parent index, optimizer, run loader or reporting entry point.
parent_report=module('length_sensitive_parent_packet_audit',LIT/'all-substring-fraction-v1/report.py')
REUSE='not_performed_relaxation_witness_only'
STOPS={'iteration_limit','time_limit','restricted_dual_stationary','exact_primal_optimum_certificate'}

def number(v):
    assert type(v) in (int,float) and math.isfinite(v) and v>=0;return v

def integer(v,minimum=0):
    assert type(v) is int and v>=minimum;return v

def replay_arm(raw,folder,work,c,contract_hash,qualification,parent_public,parent_private):
    cohort=raw['cohort'];assert cohort in ('R','naming') and raw['mode']=='flex256'
    assert raw['complete'] is True and raw['validation_loaded'] is False and raw['contract_sha256']==contract_hash
    private=folder/f'{cohort}-flex256';assert json.loads((private/'results.json').read_text())==raw
    assert json.loads((private/'status.json').read_text())=={'phase':'complete','complete':True}
    assert not (private/'failure.json').exists()
    rel=c['cohorts'][cohort];texts=json.loads((work/rel/'fit-sources.json').read_text())
    assert set(texts)==set(map(str,c['fit_ids'])) and len(texts)==raw['fit_problems']==300
    assert all(type(t) is str and t for t in texts.values()) and set(''.join(texts.values()))<=set(dual.ALPHABET)
    receipt=next(a for a in qualification['arms'] if a['width']==8 and a['arm']==('control' if cohort=='R' else 'scope_joint'))
    for pid,text in texts.items():assert receipt['qualification'][pid]['passed'] is True and receipt['per_problem'][pid]['source_sha256']==analyze.sha(text.encode())
    assert raw['fit_source_sha256']==c['private_files'][rel+'/fit-sources.json']
    prior=next(a for a in parent_public['arms'] if a['cohort']==cohort)
    old_private=next(a for a in parent_private['arms'] if a['cohort']==cohort)
    assert old_private['complete'] and not old_private['validation_loaded']
    assert old_private['fit_source_sha256']==prior['fit_source_sha256']==raw['fit_source_sha256']
    oldq=json.loads((work/c['parent_q'][cohort]).read_text());oldcert=prior['optimization']['certificate']
    assert raw['parent_q_sha256']==sha(work/c['parent_q'][cohort])==oldcert['q_sha256']==old_private['optimization']['certificate']['q_sha256']
    for k in optimize.CERT_KEYS:assert old_private['optimization']['certificate'][k]==oldcert[k]
    banned=dual.sel.forbidden_strings(texts);index=implicit.Index(texts,banned)
    counts={'pool_entries':index.distinct_allowed_entries,'implicit_groups':len(index.base.groups),'length_pieces':len(index.pieces),
            'source_characters':len(index.base.positions),'exact_ban_occurrences':sum(len(s) for rows in index.base.banned_ends.values() for s in rows)}
    for k,v in counts.items():assert raw[k]==v
    for k in ('pool_entries','implicit_groups','source_characters','exact_ban_occurrences'):assert counts[k]==prior[k]
    assert raw['capacity']==c['pool']['capacity']==256 and raw['mandatory_entries']==0 and raw['pool_scope']==c['pool']['scope']
    D=c['search']['denominator'];assert oldcert['denominator']==D
    oldnum=implicit.parent.verify(index.base,oldq,256,D);assert oldnum==oldcert['numerator']
    oldrebuilt=index.base.certificate(oldq,256,D)
    for k in optimize.CERT_KEYS:assert oldcert[k]==oldrebuilt[k]
    initial=implicit.lift_start_multipliers(oldq);initial_cert=index.certificate(initial,256,D)
    assert implicit.verify(index,initial,256,D)==oldnum
    info=raw['optimization'];cert=info['certificate'];qpath=private/'certificate-q.json'
    assert sha(qpath)==cert['q_sha256'];q=json.loads(qpath.read_text())
    numerator=implicit.verify(index,q,256,D);rebuilt=index.certificate(q,256,D)
    assert numerator==rebuilt['numerator']>=oldnum
    for k in optimize.CERT_KEYS:
        assert cert[k]==rebuilt[k] and info['initial_certificate'][k]==initial_cert[k]==oldrebuilt[k]
    assert cert['independent_partition_and_integer_replay'] is True
    assert cert['excludes_ten_percent']==(rebuilt['integer_lower_bound']>0)
    assert info['finite_numerator_gain']==numerator-oldnum
    assert info['initial_q_all_zero']==all(v==0 for values in oldq.values() for v in values)
    assert {'seed','best'}<=set(raw['witnesses'])<={'seed','best','generated'}
    witnesses={};vocabs={}
    for name,value in raw['witnesses'].items():
        witnesses[name],vocabs[name]=parent_report.witness(private/name,value,texts,banned,c,rebuilt['integer_lower_bound'])
    pinned=json.loads((work/rel/'dictionary.json').read_text())
    assert len(pinned)==len(set(pinned))<=256 and not set(pinned)&banned
    assert vocabs['seed']==[w for w in pinned if any(w in t for t in texts.values())]
    assert info['seed_objective']==witnesses['seed']['objective']
    assert info['best_objective']==witnesses['best']['objective']==min(w['objective'] for w in witnesses.values())
    assert info['generated_objective']==(witnesses['generated']['objective'] if 'generated' in witnesses else None)
    iterations=integer(info['iterations']);assert iterations<=c['search']['iterations'] and info['stop'] in STOPS
    if info['stop']=='iteration_limit':assert iterations==c['search']['iterations']
    if info['stop']=='time_limit':assert number(info['seconds'])>=c['search']['seconds']
    if info['stop']=='exact_primal_optimum_certificate':assert rebuilt['integer_lower_bound']==witnesses['best']['objective']
    attempts=integer(info['primal_attempts']);infeasible=integer(info['primal_infeasible'])
    expected_attempts=2*((iterations-1)//c['search']['primal_every']+1) if iterations else 0
    assert infeasible<=attempts==expected_attempts
    assert ('generated' in witnesses)==(attempts>infeasible)
    traces=[json.loads(line) for line in (private/'trace.jsonl').read_text().splitlines()]
    assert len(traces)==1+2*len(implicit.BINS)+iterations
    assert traces[0]['event']=='initial' and traces[0]['exact_numerator']==oldnum and traces[0]['best_numerator']==oldnum
    assert traces[0]['upper_bound']==witnesses['seed']['objective']
    best=oldnum;previous_time=0.;diagnostics=[]
    assert len(info['bin_release'])==2*len(implicit.BINS)
    for no,(expected,diagnostic_q) in enumerate(optimize.release_sweep(initial)):
        row=traces[no+1];reported=info['bin_release'][no]
        assert row=={'event':'release',**reported,'validation_loaded':False}
        assert type(row['bin']) is int and row['bin']==expected['bin'] and row['operation']==expected['operation']
        allowed_keys={'event','bin','operation','status','best_numerator','seconds','validation_loaded'}
        if diagnostic_q is None:
            assert row['status']==expected['status']
            if 'duplicate_of' in expected:
                assert row['duplicate_of']==expected['duplicate_of']
                allowed_keys.add('duplicate_of')
        elif row['status']=='not_started_budget':assert number(row['seconds'])>=c['search']['seconds']
        else:
            assert row['status']=='evaluated';value=index.certificate(diagnostic_q,256,D)['numerator']
            assert type(row['exact_numerator']) is int and type(row['improved']) is bool
            assert row['exact_numerator']==value and row['improved']==(value>best);best=max(best,value)
            allowed_keys.update(('exact_numerator','improved'))
        assert set(row)==allowed_keys,'unexpected bin-release fields for disposition'
        assert row['best_numerator']==best
        diagnostics.append({k:row[k] for k in ('bin','operation','status','best_numerator','exact_numerator','improved','duplicate_of') if k in row})
    for no,row in enumerate(traces[1+2*len(implicit.BINS):]):
        assert row['event']=='ascent' and row['iteration']==no
        exact=row['exact_numerator'];assert type(exact) is int
        best=max(best,exact);assert row['best_numerator']==best and row['integer_lower_bound']==-(-exact//D)
        assert integer(row['gradient_norm_squared'])>=0 and number(row['theta'])<=1
    for row in traces:
        assert row['validation_loaded'] is False and number(row['seconds'])>=previous_time
        previous_time=row['seconds']
    assert best==numerator
    if iterations:
        assert traces[-1]['upper_bound']==witnesses['best']['objective'] and traces[-1]['generated_objective']==info['generated_objective']
        if info['stop']=='restricted_dual_stationary':assert traces[-1]['gradient_norm_squared']==0
    clean_cert={k:rebuilt[k] for k in optimize.CERT_KEYS};clean_cert.update(q_sha256=cert['q_sha256'],independent_partition_and_integer_replay=True,excludes_ten_percent=rebuilt['integer_lower_bound']>0)
    return {'cohort':cohort,'complete':True,'validation_loaded':False,'fit_problems':len(texts),'capacity':256,**counts,
            'fit_source_sha256':raw['fit_source_sha256'],'parent_q_sha256':raw['parent_q_sha256'],
            'initial_numerator':oldnum,'initial_integer_lower_bound':oldrebuilt['integer_lower_bound'],
            'finite_numerator_gain':numerator-oldnum,'finite_integer_bound_gain':rebuilt['integer_lower_bound']-oldrebuilt['integer_lower_bound'],
            'initial_q_all_zero':info['initial_q_all_zero'],'certificate':clean_cert,'bin_release':diagnostics,
            'iterations':iterations,'stop':info['stop'],'primal_attempts':attempts,'primal_infeasible':infeasible,'witnesses':witnesses,
            'pool_seconds':number(raw['pool_seconds']),'optimization_seconds':number(info['seconds']),'seconds':number(raw['seconds']),
            'source_qualification':'Pinned item13 exact source-hash receipt reuse; inherited item23 later exit137 remains a separate failure.',
            'semantic_reuse_audit':REUSE,'source_bans_pool_q_and_packets_replayed':True}


def build_report(folder,work,here=HERE,lit=LIT):
    implicit.require_checks();cpath=here/'contract.json';c=json.loads(cpath.read_text());chash=sha(cpath)
    base={'schema':'gamma.length-sensitive-fraction.report.v1','contract_sha256':chash,'validation_loaded':False,
          'adaptive_start':'Designed after item33 c8ed60959 recorded zero retained multipliers and nonpositive bounds.',
          'semantic_reuse_audit':REUSE}
    for rel,h in c['code_hashes'].items():assert sha(lit/rel)==h
    for path,h in c['runtime_files'].items():assert sha(Path(path))==h
    if (folder/'failure.json').exists():
        f=json.loads((folder/'failure.json').read_text());assert f['contract_sha256']==chash and f['complete'] is False and f['partial_certificates_promoted'] is False
        assert f['validation_loaded'] is False
        allowed={'TimeoutError','MemoryError','AssertionError','RuntimeError','ValueError','FileNotFoundError','OSError','KeyboardInterrupt','SystemExit'}
        return {**base,'complete':False,'status':'incomplete; no whole-job certificate accepted','failure_sha256':sha(folder/'failure.json'),
                'failure_type':f['exception'] if f['exception'] in allowed else 'other_exception','seconds':number(f['seconds']),'predictions':{'P1':False,'P2':None,'P3':None,'P4':None}}
    assert not list(folder.glob('*/failure.json'))
    raw=json.loads((folder/'results.json').read_text());assert raw['complete'] is True and raw['validation_loaded'] is False and raw['contract_sha256']==chash
    assert len(raw['arms'])==2 and {a['cohort'] for a in raw['arms']}=={'R','naming'}
    elapsed=number(raw['seconds'])
    assert elapsed<=c['limits']['overall_seconds'],'completed run exceeds frozen whole-job deadline'
    assert all(number(a['seconds'])<=elapsed for a in raw['arms']),'arm duration exceeds whole-job duration'
    for rel,h in c['private_files'].items():assert sha(work/rel)==h
    qualification=json.loads((lit/'binding-descent-v1/evidence/results.json').read_text())
    parent_public=json.loads((lit/c['parent_evidence']).read_text());parent_private=json.loads((work/c['parent_private_results']).read_text())
    assert parent_public['complete'] and parent_private['complete'] and not parent_public['validation_loaded'] and not parent_private['validation_loaded']
    assert sha(work/c['parent_private_results'])==parent_public['private_results_sha256']
    arms=[replay_arm(a,folder,work,c,chash,qualification,parent_public,parent_private) for a in raw['arms']]
    assert set(c['decoder_source_files'])=={'literals.py','pass2/working/bitpack.py'}
    for rel,spec in c['decoder_source_files'].items():assert sha(lit/rel)==spec['sha256'] and (lit/rel).stat().st_size==spec['bytes']
    assert c['decoder_dependency_bytes']==sum(s['bytes'] for s in c['decoder_source_files'].values())>0
    return {**base,'complete':True,'status':'complete; independently replayed','arms':arms,'private_results_sha256':sha(folder/'results.json'),
            'seconds':elapsed,'decoder_dependency_bytes':c['decoder_dependency_bytes'],'offline_encoder_bytes':c['offline_encoder_bytes'],
            'offline_encoder_scope':c['offline_encoder_scope'],'decoded_packets':sum(len(w['per_problem']) for a in arms for w in a['witnesses'].values()),
            'predictions':{'P1':True,'P2':any(a['finite_numerator_gain']>0 for a in arms),
                           'P3':any(a['certificate']['integer_lower_bound']>0 for a in arms),
                           'P4':not any(a['witnesses'].get('generated',{}).get('objective',1)<=0 for a in arms)}}


def write_report(r,here=HERE):
    (here/'evidence').mkdir(exist_ok=True);write(here/'evidence/results.json',r)
    lines=['# Length-sensitive full-substring fraction dual','', '[Freeze](FREEZE.md); [derivation](DRAFT.md); [metadata](evidence/results.json).','',r['status']+'.','',
           'This design follows item33’s disclosed zero-multiplier result. A larger dual family does not guarantee strict improvement in a finite run. Zero or negative bounds remain inconclusive; only equality with a verified feasible upper bound certifies an exact optimum.','']
    if r['complete']:
        lines+=['| Cohort | Allowed words | Pieces | Item33 lower | New lower | Numerator gain | Iterations | Best feasible F | Generated failures |',
                '| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |']
        for a in r['arms']:
            lines.append(f"| {a['cohort']} | {a['pool_entries']} | {a['length_pieces']} | {a['initial_integer_lower_bound']} | {a['certificate']['integer_lower_bound']} | {a['finite_numerator_gain']} | {a['iterations']} | {a['witnesses']['best']['objective']} | {a['primal_infeasible']}/{a['primal_attempts']} |")
        lines+=['','Exact packet IDs, framing, Finish, dictionaries and both decoder sources are charged. One-owner/near-whole witnesses remain relaxation diagnostics with unresolved semantic reuse; no M1 legality claim. Installed runtime footprint is unmeasured.']
    lines+=['','| Prediction | Met |','| --- | --- |']+[f'| {key} | {value} |' for key,value in r['predictions'].items()]
    lines+=['','M1 unchanged:400/500,<=256 shared entries, median<=32/p95<=96 selections,<=10% single-character bits, zero whole-solution entries. Fit-only fixed-source bounds do not close M1, unseen populations, rewrites or other gates.','']
    (here/'README.md').write_text('\n'.join(lines))


def main(folder,work):
    try:r=build_report(folder,work)
    except BaseException as error:
        r={'complete':False,'status':'report verification failed; no certificate accepted','validation_loaded':False,
           'failure_type':type(error).__name__,'predictions':{'P1':False,'P2':None,'P3':None,'P4':None}}
        if folder.is_dir():write(folder/'report-failure.json',r)
        write_report(r);raise
    write_report(r)

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--run',type=Path,required=True);ap.add_argument('--work',type=Path,required=True);a=ap.parse_args();main(a.run,a.work)
