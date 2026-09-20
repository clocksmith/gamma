"""Independent cost reduction of the closed native capture, without replay or tuning."""
from pathlib import Path
import hashlib,json,math,struct
root=Path(__file__).resolve().parents[2] if __file__.endswith('/verification_source.py') else Path('projects/enwiki9').resolve()
name='fx2_training_trajectory250k_q0_v1';out=root/'results'/name
report=json.loads((out/'comparison.json').read_bytes())
manifest=json.loads((out/'artifacts.json').read_bytes())
for item in manifest['artifacts']:
    path=root/item['path'];assert path.stat().st_size==item['bytes']
    with path.open('rb') as f:assert hashlib.file_digest(f,'sha256').hexdigest()==item['sha256']
intervals=((513,641),(3124,3252),(40225,40353),(69372,69500))
selected={i for a,b in intervals for i in range(a,b)};assert len(selected)==512
reductions={}
for arm in ('P','A','J'):
    prefix=out/'native'/f'{arm}-encode'
    rows=list(struct.iter_unpack('<QBBBBf',Path(str(prefix)+'.neural').read_bytes()))
    events=list(struct.iter_unpack('<HB',Path(str(prefix)+'.bits').read_bytes()))
    assert len(rows)==151210 and len(events)==1209680
    cells={key:{'n':[],'f':[],'count':0} for key in ('trained','other_neural','no_neural')}
    for i,(index,token,marker,available,reserved,p) in enumerate(rows):
        assert index==i and reserved==0 and available==(i>0 and rows[i-1][2]!=2)
        key='trained' if i in selected else 'other_neural' if available else 'no_neural'
        cells[key]['count']+=1
        if available:cells[key]['n'].append(-math.log(p,2))
        else:assert p==0 and i not in selected
        for q,truth in events[8*i:8*i+8]:
            assert truth in (0,1) and 1<=q<=65535
            cells[key]['f'].append(16-math.log(q if truth else 65536-q,2))
    reductions[arm]={}
    for key,cell in cells.items():
        actual={'targets':cell['count'],'coded_bits':len(cell['f']),'neural_bits':math.fsum(cell['n']) if key!='no_neural' else None,'final_bits':math.fsum(cell['f'])}
        expected=report['measurements'][arm]['partitions'][key]
        for field,value in actual.items():
            assert expected[field] is None if value is None else math.isclose(value,expected[field],rel_tol=0,abs_tol=1e-7),(arm,key,field)
        reductions[arm][key]=actual
    for suffix in ('.bits','.neural','.tokens','.priors'):
        digest=lambda action:hashlib.sha256((out/'native'/f'{arm}-{action}{suffix}').read_bytes()).hexdigest()
        assert digest('encode')==digest('decode')==digest('repeat')
value={'schema':'gamma.enwiki9.trajectory-verification.v1','verified_artifacts':len(manifest['artifacts']),'target_ranges':[list(v) for v in intervals],'trained_targets':512,'modeled_targets_per_arm':151210,'final_events_per_arm':1209680,'independently_reduced_costs':reductions,'inverse_repeat_trace_identity':True,'maximum_allowed_cost_reduction_difference_bits':1e-7,'limitations':'Independent Python cost reduction and hash verification, not an independent neural implementation, causal mixer intervention or full-corpus qualification.'}
with (out/'verification.json').open('x') as f:json.dump(value,f,indent=2);f.write('\n')
print(json.dumps(value,indent=2))
