"""Authorized same-pair repeated-substring diagnostic; aggregate output only."""
import hashlib
import json
import resource
import time
import frontier as f
import repeated as r
from run_synthetic import aggregate,serial
from run_qualified_pair import CONFIG,CONFIG_SHA,IDS,KnownSpecService


def main():
    resource.setrlimit(resource.RLIMIT_AS,(512*1024**2,512*1024**2))
    resource.setrlimit(resource.RLIMIT_CPU,(60,60))
    started=time.monotonic();deadline=started+50
    report=dict(schema='gamma.exact-component-frontier.repeated-pair.v1',
        config_sha256=CONFIG_SHA,problem_ids=IDS,language='python',diagnostic_denominator=2,
        full_catalogue_denominator=4081,protected_access=False,candidate_execution=False,
        source_publication=False,original_m1='UNMET',status='started')
    service=KnownSpecService.from_config(CONFIG,CONFIG_SHA)
    metadata={};variants={}
    for pid in IDS:
        value=service.request(pid,language='python',include_source=False)
        impl=value.get('consumer_selection',{}).get('implementation',{})
        if impl.get('status')!='qualified' or impl.get('evidence_class')!='normative-typed-effects':
            raise ValueError('normative qualified metadata required before payload opens')
        metadata[pid]={k:impl[k] for k in ('source_sha256','receipt_sha256','canonical_variant_id')}
    for pid in IDS:
        value=service.request(pid,language='python',include_source=True)
        artifact=value.get('artifact',{})
        if artifact.get('status')!='materialized' or artifact.get('source_sha256')!=metadata[pid]['source_sha256']:
            raise ValueError('pinned source retrieval failed')
        text=artifact['source_utf8']
        if hashlib.sha256(text.encode()).hexdigest()!=metadata[pid]['source_sha256']:raise ValueError('hash drift')
        variants[pid]={'canonical':text}
    report['source_metadata']=metadata
    texts=[variants[pid]['canonical'] for pid in IDS]
    try:
        inventory,limits,alphabet,legal=r.complete_inventory(texts,deadline)
        report['inventory']=inventory
        report['inventory_method']='suffix automata plus prefix-doubling suffix array/LCP; linear stored index, shared substrings counted without quadratic materialization'
        all_u={};witness=[]
        for pid,text,lim in zip(IDS,texts,limits):
            cost,pieces=r.relaxed_path(text,lim,legal,deadline)
            all_u[pid]=dict(selections=cost[0],characters=cost[1])
            for piece in pieces:
                if len(piece)>1 and piece not in witness:witness.append(piece)
        report['capacity_relaxed_all_U']=dict(reachable=2,per_problem=all_u,
            selections=sum(x['selections'] for x in all_u.values()),characters=sum(x['characters'] for x in all_u.values()),
            caveat='Exact segmentation over complete shared legal substring U plus explicit characters; capacity relaxed, not a legal budgeted result')
        # Freeze BEFORE residual optimization: all distinct all-U witness literals,
        # first occurrence in declared IDS order then left-to-right path order, groups of6.
        groups=[tuple(witness[i:i+6]) for i in range(0,len(witness),6)]
        freeze=dict(residual_group_size=6,witness_candidates=len(witness),groups=len(groups),
            group_hashes=[hashlib.sha256(json.dumps(g).encode()).hexdigest() for g in groups],
            ordering='all-U witness first occurrence; declared IDs 1160 then 916, then source offset',
            fixed_basis='explicit source singletons initially; accepted full dictionary subsequently; unused entries retire after exact paths',
            guarantee='All subsets per frozen residual group and prior accepted basis only, NOT global optimum or complete pricing')
        report['residual_freeze']=freeze
        # Baseline always charges the whole alphabet; capacities too small remain absent.
        baseline,_,_,_=r.residual_frontier(variants,alphabet,[],deadline)
        report['baseline_profiles']=[dict(capacity=c,reachable=2 if row else 0,
            status='represented' if row else 'explicit_basis_exceeds_capacity',
            best=aggregate(row) if row else None) for c,row in baseline.items()]
        states,ledger,evaluations,complete=r.residual_frontier(variants,alphabet,groups,deadline)
        report['profiles']=[dict(capacity=c,reachable=2 if row else 0,
            status='represented_bounded_residual' if row else 'no_feasible_state_in_explored_residuals',
            best=aggregate(row) if row else None) for c,row in states.items()]
        report['nondominated_ledger']=[dict(stage=x['stage'],capacity=x['capacity'],state=aggregate(x['row'])) for x in ledger]
        report['evaluations']=evaluations
        report['status']='complete_frozen_residuals' if complete else 'incomplete_budget'
    except TimeoutError as exc:
        report['status']='incomplete_budget';report['reason']=str(exc)
    report['wall_seconds']=time.monotonic()-started
    report['peak_rss_kib']=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    report['code_sha256']={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in
        [f.HERE/'repeated.py',f.HERE/'run_repeated_pair.py',f.HERE/'frontier.py']}
    print(json.dumps(report,sort_keys=True,indent=2,default=serial))

if __name__=='__main__':main()
