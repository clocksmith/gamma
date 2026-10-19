"""Read sealed fit evidence; never execute candidates or read independent tests."""
import hashlib,itertools,json
from pathlib import Path
from algsolve.records import LANE_ROOT as ROOT
from algsolve.synth.typed_prediction_codec import PredictionCodec,OPS

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text())
def rows(p):return [json.loads(s) for s in p.read_text().splitlines() if s.strip()]

def main():
 old=ROOT/'runs/typed-composer-recovered-128-scorefix-v1';new=ROOT/'runs/typed-literal-margin-fit-128-v1'
 replay=ROOT/'runs/typed-interior-empty-fit-128-v1';out=Path(__file__).parent
 sources=[old/'scores.jsonl',old/'captures.jsonl',old/'candidate.json',ROOT/'runs/typed-real-dev-v5/pairs.jsonl']
 sources+=sorted(new.glob('*.json'))+sorted(replay.glob('score-*.json'))
 hashes={str(p.relative_to(ROOT)):sha(p) for p in sources}
 original={r['uid']:r for r in rows(old/'scores.jsonl') if r['split']=='development_fit'}
 captures={r['uid']:r for r in rows(old/'captures.jsonl') if r['split']=='development_fit'}
 fits=[p for p in rows(ROOT/'runs/typed-real-dev-v5/pairs.jsonl') if p['learning_split']=='development_fit']
 desc=read(old/'candidate.json')['checkpoint_contract']['prediction_encoding'];encoding=PredictionCodec(desc['slots'],desc['types'])
 diag=read(ROOT/'findings/typed-fit-semantic-diagnosis-128-v1/diagnosis.json');diag={r['uid']:r for r in diag['rows']}
 comparisons=[];coverage=[]
 for path in sorted(new.glob('score-*.json')):
  current=read(path);uid=current['uid'];index=path.stem.split('-')[1];capture=read(new/f'capture-{index}.json')
  assert captures[uid]['codes']==capture['codes']
  phase={key:dict(old=captures[uid][key],new=capture[key]) for key in ['embedding_seconds','retrieval_seconds','prediction_seconds']}
  arms={}
  for old_arm,new_arm in [('constrained','structural_control'),('nearest_training_graph','nearest_training_graph')]:
   a=original[uid]['routes'][old_arm];b=current['routes'][new_arm]
   def compact(x):
    return {**{k:x.get(k) for k in ['decision','reason','accepted_correct','independently_correct','timing']},
      'public_started':x['public'] is not None,'public_reason':(x['public'] or {}).get('reason'),
      'sandbox_wall_seconds':(x['public'] or {}).get('wall_seconds'),
      'independent_reason':(x['independent'] or {}).get('reason')}
   lost=a['accepted_correct'] and not b['accepted_correct']
   if lost:
    assert a['source_sha256']==b['source_sha256'] and b['independently_correct'] is True
    assert capture['embedding_seconds']>2 and b['public'] is None
   arms[new_arm]=dict(old=compact(a),new=compact(b),lost_correct=lost,
     source_equal=a.get('source_sha256')==b.get('source_sha256'),graph_equal=a.get('graph_sha256')==b.get('graph_sha256'),
     attribution='fresh embedding alone exceeds total budget; no sandbox started' if lost else 'no accepted-correct loss')
  comparisons.append(dict(uid=uid,phases=phase,routes=arms))
  if not diag[uid]['errors']['bits'] and not diag[uid]['errors']['op']:continue
  # Deliberately diagnostic: old structurally repaired result supplies the graph,
  # never an altered route or fresh decision. Labels are compared after ranking.
  codes=read(replay/f'score-{index}.json')['routes']['candidate']['correction']['final_codes']
  assert codes['bits']==capture['codes']['bits']
  logits=capture['logits']['bits'];pool=[]
  for slot,op in enumerate(codes['op']):
   for bit in (range(129) if OPS[op]=='int' else [1] if OPS[op]=='bool' else []):
    pool.append((abs(logits[slot][bit]),slot,bit))
  pool=sorted(pool);selected=pool[:8];ranks={(s,b):i+1 for i,(_,s,b) in enumerate(pool)}
  proposals=sorted((sum(p for p,_,_ in combo),tuple(sorted((s,b) for _,s,b in combo)))
                   for n in [1,2] for combo in itertools.combinations(selected,n))
  target=next(p for p in fits if p['graph_sha256']==diag[uid]['closest_target_sha256']);target=encoding.encode(target['target']['program'])
  changes=tuple((s,b) for s,vs in enumerate(target['bits']) for b,v in enumerate(vs) if v!=-100 and v!=codes['bits'][s][b])
  proposal_rank=next((i+1 for i,(_,coords) in enumerate(proposals) if coords==changes),None)
  coverage.append(dict(uid=uid,nonliteral_errors=sum(v for k,v in diag[uid]['errors'].items() if k!='bits'),
    required_bit_count=len(changes),required_bit_margin_ranks=[ranks.get(c) for c in changes],
    all_required_bits_in_pool=all(ranks.get(c,99999)<=8 for c in changes),
    exact_label_proposal_rank=proposal_rank,within_first_four_proposals=proposal_rank is not None and proposal_rank<=4,
    target_sha256=diag[uid]['closest_target_sha256'],
    caveat='Exact qualified-label reachability only; no alternative semantic solution excluded; proposal rank is not execution rank'))
 result=dict(scope='Sealed consumed-fit timing and post-score literal ranking diagnosis; no new inference, executions or decisions',
  input_sha256=hashes,rows=comparisons,literal_coverage=coverage,
  losses={a:[r['uid'] for r in comparisons if r['routes'][a]['lost_correct']] for a in ['structural_control','nearest_training_graph']})
 assert hashes=={str(p.relative_to(ROOT)):sha(p) for p in sources}
 with (out/'reconciliation.json').open('x') as f:json.dump(result,f,indent=2);f.write('\n')
 print(json.dumps(dict(losses=result['losses'],literal_coverage=coverage),indent=2))
if __name__=='__main__':main()
