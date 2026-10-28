"""Original independent cases plus distinct-reviewer witnesses, before repair execution."""
import hashlib
import json
from pathlib import Path
import cases as base_cases
import oracles as o

IDS=base_cases.IDS

def build(statements=None):
    data=base_cases.build(statements)
    seen={pid:{json.dumps(c['args'],sort_keys=True,separators=(',',':')) for c in values} for pid,values in data.items()}
    def add(pid,args,want,category):
        actual=o.expected(pid,args)
        assert o.exact(actual,want),(pid,'independent-reference-disagreement')
        key=json.dumps(args,sort_keys=True,separators=(',',':'))
        if key not in seen[pid]:
            seen[pid].add(key);data[pid].append({'args':args,'expected':actual,'category':category})
    packet=json.loads((Path(__file__).parent/'cohort68-repairs/review/execution-suggestions.json').read_bytes())
    for case in packet['cases']:
        if 'expected' in case:want=case['expected']
        else:
            assert case['problem_id']==386
            want=sorted(range(1,case['args'][0]+1),key=str)
            assert len(want)==case['expected_length']
            assert hashlib.sha256(json.dumps(want,separators=(',',':')).encode()).hexdigest()==case['expected_value_sha256']
        add(case['problem_id'],case['args'],want,'distinct-reviewer-targeted')
    add(287,[list(range(1,100001))+[100000]],100000,'maximum-length-selfcycle')
    add(287,[list(range(1,100001))+[1]],1,'maximum-length-fullcycle')
    matrix=[[r*300+c-45000 for c in range(300)] for r in range(300)]
    zeros=[[0]*300 for _ in range(300)]
    for k in (1,45000,90000):
        add(378,[matrix,k],k-1-45000,'maximum-square-rank-boundary')
        add(378,[zeros,k],0,'maximum-square-duplicate-multiplicity')
    return data
