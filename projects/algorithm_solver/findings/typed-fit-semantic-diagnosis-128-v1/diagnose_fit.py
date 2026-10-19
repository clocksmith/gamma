"""Read-only attribution against exposed qualified fit targets; no prediction."""
import hashlib
import json
from pathlib import Path

from algsolve.records import LANE_ROOT as ROOT
from algsolve.synth.typed_prediction_codec import PredictionCodec, OPS


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    old=ROOT/'runs/typed-composer-recovered-128-scorefix-v1'
    replay=ROOT/'runs/typed-interior-empty-fit-128-v1'
    corpus=ROOT/'runs/typed-real-dev-v5/pairs.jsonl'
    metadata=json.loads((old/'candidate.json').read_text())
    assert sha(corpus)==metadata['checkpoint_contract']['dataset_sha256']
    descriptor=metadata['checkpoint_contract']['prediction_encoding']
    encoding=PredictionCodec(descriptor['slots'],descriptor['types'])
    assert encoding.descriptor()==descriptor
    pairs=[json.loads(s) for s in corpus.read_text().splitlines()]
    fit=[p for p in pairs if p['learning_split']=='development_fit']
    positives=total=0
    for p in fit:
        values=[v for row in encoding.encode(p['target']['program'])['bits'] for v in row if v!=-100]
        total+=len(values);positives+=sum(values)
    records=[]
    sources={str(p.relative_to(ROOT)):sha(p) for p in [corpus,old/'candidate.json',old/'captures.jsonl']}
    for path in sorted(replay.glob('score-*.json')):
        sources[str(path.relative_to(ROOT))]=sha(path)
        row=json.loads(path.read_text());result=row['routes']['candidate']
        codes=result['correction']['final_codes'];options=[]
        for p in fit:
            if p['uid']!=row['uid']:continue
            target=encoding.encode(p['target']['program']);errors={}
            for field,values in target.items():
                if field=='bits':
                    errors[field]=sum(v!=-100 and v!=codes[field][i][j] for i,vs in enumerate(values) for j,v in enumerate(vs))
                else:
                    errors[field]=sum(v!=-100 and v!=codes[field][i] for i,v in enumerate(values))
            options.append((sum(v for k,v in errors.items() if k!='bits'),errors['bits'],p['graph_sha256'],errors,target))
        best=min(options,key=lambda v:v[:3]);differences=[]
        def value(bits):return (-1 if bits[0] else 1)*sum(b<<j for j,b in enumerate(bits[1:]))
        for i,vs in enumerate(best[4]['bits']):
            if -100 not in vs and vs!=codes['bits'][i]:
                differences.append(dict(slot=i,predicted=value(codes['bits'][i]),target=value(vs),operator=OPS[codes['op'][i]]))
        op_diffs=[dict(slot=i,predicted=OPS[codes['op'][i]],target=OPS[v]) for i,v in enumerate(best[4]['op']) if v!=codes['op'][i]]
        records.append(dict(uid=row['uid'],accepted_correct=result['accepted_correct'],route_reason=result['reason'],
                            qualified_target_count=len(options),closest_target_sha256=best[2],
                            selection='minimum nonliteral errors, then bit errors, then target hash; diagnostic only',
                            errors=best[3],literal_differences=differences,operation_differences=op_diffs))
    report=dict(scope='Post-score consumed-fit attribution, not a solver or correctness improvement',
                inputs_sha256=sources,fit_graphs=len(fit),fit_problems=len(records),rows=records,
                literal_supervision=dict(positive_bits=positives,supervised_bits=total,positive_fraction=positives/total,
                    all_zero_bit_accuracy=(total-positives)/total),
                limitations=['Closest target comparison is not causal training attribution','Literal imbalance is a plausible mechanism, not proven cause','No target-derived edits applied to a solver','No training, new model inference, audit rerun or protected access'])
    out=ROOT/'findings/typed-fit-semantic-diagnosis-128-v1'
    out.mkdir(exist_ok=True)
    with (out/'diagnosis.json').open('x') as stream:stream.write(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report['literal_supervision']))


if __name__=='__main__':main()
