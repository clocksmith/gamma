"""Summarize measured tradeoffs without selecting an arbitrary weighted winner."""
import json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT.parent))
from literals import digest,json_bytes,dictionary_bytes,program_bytes,decode_bytes

def main():
 result=json.loads((ROOT/'results/results.json').read_bytes())
 control=json.loads((ROOT/'controls/results.json').read_bytes())
 execution=json.loads((ROOT/'execution/report.json').read_bytes())
 rows=result['trials']+control['trials'];front=set(control['combined_pareto_ids'])
 comparisons=[]
 for b in control['budget_comparisons']:
  comparisons.append({'dictionary_budget_bytes':b['dictionary_budget_bytes'],**{name:{'id':b[name]['id'],'metrics':b[name]['metrics']} for name in ('best_baseline','best_joint')}})
 count=0
 for directory in ('results/encodings','controls/encodings'):
  for file in (ROOT/directory).glob('*.json'):
   packet=json.loads(file.read_bytes());d=dictionary_bytes(packet['literals'])
   for key,p in packet['programs'].items():
    source=decode_bytes(d,program_bytes(packet['literals'],p['sequence']))
    if digest(source.encode())!=result['source_hashes'][key+'/'+packet['selection']['choices'][key]]:raise ValueError('source mismatch')
    count+=1
 summary={'schema':'gamma.literal-pass2-summary.v1','source_combinations':result['source_combinations_exhausted'],'main_trials':len(result['trials']),'dense_baseline_trials':len(control['trials']),'combined_pareto_points':len(front),'retained_packet_reconstructions_checked':count,'budget_comparisons':comparisons,'representative_shared_point':'fdd94e86cfb2e1ed4f07','representative_baseline_point':'f4b70f1e7083ca6f960d','new_execution':{k:execution[k] for k in ('new_source_versions_executed','new_cases','new_passed','all_variants_passed')},'conclusion':'Shared rewrites preserve tested outputs and offer some three-objective Pareto tradeoffs, but do not beat the denser unchanged-source control at any of the declared byte-budget checkpoints. No general compression or autonomous-assembly improvement claimed.','results_sha256':digest((ROOT/'results/results.json').read_bytes()),'controls_sha256':digest((ROOT/'controls/results.json').read_bytes()),'execution_sha256':digest((ROOT/'execution/report.json').read_bytes())}
 (ROOT/'summary.json').write_bytes(json_bytes(summary));print(json.dumps({'reconstructions':count,'pareto':len(front),'new_passed':execution['new_passed']}))
if __name__=='__main__':main()
