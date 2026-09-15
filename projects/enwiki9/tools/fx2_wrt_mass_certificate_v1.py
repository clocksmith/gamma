#!/usr/bin/env python3
"""Exact rational envelope for selectors among the already frozen streams."""
from collections import defaultdict
from fractions import Fraction
import hashlib
import json
import mmap
from pathlib import Path
import resource
import struct
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from lib.fx2_wrt_elision_v1 import Grammar
from lib.fx2_wrt_mass_v1 import row_masses,prefixes,correct
from tools.fx2_wrt_mass250k_v1 import feature_row


def ref(p):
    with p.open('rb') as f:h=hashlib.file_digest(f,'sha256').hexdigest()
    return dict(path=str(p.relative_to(ROOT)),bytes=p.stat().st_size,sha256=h)


def envelope(hist):
    # log2(1+x) <= x/ln2 < (81/56)*x for x>0.
    # ln2 = 2*atanh(1/3) > 2*(1/3+1/81) = 56/81.
    assert 2*(Fraction(1,3)+Fraction(1,81))==Fraction(56,81)
    value=sum((Fraction(delta,parent) for parent,delta in hist.items()),Fraction(0))
    upper=value*Fraction(81,56)
    return dict(strict=value>0,upper_numerator_hex=hex(upper.numerator),
        upper_denominator_hex=hex(upper.denominator),
        integer_upper_bits=(upper.numerator+upper.denominator-1)//upper.denominator,
        logarithms_evaluated=False,ideal_gain_only=True)


def main():
    resource.setrlimit(resource.RLIMIT_AS,(512<<20,512<<20))
    resource.setrlimit(resource.RLIMIT_CPU,(120,120))
    assert envelope({})['integer_upper_bits']==0
    assert envelope({1:1})['integer_upper_bits']==2
    assert envelope({2:1,4:2})==envelope({1:1})
    cid='fx2_wrt_mass250k_v1';out=ROOT/'results'/cid
    decision=json.loads((out/'decision.json').read_text());assert decision['status']=='passed'
    contract_path=ROOT/'operations/adaptive/experiments'/(cid+'.json')
    contract=json.loads(contract_path.read_text())
    for r in contract['inputs']:assert ref(ROOT/r['path'])['sha256']==r['sha256'].removeprefix('sha256:')
    meta=json.loads((out/'projection.json').read_text());body=(out/'population.modeled').read_bytes();counts=(out/'parent.q16').read_bytes()
    assert hashlib.sha256(body).hexdigest()==meta['modeled_sha256']
    assert hashlib.sha256(counts).hexdigest()==meta['parent_count_sha256']
    vocab=meta['vocabulary'];g=Grammar(meta['word_count'],vocab)
    hist={'KM':defaultdict(int),'KMS':defaultdict(int)};favorable={k:0 for k in hist}
    actions={a:hashlib.sha256() for a in 'KMS'};states=hashlib.sha256();states.update(g.state());features=hashlib.sha256()
    with (ROOT/meta['neural_path']).open('rb') as f,mmap.mmap(f.fileno(),0,access=mmap.ACCESS_READ) as neural:
        assert hashlib.sha256(neural).hexdigest()==meta['neural_sha256']
        for i,(parent,) in enumerate(struct.iter_unpack('<H',counts)):
            if i%8==0:
                row=feature_row(neural,i//8,2*len(vocab))
                if row is not None:
                    features.update(row);cm,am=prefixes(row_masses(row,vocab),g.allowed());cs,ss=prefixes(row_masses(row,vocab,True),g.allowed())
            y=body[i//8]>>(7-i%8)&1;forced=g.forced()
            if forced is not None:
                assert forced==y;q={a:0 for a in 'KMS'}
            else:
                q=dict(K=parent,M=correct(parent,g.prefix,cm,am),S=correct(parent,g.prefix,cs,ss))
                truth={a:p if y else 65536-p for a,p in q.items()};base=truth['K']
                for key in hist:
                    delta=max(truth[a] for a in key)-base
                    if delta:hist[key][base]+=delta;favorable[key]+=1
            for a in actions:actions[a].update(struct.pack('<HHB',parent,q[a],y))
            g.observe(y)
            if i%8==7:states.update(g.state())
    g.finish()
    for a in actions:
        r=decision['arms'][a]
        assert actions[a].hexdigest()==r['action_sha256']
        assert states.hexdigest()==r['grammar_state_sha256']
        assert features.hexdigest()==r['causal_feature_sha256']
    bounds={key:{**envelope(h), 'favorable_events':favorable[key],
                 'summed_positive_count_deltas_by_parent_truth_count':dict(sorted(h.items()))} for key,h in hist.items()}
    unary_path=ROOT/'operations/provenance/fx2_wrt_elision_exact_certificate_20260915.json'
    unary=json.loads(unary_path.read_text());assert unary['arms']['D']['upper_bits']==59
    for r in bounds.values():r['integer_upper_bits_including_parent_unary_effect']=59+r['integer_upper_bits']
    result=dict(schema='gamma.enwiki9.fixed-stream-selector-envelope.v1',candidate_id=cid,
        decision=ref(out/'decision.json'),experiment=ref(contract_path),unary_certificate=ref(unary_path),
        source=ref(Path(__file__).resolve()),bounds=bounds,action_state_feature_hashes_reproduced=True,
        arithmetic='Exact rational arithmetic. ln2 > 56/81 from two positive terms of the atanh series; ln(1+x)<=x.',
        family='Any truth-dependent selector or convex probability mixture of the named fixed integer probability streams, with parent predictions and all components unchanged. This even grants free clairvoyant choices.',
        exclusions='Not a bound on new probabilities, changed parent trajectories, new supports or new expert models. Not a finite-archive bound; arithmetic interval rounding/termination must be measured or separately bounded. Program, model and framing costs are omitted optimistically.',
        raw_bytes=250000,events=len(counts)//2,objective_credit_bytes=0,full_corpus_score_bytes=None,
        self_checks_passed=3,resource_caps=dict(address_space_bytes=512<<20,cpu_seconds=120))
    path=ROOT/'operations/provenance/fx2_wrt_mass_selector_certificate_20260915.json'
    with path.open('x') as f:json.dump(result,f,indent=2,sort_keys=True);f.write('\n')
    print(json.dumps({k:{f:v[f] for f in ['integer_upper_bits','integer_upper_bits_including_parent_unary_effect','favorable_events']} for k,v in bounds.items()}))


if __name__=='__main__':main()
