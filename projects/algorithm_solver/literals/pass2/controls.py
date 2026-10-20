"""Denser unchanged-source controls to check sensitivity to merge-step spacing."""
import argparse,json,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT.parent))
from literals import digest,json_bytes,merged_dictionary,encode_corpus,pareto

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);args=p.parse_args()
 manifest=json.loads((ROOT/'source_manifest.json').read_text())
 texts={f.stem:f.read_bytes().decode('utf-8') for f in sorted((ROOT.parent/'sources/normalized').glob('*.js'))}
 assert len(texts)==20
 for key,text in texts.items():
  if digest(text.encode())!=manifest['source_hashes'][key+'/baseline']:raise ValueError('baseline drift')
 args.output.mkdir(parents=True,exist_ok=False);(args.output/'encodings').mkdir()
 rows=[];started=time.perf_counter()
 for steps in range(8,257,8):
  begin=time.perf_counter();packet=encode_corpus(texts,merged_dictionary(list(texts.values()),'lexical',steps,False))
  packet['selection']={'choices':dict.fromkeys(texts,'baseline'),'method':'lexical','merge_steps':steps,'explicit_helper_literal':False}
  identity='baseline-dense-'+str(steps)
  row={'id':identity,'choices':packet['selection']['choices'],'method':'lexical','merge_steps':steps,'explicit_helper_literal':False,'metrics':packet['metrics'],'search_seconds':time.perf_counter()-begin,'encoding_sha256':digest(json_bytes(packet))}
  rows.append(row);(args.output/'encodings'/f'{identity}.json').write_bytes(json_bytes(packet))
 original=json.loads((ROOT/'results/results.json').read_text())
 combined=original['trials']+rows
 budgets=[]
 for cap in [512,768,1024,1280,1536,2048,3072,4096,8192]:
  eligible=[r for r in combined if r['metrics']['dictionary_bytes']<=cap]
  baseline=[r for r in eligible if set(r['choices'].values())=={'baseline'}]
  if not eligible or not baseline:continue
  best=lambda rs:min(rs,key=lambda r:(r['metrics']['total_selections'],r['metrics']['dictionary_bytes'],r['metrics']['vocabulary_cardinality']))
  budgets.append({'dictionary_budget_bytes':cap,'best_baseline':best(baseline),'best_joint':best(eligible)})
 result={'schema':'gamma.literal-dense-control.v1','purpose':'Measure sensitivity to coarse baseline merge-step spacing; no additional source variants','trials':rows,'combined_pareto_ids':[r['id'] for r in pareto(combined)],'budget_comparisons':budgets,'elapsed_seconds':time.perf_counter()-started,'main_results_sha256':digest((ROOT/'results/results.json').read_bytes())}
 (args.output/'results.json').write_bytes(json_bytes(result))
 print(json.dumps({'trials':len(rows),'seconds':result['elapsed_seconds'],'budgets':[(b['dictionary_budget_bytes'],b['best_baseline']['metrics']['total_selections'],b['best_joint']['metrics']['total_selections']) for b in budgets]}))
if __name__=='__main__':main()
