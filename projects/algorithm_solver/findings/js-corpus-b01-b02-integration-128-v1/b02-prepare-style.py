from pathlib import Path
import hashlib,json,subprocess
TASK=Path('/home/x/Documents/Codex/2026-10-19/task')
PACK=TASK/'js-corpus-wave-001'
OUT=Path('/home/x/deco/gamma/projects/algorithm_solver/runs/js-corpus-wave-001/W001-B02')
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write(p,v):
 with p.open('x') as f:json.dump(v,f,indent=2);f.write('\n')
contract=dict(schema='algsolve.role-style.v1',scope='B02 owner-source normalization only; no algorithm or oracle changes',entry='Public function name and parameter names/order unchanged',locals='Scope-aware role names with fresh two-phase renaming and reference-binding capture checks',format='Babel two-space formatting, semicolons and explicit ordinary loop/if blocks',preserve=['declaration kind','statement order','operators','literals','property names','regex','function calls','loop forms','input mutation','return aliasing'],numeric='Original Number behavior unchanged. Exact-integer successors are separate candidates.',normalizer_sha256=sha(TASK/'b02-normalize.cjs'),shared_qualifier_sha256=sha(PACK/'qualify.py'))
assert contract['shared_qualifier_sha256']=='d90952fec65c0c00ec999708d909cf29e8f887c9bc18eefc89f15379c37d8cd2'
write(OUT/'style-contract.json',contract)
rows=[]
for row in json.loads((PACK/'W001-B02/assignment.json').read_text())['rows']:
 n=row['id'];original=OUT/f'{n:04d}-owner-original.js'
 receipt=json.loads((OUT/f'{n:04d}/attempt-001/receipt.json').read_text());assert sha(original)==receipt['source_sha256']
 data=dict(id=n,method=row['entry']['method'],params=[p[0] for p in row['params']],source=original.read_text())
 out=subprocess.run(['/usr/bin/node',str(TASK/'b02-normalize.cjs')],input=json.dumps(data),text=True,capture_output=True,check=True)
 normalized=json.loads(out.stdout);source=OUT/f'{n:04d}-role-style.js'
 with source.open('x') as f:f.write(normalized.pop('source'))
 subprocess.run(['/usr/bin/node','--check',str(source)],check=True,capture_output=True)
 semantics=json.loads((OUT/f'{n:04d}-owner-original-semantics.json').read_text())
 semantics['normalization']='Role-based bound-local names and explicit blocks only, preserving the public signature, algorithm, numeric behavior, side effects and return aliases; see style-contract.json and per-source normalization record.'
 write(OUT/f'{n:04d}-role-style-semantics.json',semantics)
 normalized.update(id=n,original_sha256=sha(original),normalized_sha256=sha(source),semantics_sha256=sha(OUT/f'{n:04d}-role-style-semantics.json'))
 write(OUT/f'{n:04d}-normalization.json',normalized);rows.append(normalized)
write(OUT/'normalized-source-seal.json',dict(contract_sha256=sha(OUT/'style-contract.json'),rows=rows))
print('Prepared and syntax checked',len(rows),'sources')
