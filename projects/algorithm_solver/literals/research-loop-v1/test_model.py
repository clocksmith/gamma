import itertools,json,math
from pathlib import Path
import model
C=Path(__file__).resolve().parent
fixtures=[(['ababa','babab'],['a','b','ab','ba','aba'],3),(['aaa','aab'],['a','b','aa','ab'],3),(['éaé','aéa'],['a','é','aé','éa'],3)]
rows=[]
for texts,pool,cap in fixtures:
 mandatory={i for i,s in enumerate(pool) if len(s)==1};optional=set(range(len(pool)))-mandatory
 for width in [7,8]:
  for objective in ['selections','package_bytes']:
   m=model.build(texts,pool,cap,width,objective);best=float('inf');enumerated=0
   for n in range(cap-len(mandatory)+1):
    for chosen in itertools.combinations(sorted(optional),n):
     cost=model.evaluate(texts,pool,m['graphs'],mandatory|set(chosen),width)[objective];best=min(best,cost);enumerated+=1
   lp=model.solve(m,False,2);ip=model.solve(m,True,2)
   assert lp['success'] and ip['success'];assert lp['constraint_violation']<1e-6 and ip['constraint_violation']<1e-6
   assert abs(ip['objective']-best)<1e-6,(texts,width,objective,ip['objective'],best);assert lp['objective']<=best+1e-6
   for rounding in ['Det','Bias','Int']:
    selected=model.rounded(m,lp,rounding);v=model.evaluate(texts,pool,m['graphs'],selected,width);assert v['entries']<=cap and mandatory<=selected
   rows.append({'texts':texts,'width':width,'objective':objective,'enumerated_dictionaries':enumerated,'enumerated_optimum':best,'MIP_optimum':ip['objective'],'LP_lower_bound':lp['objective']})
(C/'fixture-tests.json').write_text(json.dumps({'passed':True,'cells':len(rows),'rounding_checks':3*len(rows),'rows':rows},indent=2)+'\n');print(json.dumps({'passed':True,'cells':len(rows),'rounding_checks':3*len(rows)}))
