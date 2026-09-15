#!/usr/bin/env python3
"""Price one fixed sparse affine family from verified native feature records."""
import json
from pathlib import Path
import sys
from lib.fx2_sparse_residual_v1 import analyze
from tools.wrt_exact import parse_store_bytes, read_dictionary_words

def main():
    root,out=map(Path,sys.argv[1:])
    native=root/'results/fx2_residual_features250k_v3/work/native'
    stored=(root/'results/fx2_weight_native_transfer250k_q0_v1/work/native/opening.stored').read_bytes()
    raw=(native/'population.raw').read_bytes()
    parsed=parse_store_bytes(stored,read_dictionary_words(native/'dictionary/english.dic'))
    if parsed.decoded!=raw or parsed.stream[5:]!=stored[10:]:raise ValueError('WRT inverse differs')
    if len(raw)!=250000 or len(stored[10:])!=151210:raise ValueError('population differs')
    result=analyze((native/'encode.features').read_bytes(),stored[10:],(native/'encode.coder').read_bytes())
    old=json.loads((native.parent.parent/'bound.json').read_text())
    if result['residual_integer_sums']!=old['residual_integer_sums']:raise ValueError('independent first moments differ')
    result.update(exact_wrt_inverse=True,first_moments_match_prior=True,
        mathematical_scope='All sparse tables with at most one of32 fixed ternary features per bit row; nonzero coefficient integer -16384..16384 at scale32768. One version byte,eight mask bits,20bits per active row (5feature+1sign+14magnitude-minus-one),zero byte padding. Upper includes Q16 rounding,not finite arithmetic or shared code.',
        prior_exposure='Exposed opening250KB; no reserved input or new native predictor run.',
        scientific_verdict='Sparse ideal-plus-table family ruled out on this population.' if not result['fitting_permitted_by_bound'] else 'Upper bound does not exclude sparse-table gain; fitting and actual finite replay remain required.')
    with out.open('x') as f:json.dump(result,f,indent=2,sort_keys=True);f.write('\n')
    print(json.dumps({k:result[k] for k in ('paid_upper_bits_diagnostic','best_bound_active_rows','fitting_permitted_by_bound')}))

if __name__=='__main__':main()
