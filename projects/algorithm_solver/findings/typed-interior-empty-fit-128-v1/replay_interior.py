"""Fit-only diagnostic replay of frozen predictions; no model or training.

Only opt-in change: interior EMPTY op slots enter the bounded edit pool.
Keep historical raw/control evidence and charge saved inference separately.
"""
import json
from pathlib import Path
import time

from algsolve.records import LANE_ROOT as ROOT, load_hidden_tests
from algsolve.rebuild_recognition import Monitor, publish, sha
from algsolve.synth import typed_codec, typed_confirmation, development_tests, mine
from algsolve.synth.train_typed import problem_for
from algsolve.synth.typed_prediction_codec import PredictionCodec
from algsolve.synth.typed_comparison import run_route, score_fixed

OLD = ROOT/'runs/typed-composer-recovered-128-scorefix-v1'
OUT = ROOT/'runs/typed-interior-empty-fit-128-v1'
load = lambda p: json.loads(p.read_text())
rows = lambda p: [json.loads(s) for s in p.read_text().splitlines()]


def main():
    assert not OUT.exists(), 'Preserve prior attempts; no overwrite'
    prior=load(OLD/'candidate.json');config=prior['config'];identity=prior['codec_sha256']
    original={n:sha(OLD/n) for n in ['captures.jsonl','decisions.jsonl','scores.jsonl','candidate.json','summary.json']}
    saved=load(OLD/'summary.json')
    for n in ['captures.jsonl','decisions.jsonl','scores.jsonl','candidate.json']:
        assert original[n]==saved['artifacts_sha256'][n], n
    assert sha(ROOT/config['corpus'])==prior['checkpoint_contract']['dataset_sha256']
    pairs=typed_confirmation.verify_development(ROOT/config['corpus'],ROOT/config['qualification'],identity)
    fit={p['uid']:p for p in reversed(pairs) if p['learning_split']=='development_fit'}
    captures=[r for r in rows(OLD/'captures.jsonl') if r['split']=='development_fit']
    assert len(captures)==10 and {r['uid'] for r in captures}==set(fit)
    descriptor=prior['checkpoint_contract']['prediction_encoding']
    encoding=PredictionCodec(descriptor['slots'],descriptor['types'])
    assert encoding.descriptor()==descriptor
    current_sources={str(p.relative_to(ROOT)):sha(p) for p in sorted((ROOT/'algsolve').rglob('*.py'))}
    OUT.mkdir()
    publish(OUT/'candidate.json',dict(name=OUT.name,scope='Consumed development_fit diagnostic; no audit rerun or selection',
            original_files_sha256=original,source_sha256=current_sources,driver_sha256=sha(Path(__file__)),
            corpus_sha256=sha(ROOT/config['corpus']),codec_sha256=identity,
            control_config=config['correction'],candidate_config=dict(config['correction'],include_interior_empty=True),
            inference='Replay original codes/logits without mutation; no model inference. Historical shared inference time charged separately; hybrid total is not new end-to-end latency.',
            decision_budget=config['decision_wall_seconds'],protected_opened=False,training=False))
    monitor=Monitor([OUT,OLD,ROOT/config['corpus']],seconds=60);monitor.start()
    try:
        decisions=[]
        for i,capture in enumerate(captures):
            pair=fit[capture['uid']];problem=problem_for(pair)
            shared=sum(capture[n] for n in ['embedding_seconds','retrieval_seconds','prediction_seconds'])
            arms={}
            for arm in (['control','candidate'] if i%2==0 else ['candidate','control']):
                cfg=dict(config['correction'])
                if arm=='candidate':cfg['include_interior_empty']=True
                tick=time.perf_counter()
                arms[arm]=run_route('constrained',problem,capture['codes'],capture['logits'],encoding,
                                   identity,shared,cfg,config['decision_wall_seconds'])
                arms[arm]['measured_replay_wall_seconds']=time.perf_counter()-tick
                assert arms[arm]['raw_codes']==capture['codes']
            record=dict(uid=capture['uid'],split='development_fit',routes=arms)
            publish(OUT/f'decision-{i:04d}.json',record);decisions.append(record)
        publish(OUT/'decisions-seal.json',dict(candidate_sha256=sha(OUT/'candidate.json'),
                decisions={p.name:sha(p) for p in sorted(OUT.glob('decision-*.json'))}))
        scored=[]
        for i,decision in enumerate(decisions):
            pair=fit[decision['uid']];problem=problem_for(pair)
            tests,_=development_tests.select(pair['uid'],load_hidden_tests(problem))
            assert mine.digest(tests)==pair['provenance']['independent_tests_sha256']
            result=dict(uid=pair['uid'],routes={arm:score_fixed(r,problem,tests) for arm,r in decision['routes'].items()})
            publish(OUT/f'score-{i:04d}.json',result);scored.append(result)
        compact=[]
        for r in scored:
            compact.append(dict(uid=r['uid'],**{a:dict(valid=v['structurally_valid'],correct=v['accepted_correct'],
                wrong=v['wrong_acceptance'],decision=v['decision'],reason=v['reason'],
                correction_seconds=v['timing']['correction_seconds'],replay_wall_seconds=v['measured_replay_wall_seconds'],
                inherited_inference_seconds=v['timing']['shared_inference_seconds'],hybrid_total_seconds=v['timing']['total_seconds'],
                repair_reason=v['correction']['reason'],attempts=len(v['correction']['attempts']),
                interior_empty_slots=v['correction'].get('interior_empty_slots',[]),edits=v['correction']['edits'])
                for a,v in r['routes'].items()}))
        summary=dict(name=OUT.name,rows=compact,totals={a:dict(cases=10,
                valid=sum(r[a]['valid'] for r in compact),accepted_correct=sum(r[a]['correct'] for r in compact),
                wrong_acceptances=sum(r[a]['wrong'] for r in compact),abstentions=sum(r[a]['decision']=='abstain' for r in compact),
                correction_seconds=sum(r[a]['correction_seconds'] for r in compact)) for a in ['control','candidate']},
                resources=monitor.counters(),candidate_sha256=sha(OUT/'candidate.json'),
                promotion=False,limitations=['Fit-only consumed replay; no audit qualification','Original inference is cached, repair/execution costs freshly measured','No tuning or budget expansion after this result'])
        assert original=={n:sha(OLD/n) for n in original}, 'Historical evidence changed'
        assert current_sources=={str(p.relative_to(ROOT)):sha(p) for p in sorted((ROOT/'algsolve').rglob('*.py'))}
        publish(OUT/'summary.json',summary)
        print(json.dumps(summary,indent=2))
    except BaseException as e:
        publish(OUT/'failure.json',dict(error=type(e).__name__,detail=str(e)))
        raise
    finally:
        monitor.stop.set()


if __name__=='__main__':main()
