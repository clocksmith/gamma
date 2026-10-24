"""Bounded item58 historical comparator-only reporter; no source execution."""
import time
STARTED=time.monotonic()
import signal
class BootstrapDeadline(BaseException):pass
if __name__=='__main__':
    signal.signal(signal.SIGALRM,lambda *_:(_ for _ in ()).throw(BootstrapDeadline('Import deadline')))
    signal.setitimer(signal.ITIMER_REAL,max(.000001,STARTED+600-time.monotonic()))
import argparse
import math
import os
from pathlib import Path
import resource
import signal
import types
import common as c
import adapter
import binding
import decisions

RESULT_KEYS=set('schema complete historical_only promotion_allowed current_best_claim recorded54_commit fixed51_commit contract_sha256 authorities private_inputs comparator candidates restated54_predicates predictions58 parent54_P4_preserved decoded_comparator_packets candidate_packets_replayed_here accepted54_packet_views fresh_source_executions fresh_qualification_jobs ban_replay decoder_dependency_bytes offline_implementation_bytes model_bytes training_steps runtime_footprint scope worker_seconds peak_rss_kib'.split())

class Deadline(BaseException):pass

def validate_output(value):
    assert set(value)==RESULT_KEYS
    assert value['schema']=='gamma.comparator-carrier-replay.evidence.v1'
    assert value['complete'] is True and value['historical_only'] is True
    assert value['promotion_allowed'] is False and value['current_best_claim'] is False
    seconds=value['worker_seconds'];assert type(seconds) in (int,float) and math.isfinite(seconds) and 0<=seconds<=c.WORKER_SECONDS
    assert value['decoded_comparator_packets']==800 and value['candidate_packets_replayed_here']==0
    assert value['parent54_P4_preserved'] is None
    assert len(value['candidates'])==12 and set(value['comparator'])==set(adapter.POLICIES)
    assert value['restated54_predicates']['record_time_best']['resolved'] is True
    for a in [*value['candidates'],*value['comparator'].values()]:
        assert set(a)==set('arm policy width entries character_entries dictionary_bytes dictionary_sha256 dictionary_binary_sha256 illegal_entry_sha256 fit validation per_problem qualification'.split())
        assert all(set(row)==binding.ROW for row in a['per_problem'].values())
    return value

def arm(deadline):
    left=deadline-time.monotonic()
    if left<=0:raise Deadline('Absolute report deadline')
    signal.setitimer(signal.ITIMER_REAL,left)

def failure_bound(error,deadline):
    end=min(time.monotonic()+c.CLEANUP,deadline+c.CLEANUP)
    end=min(end,getattr(error,'_carrier58_failure_deadline',end));error._carrier58_failure_deadline=end
    return end

def remove_success(out,deadline):
    for name in ('results.json','REPORT.md','supervisor.json'):
        arm(deadline)
        try:(out/name).unlink(missing_ok=True)
        except OSError:pass

def withdraw(out,error,deadline):
    end=failure_bound(error,deadline);remove_success(out,end)
    arm(end);out.mkdir(parents=True,exist_ok=True)
    value={'schema':'gamma.comparator-carrier-replay.failure.v1','complete':False,'historical_only':True,
      'promotion_allowed':False,'error_type':type(error).__name__,'verdict':None}
    arm(end);c.write(out/'failure.json',value)
    arm(end);(out/'REPORT.md').write_text('# Item58 incomplete\n\nNo historical comparison verdict.\n')
    arm(end);c.write(out/'results.json',value)
    arm(end)

def safe_arm(a):
    """Fresh metadata construction; no raw input blob copied into publication."""
    keys=('arm','policy','width','entries','character_entries','dictionary_bytes','dictionary_sha256','dictionary_binary_sha256','illegal_entry_sha256','fit','validation')
    out={key:a[key] for key in keys}
    out['per_problem']={pid:{key:row[key] for key in binding.ROW} for pid,row in a['per_problem'].items()}
    out['qualification']={pid:{'passed':row['qualified_source'],'source_sha256':row['source_sha256']} for pid,row in a['per_problem'].items()}
    return out

