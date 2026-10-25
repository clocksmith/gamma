"""Authorized two-ID metadata-first diagnostic; no candidate execution or source output."""
import hashlib
import json
from pathlib import Path
import resource
import sys
import time
import frontier as f
from run_synthetic import serial, aggregate

REPO=f.HERE.parents[3]
sys.path.insert(0,str(REPO))
from projects.algorithm_solver.catalogue.known_spec_service import KnownSpecService

CONFIG='/workspace/shared/gamma-known-spec-service-v9b-20261025-2029/config.json'
CONFIG_SHA='c805894d69b36fefbc4cb0af6204872dfe9b655e719679019a088513db2bcea2'
IDS=('leetcode:1160','leetcode:916')


def main():
    resource.setrlimit(resource.RLIMIT_AS,(512*1024**2,512*1024**2))
    resource.setrlimit(resource.RLIMIT_CPU,(60,60))
    started=time.monotonic()
    service=KnownSpecService.from_config(CONFIG,CONFIG_SHA)
    metadata={}
    # Validate BOTH metadata selections before opening either payload.
    for pid in IDS:
        result=service.request(pid,language='python',include_source=False)
        impl=result.get('consumer_selection',{}).get('implementation',{})
        if impl.get('evidence_class')!='normative-typed-effects' or impl.get('status')!='qualified':
            raise ValueError('required qualified normative receipt absent')
        metadata[pid]={k:impl[k] for k in ('source_sha256','receipt_sha256','canonical_variant_id')}
    variants={}
    for pid in IDS:
        result=service.request(pid,language='python',include_source=True)
        artifact=result.get('artifact',{})
        if artifact.get('status')!='materialized' or artifact.get('source_sha256')!=metadata[pid]['source_sha256']:
            raise ValueError('authorized source materialization failed')
        text=artifact['source_utf8']
        if hashlib.sha256(text.encode()).hexdigest()!=metadata[pid]['source_sha256']:
            raise ValueError('source identity mismatch')
        variants[pid]={'canonical':text}
        metadata[pid]['source_bytes']=len(text.encode())
    witnesses={}
    whole=[s for rows in variants.values() for s in rows.values()]
    # Ban whole source and complete solve-body containment, ignoring whitespace.
    compact=lambda s: ''.join(s.split())
    banned=[compact(s) for s in whole]
    for s in whole:
        lines=s.splitlines(keepends=True)
        for i,line in enumerate(lines):
            if line.lstrip().startswith('def solve('):
                body=compact(''.join(lines[i+1:]))
                if body:
                    banned.append(body)
    for pid,rows in variants.items():
        lines=rows['canonical'].splitlines(keepends=True)
        for length in (1,2):
            for at in range(len(lines)-length+1):
                literal=''.join(lines[at:at+length])
                if literal:
                    witnesses.setdefault(literal,set()).add(pid)
    legal=lambda s: (len(s)==1 or len(witnesses[s])>=2) and not any(b in compact(s) for b in banned)
    universe=tuple(sorted(s for s in witnesses if legal(s)))
    report=dict(schema='gamma.exact-component-frontier.qualified-pair.v1',
                config_sha256=CONFIG_SHA,language='python',problem_ids=IDS,
                family='character-frequency constraints',source_metadata=metadata,
                diagnostic_denominator=2,full_catalogue_denominator=4081,
                candidate_execution=False,protected_access=False,source_publication=False,
                universe_policy='Every witnessed complete line and adjacent two-line merge; multichar requires two distinct problem witnesses; whole-source/complete-body containment excluded.',
                universe_entries=len(universe),proposed_entries=len(witnesses),
                universe_sha256=hashlib.sha256(json.dumps(universe).encode()).hexdigest(),
                search_scope='Restricted finite U, one canonical V/problem; not complete pricing, full-corpus result, M1 or all-input proof.',
                original_m1='UNMET',profiles=[])
    if len(universe)>18:
        report['status']='blocked_exact_universe_cap'
    else:
        for capacity in f.PROFILES:
            result=f.solve(variants,universe,capacity,seconds=min(8,55-(time.monotonic()-started)),legal=legal)
            report['profiles'].append(dict(capacity=capacity,status=result['status'],
                dictionaries=result['dictionaries'],evaluations=result['evaluations'],
                best=aggregate(result['best']) if result['best'] else None,
                nondominated_ledger=[aggregate(r) for r in result['frontier']]))
        report['status']='complete_restricted_diagnostic' if all(p['status']!='incomplete_budget' for p in report['profiles']) else 'incomplete'
    report['unlimited_U_reachable']=sum(f.exact_path(rows['canonical'],universe) is not None for rows in variants.values())
    report['next_step']='Freeze a deterministic cross-problem repeated-substring trie universe and a bounded exact residual neighborhood; do not infer impossibility from this line-only U. Any larger compute or further source variant access requires coordination.'
    report['wall_seconds']=time.monotonic()-started
    report['peak_rss_kib']=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    print(json.dumps(report,sort_keys=True,indent=2,default=serial))


if __name__=='__main__':
    main()
