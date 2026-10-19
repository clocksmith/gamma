from pathlib import Path
import json,hashlib,sys,importlib.util,math,itertools
T=Path('/home/x/Documents/Codex/2026-10-19/task');R=Path('/home/x/deco/gamma/projects/algorithm_solver');OUT=R/'runs/js-corpus-b01-b02-review-128-v1';PACK=T/'js-corpus-wave-001';sys.path[:0]=[str(R),str(R/'findings/js-exact-integer-transport-128-v1')]
from algsolve import validate
from algsolve.judge import judge,sandbox
import exact_integer
namespace={};prefix=(T/'b01-b02-check-style.py').read_text().split('control_args=')[0].replace(" assert all('error' not in v for v in records[:-1]),records\n",'');exec(prefix,namespace);run=namespace['run']
manifest=json.loads((PACK/'manifest.json').read_text());rows={r['id']:r for r in manifest['rows']};records=[]
def source(n,suffix='role-style'):
 return (R/'runs/js-corpus-wave-001'/rows[n]['batch_id']/f'{n:04d}-{suffix}.js').read_text()
def check(n,calls,expected=None):
 row=rows[n];a=run(source(n,'owner-original'),row['entry']['method'],row['params'],calls);b=run(source(n),row['entry']['method'],row['params'],calls);assert a==b,(n,'style behavior')
 if expected is not None:assert [r.get('result') for r in b]==expected,(n,b,expected)
 records.append(dict(id=n,calls=calls,observations=b,original_normalized_equivalent=True));return b
# Codepoint behavior, including an intentionally decomposed combining sequence.
check(3,[['\U0001f600a\U0001f600'],['e\u0301e']], [2,2]);check(6,[['\U0001f600ab',2]],['\U0001f600ba']);check(10,[['\U0001f600','.'],['\U0001f600\U0001f600','\U0001f600*']],[True,True]);check(14,[[['\U0001f600a','\U0001f600b']]],['\U0001f600'])
# UTF16 extensions differ from Python codepoint semantics; these are outside ASCII scope.
check(28,[['\U0001f600a','a']],[2]);check(30,[['\U0001f600a',['a']]],[ [2] ]);check(44,[['\U0001f600','?']],[False])
check(7,[[1534236469],[-2147483648],[1463847412]],[0,0,2147483641]);check(8,[['-2147483649'],['2147483648'],['\t42'],['-0']],[-2147483648,2147483647,0,0]);check(29,[[-2147483648,-1],[-2147483648,1],[7,-3]],[2147483647,-2147483648,-2])
check(43,[['9'*200,'9'*200]],[str(int('9'*200)**2)])
# Actual mutable references, not just serialized result equality.
node=lambda a:{'__list_node__':a}
for n,calls in [(19,[[node([1,2,3]),2]]),(21,[[node([1,3]),node([2,4])]]),(23,[[[node([-2,2]),node([-2,3]),node([])]]]),(24,[[node([1,2,3,4,5])]]),(25,[[node([1,2,3,4,5]),3]])]:
 result=check(n,calls);assert result[0]['return_aliases'],n
for n,calls in [(15,[[[3,-1,-2,0]]]),(16,[[[4,1,2],8]]),(18,[[[3,2,1,0],6]]),(39,[[[3,2],6]]),(40,[[[2,1,2,1],4]])]:
 result=check(n,calls);assert all(r['args_before']==r['args_after'] for r in result),n
result=check(41,[[[3,4,-1,1]]],[2]);assert result[0]['args_before']!=result[0]['args_after']
# Exceptions retained by normalization; these are not accepted problem-domain inputs.
for n,calls in [(4,[[[],[]]]),(16,[[[1,2],0]]),(19,[[node([1]),2]]),(22,[[-1]]),(29,[[1,0]])]:
 result=check(n,calls);assert all(r.get('error')=='RangeError' for r in result)
