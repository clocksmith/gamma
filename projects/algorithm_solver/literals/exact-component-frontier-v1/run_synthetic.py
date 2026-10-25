"""Public synthetic controls only; no source/case paths accepted by this runner."""
import hashlib
import json
from pathlib import Path
import resource
import time
from fractions import Fraction
import frontier as f


def serial(value):
    if isinstance(value,Fraction):
        return {'numerator':value.numerator,'denominator':value.denominator}
    raise TypeError(type(value).__name__)


def aggregate(row):
    return dict(metrics=row['metrics'], unreachable=row['unreachable'],
                dictionary_sha256=hashlib.sha256(f.base.dictionary_bytes(list(row['dictionary']))).hexdigest(),
                selected_variants={p:k for p,(k,_) in row['selected'].items()})


def main():
    resource.setrlimit(resource.RLIMIT_AS,(512*1024**2,512*1024**2))
    resource.setrlimit(resource.RLIMIT_CPU,(60,60))
    start=time.monotonic()
    # Public inert strings authored for this control, not executable candidates.
    variants={'p':{'left':'ababa','right':'aaaaaa'},'q':{'left':'babab','right':'bbbbbb'}}
    stages=[]
    # All merge lengths 1..3, every witnessed literal; no random/top-K sweep.
    for stage,u in enumerate(f.expansion_levels(variants,3),1):
        for capacity in f.PROFILES:
            result=f.solve(variants,u,capacity,seconds=min(10,55-(time.monotonic()-start)))
            stages.append(dict(stage=stage,capacity=capacity,status=result['status'],
                               universe_entries=result['universe_entries'],dictionaries=result['dictionaries'],
                               evaluations=result['evaluations'],best=aggregate(result['best']) if result['best'] else None,
                               nondominated_ledger=[aggregate(r) for r in result['frontier']]))
    pins=[f.HERE/'frontier.py',f.HERE/'run_synthetic.py',f.HERE/'test_frontier.py',
          f.LIT/'explicit-basis-v2/segmentation.py',f.LIT/'readable-v1/literal_codec.py',f.LIT/'literals.py']
    report=dict(schema='gamma.exact-component-frontier.synthetic.v1',
                status='complete' if all(x['status']=='optimal_finite_U_V' for x in stages) else 'incomplete',
                source_class='public inert synthetic strings',candidate_execution=False,protected_access=False,
                original_m1='UNMET; synthetic control is not a qualification population',
                objective=['maximum coverage','minimum selections N','minimum absolute singleton selections C'],
                source_choice='exhaustive variant cross-product with exact minimum-N-then-C segmentation',
                median='exact arithmetic mean of two middle counts for even population',
                scope='Exact only for supplied finite U/V and gates; never global impossibility',
                code_sha256={str(p.relative_to(f.LIT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in pins},
                wall_seconds=time.monotonic()-start,peak_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
                stages=stages)
    # Preserve old runs: stdout only; caller chooses a new evidence file.
    print(json.dumps(report,sort_keys=True,indent=2,default=serial))


if __name__=='__main__':
    main()
