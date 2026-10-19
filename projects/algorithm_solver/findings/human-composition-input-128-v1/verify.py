"""Execute original authored binary-input graphs on bounded exhaustive domains."""
import hashlib,itertools,json
from pathlib import Path
from algsolve.synth.typed_program import execute
from algsolve.synth.typed_recipes import catalog
root=Path(__file__).parent
fixture_path=root/'fixtures.json'
fixtures=json.loads(fixture_path.read_text())
arrays=[list(x) for n in range(6) for x in itertools.product((-1,0,1),repeat=n)]
rows=[]
for fixture in fixtures['fixtures']:
    identity=fixture['id']; graph=fixture['program']; count=0
    cases=({'a':a,'b':b} for a in range(-10,11) for b in range(-10,11)) if identity in ('add','shifted') else ({'values':v} for v in arrays)
    for args in cases:
        if identity=='add': expected=args['a']+args['b']
        elif identity=='shifted': expected=args['a']+args['b']-1
        elif identity=='sort': expected=sorted(args['values'])
        elif identity=='unique': expected=list(dict.fromkeys(args['values']))
        else: expected=len(args['values'])!=len(set(args['values']))
        actual=execute(graph,args,recipes=catalog())
        assert type(actual) is type(expected) and actual==expected,(identity,args,actual,expected)
        count+=1
    rows.append(dict(id=identity,passed=count,binary_presses=fixture['tape']['metrics']['binary_presses'],entry_actions=fixture['tape']['metrics']['total_actions'],encoding_costs=fixture['encoding_costs']))
result=dict(scope='Original authored graphs and oracles, automated bounded execution. Not independent human or protected autonomous evaluation.',fixtures_sha256=hashlib.sha256(fixture_path.read_bytes()).hexdigest(),rows=rows,total_checks=sum(row['passed'] for row in rows))
print(json.dumps(result,indent=2))