# Independent finite floating oracle, unchanged judge tolerance; no nonfinite acceptance.
float_calls=[[2.,-10],[-2.,-3],[1.00001,100],[1.00001,-100],[2.,-2147483648],[0.5,10]]
check(50,float_calls)
for args in float_calls:
 test=judge.FunctionalTest(args=args,expected=math.pow(*args));calls=dict(method='myPow',params=rows[50]['params'],calls=[dict(args=args,capture_args=False)])
 raw=sandbox.run(['/usr/bin/node','--jitless','--max-old-space-size=64','harness.cjs'],files={'harness.cjs':(R/'findings/source-corpus-js-py-128-v3/return_harness.cjs').read_text(),'candidate.cjs':source(50),'calls.json':json.dumps(calls)},limits=sandbox.Limits(wall_seconds=8,cpu_seconds=3,memory_bytes=1024**3,max_output_bytes=65536));assert judge._score_functional(raw,[test]).passed
# Positive-candidate combination oracle via independent product enumeration.
for n,a,target in [(39,[2,3,5],8),(40,[1,1,2,2,3],4)]:
 if n==39:expected=sorted([sorted(sum(([v]*k for v,k in zip(a,ks)),[])) for ks in itertools.product(range(target//min(a)+1),repeat=len(a)) if sum(v*k for v,k in zip(a,ks))==target])
 else:expected=sorted({tuple(sorted(a[i] for i in range(len(a)) if mask>>i&1)) for mask in range(1<<len(a)) if sum(a[i] for i in range(len(a)) if mask>>i&1)==target});expected=[list(v) for v in expected]
 result=check(n,[[a,target]])[0]['result'];assert sorted(result)==expected and len(result)==len(expected)
# Board oracle independently enumerates permutations, testing diagonal uniqueness.
boards=check(51,[[4]])[0]['result'];expected=[]
for perm in itertools.permutations(range(4)):
 if len({i-v for i,v in enumerate(perm)})==4 and len({i+v for i,v in enumerate(perm)})==4:expected.append(['.'*v+'Q'+'.'*(3-v) for v in perm])
assert sorted(boards)==sorted(expected) and len(boards)==len(expected)
# Mutant duplicate/missing collections must fail unchanged exact scoring for39/40/51.
for expected in [[[2,2,2],[3,3]],[[1,1,2],[2,2]],boards]:
 for actual in [expected[:-1],expected+[expected[0]]]:
  raw=sandbox.SandboxResult(0,None,(json.dumps(dict(i=0,result=actual))+'\n'+json.dumps(dict(done=1))+'\n').encode(),b'',0);assert not judge._score_functional(raw,[judge.FunctionalTest(expected=expected)]).passed
# BigInt successor checked against an independent digit-reversal oracle.
values=[0,1,10,-121,121,1221,12321,2147483647,9007199254740991,9007199254740993,123456789987654321,10**40+1,10**40+2]
tests=[judge.FunctionalTest(args=[v],expected=v>=0 and str(v)==str(v)[::-1]) for v in values]
v,raw,payload=exact_integer.execute((OUT/'0009-exact-integer-successor.js').read_text(),'isPalindrome',[['x','int']],tests);assert v.passed;assert 'expected' not in json.loads(payload)
report=dict(runner_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),groups=len(records),original_normalized_runtime_calls=sum(len(r['calls']) for r in records),records=records,exact_integer_independent_controls=len(values),float_math_pow_controls=len(float_calls),collection_mutant_rejections=6,unicode_scope='3/6/10/14 use codepoints.28/30/44 UTF16 examples explicitly demonstrate outside-ASCII differences; do not claim universal Unicode parity.',termination_39='Strictly positive2..40 distinct inputs only; recursion strictly decreases remaining sum. Zero/negative values remain unsupported, never supplied to unsafe unbounded recursion.',limitations='Finite probes and source inspection, not proof, maximum-bound performance, or new autonomous solving.')
with (OUT/'semantic-probes.json').open('x') as f:json.dump(report,f,indent=2,allow_nan=False)
print(json.dumps({k:v for k,v in report.items() if k!='records'},indent=2))
