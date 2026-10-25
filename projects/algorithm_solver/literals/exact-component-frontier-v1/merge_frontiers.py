"""Merge aggregate evidence only; no source/case loader or candidate execution."""
import hashlib,json
from fractions import Fraction
from pathlib import Path
from run_synthetic import serial

HERE=Path(__file__).resolve().parent
INPUTS=('JS-GLOBAL-RESULT-v3.json','JS-LONG-SPAN-RESULT-v1.json','JS-COMPLEMENTARY-RESULT-v1.json')


def main():
    archive={};pins={};decoder=None
    for name in INPUTS:
        raw=(HERE/name).read_bytes();pins[name]=hashlib.sha256(raw).hexdigest()
        r=json.loads(raw,object_hook=lambda x:Fraction(x['numerator'],x['denominator']) if set(x)=={'numerator','denominator'} else x)
        if r['fit_denominator']!=300 or r['source_opens']!=875 or r['candidate_execution'] or r['protected_access']:
            raise ValueError('unmatched or forbidden evidence scope')
        current=r['final_full_costs']['decoder_bytes']
        if decoder is not None and decoder!=current:raise ValueError('decoder charge drift')
        decoder=current
        for row in r['nondominated_ledger']:
            m=dict(row['metrics'])
            m.update(dictionary_bytes=8+4*m['entries']+m['literal_utf8_bytes'],packet_bytes=41*300+m['selections'],decoder_bytes=decoder)
            m['package_bytes']=m['dictionary_bytes']+m['packet_bytes']+decoder
            key=(row['dictionary_sha256'],row['source_choices_sha256'])
            if key in archive:
                if archive[key]['metrics']!=m:raise ValueError('same state hash, inconsistent metrics')
                archive[key]['evidence'].append(name)
            else:archive[key]=dict(dictionary_sha256=key[0],source_choices_sha256=key[1],metrics=m,evidence=[name])
    states=list(archive.values())
    objectives=('selections','characters','median','p95','entries','package_bytes')
    def dominates(a,b):return all(a['metrics'][k]<=b['metrics'][k] for k in objectives) and any(a['metrics'][k]<b['metrics'][k] for k in objectives)
    frontier=[s for s in states if not any(dominates(other,s) for other in states)]
    report=dict(schema='gamma.exact-component-frontier.aggregate-ledger.v1',input_sha256=pins,
        fit_denominator=300,source_variants=875,candidate_execution=False,protected_access=False,m1_qualified=False,
        cost_basis='Exact LTD1/LTV1 width8 formula including decoder; incumbent paths independently decoded in each source receipt, not every archived tradeoff',
        objectives=objectives,archived_states=len(states),nondominated_states=len(frontier),
        archive=states,frontier=frontier,search_complete=False,
        pending='Complementary worklist: bundle247 has97/257 active-entry deletions remaining;25 subsequent over-cap unions unpriced; one retirement-dependent prior repair dictionary unrecovered.')
    output=HERE/'JOINT-FRONTIER-v1.json'
    if output.exists():raise ValueError('preserve prior aggregate ledger')
    output.write_text(json.dumps(report,sort_keys=True,indent=2,default=serial)+'\n')
    print(json.dumps({'archived_states':len(states),'nondominated_states':len(frontier)}))

if __name__=='__main__':main()
