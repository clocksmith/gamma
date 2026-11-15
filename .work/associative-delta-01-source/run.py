"""Frozen synthetic reference screen. No model or GPU dependency."""
import hashlib
import json
from pathlib import Path
import platform
import sys
from time import perf_counter_ns
import numpy as np
from delta import derive, apply

root = Path(__file__).parent
protocol_bytes = (root / 'protocol.json').read_bytes()
p = json.loads(protocol_bytes)
prefix = Path(sys.argv[1])
lock = {'protocol': p, 'sourceHashes': {name: hashlib.sha256((root/name).read_bytes()).hexdigest() for name in ['run.py','delta.py','protocol.json']}, 'python': platform.python_version(), 'numpy': np.__version__}
with Path(str(prefix)+'.lock.json').open('x') as f:
    json.dump(lock,f,indent=2)
rng = np.random.default_rng(p['seed'])
d, o = p['inputDimension'], p['outputDimension']
base = rng.normal(size=(o,d))/np.sqrt(d)
base_copy = base.copy()
rows = []
for family in p['families']:
    maps = [rng.normal(size=(o,2)) @ rng.normal(size=(2,d))/np.sqrt(2*d) for _ in range(p['tasksPerFamily'])]
    for index, task_map in enumerate(maps):
        keys = rng.normal(size=(p['demonstrations'],d))
        queries = rng.normal(size=(p['queries'],d))
        def outputs(x, matrix):
            shift = x @ matrix.T
            if family == 'nonlinear-tanh-shift':
                shift = np.tanh(shift)
            return x@base.T + shift
        values = outputs(keys,task_map)+rng.normal(scale=p['demonstrationNoise'],size=(len(keys),o))
        wrong = outputs(keys,maps[(index+1)%len(maps)])+rng.normal(scale=p['demonstrationNoise'],size=(len(keys),o))
        shuffled = values[rng.permutation(len(values))]
        random_matrix = rng.normal(size=(o,d))
        prediction_records = []
        arms = p['arms'][index%len(p['arms']):]+p['arms'][:index%len(p['arms'])]
        for arm in arms:
            start = perf_counter_ns()
            if arm == 'base':
                left,right = np.empty((o,0)),np.empty((0,d))
            elif arm == 'ridge':
                correction = np.linalg.solve(keys.T@keys+p['ridgeLambda']*np.eye(d),keys.T@(values-keys@base.T)).T
                left,right = correction,np.eye(d)
            else:
                labels = shuffled if arm == 'shuffled-labels' else wrong if arm == 'wrong-task' else values
                left,right = derive(base,keys,labels,p['rate'],p['epsilon'])
                if arm == 'norm-matched-random':
                    magnitude = np.linalg.norm(left@right)
                    left,right = random_matrix*(magnitude/np.linalg.norm(random_matrix)),np.eye(d)
            derive_ns = perf_counter_ns()-start
            start=perf_counter_ns()
            prediction=apply(base,left,right,queries)
            query_ns=perf_counter_ns()-start
            assert np.isfinite(prediction).all()
            # Roundtrip only the request-local update. Not neural regeneration.
            restored=json.loads(json.dumps({'left':left.tolist(),'right':right.tolist()}))
            np.testing.assert_allclose(apply(base,np.array(restored['left']).reshape(left.shape),np.array(restored['right']).reshape(right.shape),queries),prediction,rtol=0,atol=0)
            prediction_records.append((arm,prediction,derive_ns,query_ns,left.nbytes+right.nbytes))
        # Targets evaluated only after every arm has emitted predictions.
        target=outputs(queries,task_map)
        for arm,prediction,derive_ns,query_ns,update_bytes in prediction_records:
            rows.append({'family':family,'task':index,'arm':arm,'mse':float(np.mean((prediction-target)**2)),'deriveMs':derive_ns/1e6,'queryMs':query_ns/1e6,'updateBytes':update_bytes})
        np.testing.assert_array_equal(base,base_copy)
summary={}
for family in p['families']:
    summary[family]={}
    baseline={r['task']:r['mse'] for r in rows if r['family']==family and r['arm']=='base'}
    for arm in p['arms']:
        selected=[r for r in rows if r['family']==family and r['arm']==arm]
        summary[family][arm]={'meanMSE':float(np.mean([r['mse'] for r in selected])),'winsAgainstBase':sum(r['mse']<baseline[r['task']] for r in selected),'tasks':len(selected),'medianDeriveMs':float(np.median([r['deriveMs'] for r in selected])),'medianQueryMs':float(np.median([r['queryMs'] for r in selected])),'updateBytes':selected[0]['updateBytes']}
result={'classification':p['classification'],'complete':True,'lockSha256':hashlib.sha256(json.dumps(lock,sort_keys=True).encode()).hexdigest(),'summary':summary,'rows':rows}
with Path(str(prefix)+'.result.json').open('x') as f:
    json.dump(result,f,indent=2)
print(json.dumps(summary,indent=2))
