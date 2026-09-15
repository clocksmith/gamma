from pathlib import Path
import json,hashlib,sys
sys.path.insert(0,str(Path.cwd()))
from tools.fx2_compact_complement_bound_v1 import aligned_counts,analyze
out=Path('results/fx2_head_transport_opening250k_v2');native=out/'work/native'
def ref(p):
 p=Path(p)
 with p.open('rb') as f:h=hashlib.file_digest(f,'sha256').hexdigest()
 return dict(path=str(p),bytes=p.stat().st_size,sha256=h)
d=json.load(open(out/'decision.json'));assert d['status']=='passed' and d['all_parent_probability_and_truth_identity']
g=json.load(open('run_logs/adaptive/20260915T025312Z_f55e6caa2e.resources/guard.json'));assert g['status']=='complete' and not any(g['guards'].values())
body=Path('results/fx2_weight_native_transfer250k_q0_v1/work/native/opening.stored').read_bytes()[10:];assert len(body)==151210
left=native/'P-encode.coder';right=native/'D-encode.coder';pa,da=aligned_counts(left.read_bytes(),right.read_bytes(),body)
a=analyze(pa,da,block_bytes=())
r=dict(schema='gamma.enwiki9.closed-pair-oracle.v1',inputs=[ref(left),ref(right),ref(out/'decision.json'),ref('tools/fx2_compact_complement_bound_v1.py')],classification='Posthoc read-only diagnostic of closed traces; no new corpus encode or prediction mutation.',analysis=a,proof='For every event, every convex combination of these two fixed Q16 probability vectors assigns the actual truth at most max(P,D). Balanced exact integer products and shifts certify the ceiling of log2(product(max(P,D)/P)). This oracle sees future truth and is not a decoder.',limits=['Bound covers only the frozen final P and D streams, not alternative head states, underlying unmixed transported experts, other populations or changed trajectories.','It bounds ideal probability savings, not finite archive savings or a prize score.','Observed source/binary sum is an overlapping inventory sensitivity, not the cost of every hypothetical implementation.'],objective_credit_bytes=0,full_corpus_score_bytes=None)
p=Path('/run/user/1000/head_transport_pair_audit_20260915.json');p.write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(a))
