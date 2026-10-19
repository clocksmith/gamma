"""Rebuild summary from sealed captures/decisions and completed scores; no execution."""
import hashlib,json
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[2]
TRAIN=ROOT/'runs/typed-literal-balanced-pair-128-v1';SCORE=ROOT/'runs/typed-literal-balanced-pair-128-v1-scoring';OUT=Path(__file__).parent
load=lambda p:json.loads(p.read_text())
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
contract=load(TRAIN/'contract.json');continuation=load(SCORE/'contract.json')
assert sha(TRAIN/'contract.json')==continuation['prior_contract_sha256']
assert all(sha(ROOT/n)==h for n,h in contract['sources_sha256'].items())
assert all(sha(Path(n))==h for n,h in contract['judge_sources_sha256'].items())
assert all(sha(TRAIN/n)==h for n,h in continuation['captures_sha256'].items())
assert all(sha(SCORE/n)==h for n,h in load(SCORE/'decisions-seal.json').items())
assert all(sha(TRAIN/arm/'model.pt')==h for arm,h in continuation['checkpoints_sha256'].items())
paths=sorted(SCORE.glob('score-*.json'));assert len(paths)==20
rows=[load(p) for p in paths];metrics={};by={}
for arm in ('control','balanced'):
    by[arm]={r['uid']:r for r in rows if r['arm']==arm};assert len(by[arm])==10;metrics[arm]={}
    for route in ('raw','guard','nearest'):
        rs=[r['routes'][route] for r in by[arm].values()];times=[r['timing']['total_seconds'] for r in rs]
        metrics[arm][route]=dict(cases=10,correct=sum(r['accepted_correct'] for r in rs),independently_correct=sum(r['independently_correct'] is True for r in rs),wrong=sum(r['wrong_acceptance'] for r in rs),infrastructure=sum(r['infrastructure_failure'] for r in rs),p95=float(np.percentile(times,95)),abstentions=sum(r['decision']=='abstain' for r in rs))
assert by['control'].keys()==by['balanced'].keys()
losses={r:[uid for uid in by['control'] if by['control'][uid]['routes'][r]['accepted_correct'] and not by['balanced'][uid]['routes'][r]['accepted_correct']] for r in ('raw','guard')}
quality=all(metrics['balanced'][r]['correct']>=metrics['control'][r]['correct']+1 and not losses[r] for r in ('raw','guard')) and not any(v['wrong'] or v['infrastructure'] for m in metrics.values() for v in m.values())
resources=[load(p/'failure.json')['resources'] for p in (TRAIN,SCORE)]
summary=dict(name='typed-literal-balanced-pair-128-v1',checkpoints_sha256=continuation['checkpoints_sha256'],metrics=metrics,lost_correct=losses,quality_pass=quality,latency_pass=metrics['balanced']['guard']['p95']<=2,release_qualified=False,protected_opened=False,audit_opened=False,training_steps=800,resources=resources,combined_recorded_wall_seconds=sum(r['wall_seconds'] for r in resources),recovery='Both400-step arms and20freshcaptures complete before immutable setup receipt rewrite failed. Scoring-only continuation sealed60public decisions and completed20score rows before a report variable typo. This rebuild performs no training, inference or scoring; both failures preserved.',scores_sha256={p.name:sha(p) for p in paths},literal_diagnostics_sha256=sha(SCORE/'literal-diagnostics.json'),report_sha256=sha(Path(__file__)))
text=json.dumps(summary,indent=2)+'\n';path=OUT/'summary.json'
if path.exists():assert path.read_text()==text
else:path.write_text(text)
print(text)
