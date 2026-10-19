from pathlib import Path
import hashlib,json,sys
ROOT=Path('/home/x/deco/gamma/projects/algorithm_solver');sys.path.insert(0,str(ROOT))
from algsolve.judge import sandbox
PACK=Path('/home/x/Documents/Codex/2026-10-19/task/js-corpus-wave-001')
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
base=ROOT/'findings/source-corpus-js-py-128-v3/return_harness.cjs'
instrument='''const argsBefore = args.map(value => output(value));
      const inputIds = new Map();
      function indexObjects(value) {
        if (!value || typeof value !== 'object' || inputIds.has(value)) return;
        inputIds.set(value, inputIds.size);
        for (const child of Object.values(value)) indexObjects(child);
      }
      args.forEach(indexObjects);
      const result = fn(...args);
      const returnAliases = [];
      function captureAliases(value, path, seen = new Set()) {
        if (!value || typeof value !== 'object') return;
        if (inputIds.has(value)) returnAliases.push([path, inputIds.get(value)]);
        if (seen.has(value)) return;
        seen.add(value);
        for (const [key, child] of Object.entries(value)) captureAliases(child, path.concat(key), seen);
      }
      captureAliases(result, []);'''
harness=base.read_text().replace('const result = fn(...args);',instrument).replace('emit({ i, result:', 'emit({ i, args_before: argsBefore, return_aliases: returnAliases, result:')
def run(source,method,params,calls):
 r=sandbox.run(['/usr/bin/node','--jitless','--max-old-space-size=64','harness.cjs'],files={'harness.cjs':harness,'candidate.cjs':source,'calls.json':json.dumps(dict(method=method,params=params,calls=[dict(args=c,capture_args=True) for c in calls]))},limits=sandbox.Limits(wall_seconds=8,cpu_seconds=3,memory_bytes=1024**3,max_output_bytes=65536))
 records=[json.loads(l) for l in r.stdout.decode().splitlines()]
 assert r.ok and records[-1:]==[{'done':len(calls)}],r
 assert all('error' not in v for v in records[:-1]),records
 return records[:-1]
def write(p,v):
 with p.open('x') as f:json.dump(v,f,indent=2);f.write('\n')
control_args=[[[1,2]]]
controls={k:run(s,'f',[['x','List[int]']],control_args) for k,s in {'same_array':'function f(x){return x;}','copy':'function f(x){return x.slice();}','mutate':'function f(x){x.push(3);return x;}'}.items()}
assert controls['same_array'][0]['return_aliases'] and not controls['copy'][0]['return_aliases']
assert controls['same_array'][0]['args_before']==controls['same_array'][0]['args_after']
assert controls['mutate'][0]['args_before']!=controls['mutate'][0]['args_after']
for batch in ['W001-B01','W001-B02']:
 out=ROOT/'runs/js-corpus-wave-001'/batch;rows=[]
 for row in json.loads((PACK/batch/'assignment.json').read_text())['rows']:
  n=row['id'];old=json.loads((out/f'{n:04d}/attempt-001/receipt.json').read_text());new=json.loads((out/f'{n:04d}/attempt-002/receipt.json').read_text())
  def outcome(r):
   return [(v['group'],v.get('offset'),v['status'],[(v.get(lang,{}).get('passed'),v.get(lang,{}).get('reason'),v.get(lang,{}).get('tests_passed'),v.get(lang,{}).get('tests_total'),v.get(lang,{}).get('first_failure')) for lang in ['python','javascript']]) for v in r['results']]
  assert outcome(old)==outcome(new),(batch,n,'Qualification changed')
  packet=json.loads(Path(row['problem_packet']).read_text());calls=[t['args'] for t in packet['public_tests']]
  a=run((out/f'{n:04d}-owner-original.js').read_text(),row['entry']['method'],row['params'],calls)
  b=run((out/f'{n:04d}-role-style.js').read_text(),row['entry']['method'],row['params'],calls)
  assert a==b,(batch,n,'Differential behavior changed')
  rec=dict(id=n,qualified=new['qualified'],original_receipt_sha256=sha(out/f'{n:04d}/attempt-001/receipt.json'),normalized_receipt_sha256=sha(out/f'{n:04d}/attempt-002/receipt.json'),all_original_outcomes_preserved=True,public_differential_calls=len(calls),runtime_results_mutation_and_aliasing_match=True,observations=a)
  write(out/f'{n:04d}-style-differential.json',rec);rows.append(rec)
 write(out/'style-verification.json',dict(normalizer_contract_sha256=sha(out/'style-contract.json'),runner_sha256=sha(__file__),instrumented_harness_sha256=hashlib.sha256(harness.encode()).hexdigest(),base_harness_sha256=sha(base),controls=controls,rows=rows,qualified=sum(r['qualified'] for r in rows),differential_calls=sum(r['public_differential_calls'] for r in rows),scope='Finite development qualification plus public-input result, mutation and reference-alias equivalence; not a formal proof or autonomous solving result.'))
 print(batch,'style outcomes and runtime mutation/aliasing preserved',len(rows),sum(r['public_differential_calls'] for r in rows),flush=True)