def execute(config,deadline):
    arm(deadline);c.verify(config);parent,e,references=binding.public_inputs(config)
    prior=c.shared('report');ban=c.shared('ban_replay').BanReplay(c.LIT/'tail-search-v1/structure.cjs',deadline,Deadline)
    def bans(texts):
        arm(deadline);variants={f'{pid}:{c.sha(text.encode())}':text for pid,text in texts.items()}
        ban.extend(variants);arm(deadline);return ban.banned(variants)
    def encode(text,vocab,policy):arm(deadline);return prior.encode(text,vocab,policy)
    r=types.SimpleNamespace(c=prior.c,encode=encode,aggregate=prior.aggregate,external_original_bans=bans)
    reader=c.Reader(config);index={(a['arm'],a['policy']):a for a in e['arms']}
    policies,meta=adapter.external(config['comparator_binding'],parent,index,r,reader)
    arm(deadline);assert set(x['path'] for x in reader.private_reads)==set(config['private_inputs']) and len(reader.private_reads)==4
    outcome=decisions.decisions(e['arms'],references,parent,policies,meta,prior.aggregate)
    for name,v in outcome['verdicts'].items():
        old=e['verdicts'][name];assert v['transfer']==old['transfer']
        for policy in prior.POLICIES:
            adapter.exact(v['policies'][policy]['transfer'],old['policies'][policy]['transfer'])
            for ref in ('R','seed13','best24','N','NCP'):adapter.exact(v['policies'][policy]['comparisons'][ref],old['policies'][policy]['comparisons'][ref])
    for key in ('P1','P2','P3'):assert outcome['predictions'][key]==e['predictions'][key]
    assert outcome['M1_gaps']==e['M1_gaps']
    # All outcome fields are newly reconstructed. Historical field names remain
    # the original predicate names; they never designate today's best/default.
    return {'schema':'gamma.comparator-carrier-replay.evidence.v1','complete':True,'historical_only':True,
      'promotion_allowed':False,'current_best_claim':False,'recorded54_commit':config['recorded54_commit'],
      'fixed51_commit':config['fixed51_commit'],'contract_sha256':c.hashfile(c.HERE/'contract.json'),
      'authorities':config['authorities'],'private_inputs':reader.private_reads,'comparator':{p:safe_arm(a) for p,a in policies.items()},
      'candidates':[safe_arm(a) for a in e['arms']],'restated54_predicates':outcome,
      'predictions58':{'R1_complete_comparator_resolution':meta['resolved'],'R2_no_historical_successor':outcome['selected_successor'] is None},
      'parent54_P4_preserved':None,'decoded_comparator_packets':800,'candidate_packets_replayed_here':0,
      'accepted54_packet_views':4800,'fresh_source_executions':0,'fresh_qualification_jobs':0,
      'ban_replay':ban.receipt(),'decoder_dependency_bytes':parent['decoder_dependency_bytes'],
      'offline_implementation_bytes':config['offline_implementation_bytes'],'model_bytes':0,'training_steps':0,
      'runtime_footprint':'Installed runtime size unmeasured; memory limits are per process.',
      'scope':'Corrected historical item54 versus fixed recorded item51-flat. Candidate scientific authority is accepted54 public replay, not a new replay or current-best selection.'}

def prose(value):
    lines=['# Item58 historical item54 versus item51 comparison','',
      'This separately reconstructed historical result does not change item54\'s unresolved record or claim the current best. No promotion is authorized.','',
      '| Fixed item51 policy | Validation N | Actions | C | C/N | Raw package bytes |',
      '| --- | ---: | ---: | ---: | ---: | ---: |']
    for policy,a in value['comparator'].items():
        v=a['validation'];lines.append(f"| {policy} | {v['selections']['total']} | {v['actions']['total']} | {v['single_character_codes']} | {v['single_character_fraction']:.8%} | {v['package_bytes']} |")
    lines+=['','Historical passing candidates: '+str(value['restated54_predicates']['ranked_passing_candidates'])+'.',
      'Candidate metrics and transfer predicates reproduce accepted54; 800 comparator packets decode, with zero candidate packets or fresh source qualifications replayed here.','']
    return '\n'.join(lines)

def main(out):
    out=Path(out);deadline=STARTED+c.WORKER_SECONDS
    signal.signal(signal.SIGALRM,lambda *_:(_ for _ in ()).throw(Deadline('Worker deadline')))
    writable=False
    try:
        arm(deadline);resource.setrlimit(resource.RLIMIT_AS,(c.MEMORY,)*2);os.sched_setaffinity(0,{0,1,2,3})
        assert not out.exists(),'Fresh output required';writable=True
        config=c.read(c.HERE/'contract.json');value=execute(config,deadline)
        value['worker_seconds']=time.monotonic()-STARTED;assert math.isfinite(value['worker_seconds']) and 0<=value['worker_seconds']<=c.WORKER_SECONDS
        value['peak_rss_kib']=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        validate_output(value);arm(deadline);out.mkdir(parents=True);(out/'REPORT.md').write_text(prose(value))
        arm(deadline);c.write(out/'results.json',value);arm(deadline)
        return value
    except BaseException as error:
        if writable:
            try:withdraw(out,error,deadline)
            except Deadline:pass
        raise
    finally:signal.setitimer(signal.ITIMER_REAL,0)

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--output',type=Path,required=True);a=ap.parse_args();main(a.output)
