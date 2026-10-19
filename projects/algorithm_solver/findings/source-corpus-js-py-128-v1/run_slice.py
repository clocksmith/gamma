"""Five permitted fit families, existing source, frozen before independent scoring."""
import ast
import hashlib
import json
from pathlib import Path
import subprocess
from algsolve import validate
from algsolve.records import LANE_ROOT as ROOT,Problem,load_hidden_tests
from algsolve.synth import development_tests,mine
from algsolve.judge import sandbox,judge

FIND=ROOT/'findings/source-corpus-js-py-128-v1';OUT=ROOT/'runs/source-corpus-js-py-128-v1'
PIN=ROOT/'data/raw/doocs__leetcode_input/88c8c2c29f19c186d7cc05c9db17245d9ae3df43'
PYROOT=ROOT/'data/raw/doocs__leetcode/solution'
# Explicitly permitted consumed fit cases. Do not inspect audit or protected sources.
CASES=[(1512,'numIdenticalPairs','Solution.js',1,100,0,100,False),
       (1748,'sumOfUnique','Solution.ts',1,100,0,100,False),
       (252,'canAttendMeetings','Solution.ts',0,1000000,0,10000,True),
       (1464,'maxProduct','Solution.ts',1,1000,2,500,False),
       (1046,'lastStoneWeight','Solution.js',1,1000,1,30,False)]
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write(p,value):
    with p.open('x') as f:json.dump(value,f,indent=2);f.write('\n')

def normalize_py(source,method):
    tree=ast.parse(source);cls=next(n for n in tree.body if isinstance(n,ast.ClassDef));fn=next(n for n in cls.body if isinstance(n,ast.FunctionDef) and n.name==method)
    assert len(fn.args.args)==2
    names={fn.args.args[1].arg:'p0'}
    for n in ast.walk(fn):
        if isinstance(n,ast.Name) and isinstance(n.ctx,ast.Store) and n.id not in names:names[n.id]=f'local{len(names)-1}'
    class Rename(ast.NodeTransformer):
        def visit_Name(self,n):
            if n.id in names:n.id=names[n.id]
            return n
        def visit_arg(self,n):
            if n.arg in names:n.arg=names[n.arg]
            return n
    fn=Rename().visit(fn);fn.name='implementation';cls.name='Implementation'
    ast.fix_missing_locations(tree)
    return ast.unparse(tree)+'\n'

def js_wrapper(method,domain):
    lo,hi,minn,maxn,nested=domain
    condition=f'Number.isSafeInteger(x) && x >= {lo} && x <= {hi}'
    element=f'Array.isArray(row) && row.length === 2 && row.every(x => {condition}) && row[0] < row[1]' if nested else condition
    valid=f'p0.every({"row" if nested else "x"} => {element})'
    return f"function {method}(p0) {{\n  if (!Array.isArray(p0) || p0.length < {minn} || p0.length > {maxn} || !({valid})) throw new TypeError('declared input domain');\n  return implementation(JSON.parse(JSON.stringify(p0)));\n}}\n"

def py_wrapper(method,domain):
    lo,hi,minn,maxn,nested=domain
    atom=f'type(x) is int and {lo} <= x <= {hi}'
    element=f'type(row) is list and len(row) == 2 and all({atom} for x in row) and row[0] < row[1]' if nested else atom
    valid=f'all({element} for {"row" if nested else "x"} in p0)'
    return f"class Solution:\n    def {method}(self, p0):\n        if type(p0) is not list or not {minn} <= len(p0) <= {maxn} or not ({valid}):\n            raise ValueError('declared input domain')\n        return Implementation().implementation({('[row[:] for row in p0]' if nested else 'p0[:]')})\n"

PRELUDE='from typing import List\nfrom collections import Counter\nfrom heapq import heapify, heappop, heappush\nfrom itertools import pairwise\n'

def js_judge(source,method,tests):
    ts=validate.functional_tests(tests)
    calls={'method':method,'params':[['p0','List[int]']],'calls':[{'args':t.args} for t in ts]}
    result=sandbox.run(['/usr/bin/node','--jitless','--max-old-space-size=64','harness.cjs'],files={'harness.cjs':(ROOT/'algsolve/editor_harness.cjs').read_text(),'candidate.cjs':source,'calls.json':json.dumps(calls)},limits=sandbox.Limits(wall_seconds=8,cpu_seconds=3,memory_bytes=1024**3,max_output_bytes=65536))
    return judge._score_functional(result,ts).to_dict()


def main():
    OUT.mkdir()
    corpus=ROOT/'runs/typed-real-dev-v5/pairs.jsonl';assert sha(corpus)=='566d6b440d7fdd16bac0b86114b5e8dd35ba8bd646b6bd304f8cfbc5e201330e'
    pairs={}
    for line in corpus.read_text().splitlines():
        p=json.loads(line)
        if p['learning_split']=='development_fit':pairs.setdefault(p['uid'],p)
    pinned={r['path']:r for r in json.loads((PIN/'manifest.json').read_text())['files']}
    contract=dict(name=OUT.name,cases=[c[0] for c in CASES],corpus_sha256=sha(corpus),pinned_revision=PIN.name,
        pinned_manifest_sha256=sha(PIN/'manifest.json'),goals_commit='a373bcb91bfaa41d0ba1c0c8d6143f54464a8826',
        sources_sha256={str(p.relative_to(ROOT)):sha(p) for p in [Path(__file__),FIND/'normalize_js.cjs',ROOT/'algsolve/editor_harness.cjs',ROOT/'algsolve/judge/sandbox.py',ROOT/'algsolve/judge/judge.py']},
        normalization='Existing source -> deterministic AST formatting/identifier normalization; TypeScript type erasure where declared. Separate wrapper checks declared integer domain and copies inputs. No algorithm substitution or new dependency.',
        dependencies='Python explicitly imports existing standard-library typing, collections, heapq and itertools. JavaScript receives no invented priority queue; missing external dependencies remain failures.',
        language_agnostic_identity=True,each_implementation_scored_separately=True,
        selection='Five named consumed fit families only, chosen before scoring; no target replacement or missing-test fallback.',
        expected_output_boundary='Host-side only; never passed to isolated candidate.',
        limits={'cpu_threads':4,'memory_bytes':8*1024**3,'wall_seconds':180,'disk_bytes':5*1024**3},
        training=False,downloads=False,protected_scoring=False,production_catalog_changed=False,public_push=False,deployment=False)
    write(OUT/'contract.json',contract)
    rows=[]
    for num,method,jsname,*domain in CASES:
        pair=pairs[f'lcd:{num}'];assert pair['learning_split']=='development_fit'
        pypath=next(PYROOT.glob(f'*/{num:04d}.*/Solution.py'));jspath=next((PIN/'solution').glob(f'*/{num:04d}.*/{jsname}'))
        rel=str(jspath.relative_to(PIN));assert sha(jspath)==pinned[rel]['sha256']
        original_py=pypath.read_text();original_js=jspath.read_text()
        result=json.loads(subprocess.check_output(['/usr/bin/node',str(FIND/'normalize_js.cjs')],input=json.dumps(dict(source=original_js,method=method,typescript=jspath.suffix=='.ts')),text=True))
        sources={'python-original':PRELUDE+original_py,'python-normalized':PRELUDE+normalize_py(original_py,method)+py_wrapper(method,domain),
                 'javascript-original':result['original'],'javascript-normalized':result['normalized']+js_wrapper(method,domain)}
        for kind,source in sources.items():(OUT/f'{num}-{kind}.{ "py" if kind.startswith("python") else "js"}').write_text(source)
        (OUT/f'{num}-upstream{jspath.suffix}').write_text(original_js);(OUT/f'{num}-upstream.py').write_text(original_py)
        row=dict(uid=pair['uid'],key=pair['key'],method=method,domain=dict(zip(['minimum_integer','maximum_integer','minimum_length','maximum_length','intervals'],domain)),
            source_provenance={'python_path':str(pypath.relative_to(ROOT)),'python_sha256':sha(pypath),'javascript_path':str(jspath.relative_to(ROOT)),'javascript_sha256':sha(jspath),'javascript_upstream_revision':PIN.name,'javascript_license':'doocs/leetcode CC-BY-SA-4.0; commercial reprints require author authorization; research use only','python_license':pair['provenance']['license'],'type_erasure':result['type_erasure']},
            tools=result['tools'],core_ast={'javascript_original':result['original_ast'],'javascript_normalized':result['normalized_core_ast']},
            independent_tests_sha256=pair['provenance']['independent_tests_sha256'],sources={k:{'file':f'{num}-{k}.{ "py" if k.startswith("python") else "js"}','sha256':hashlib.sha256(v.encode()).hexdigest()} for k,v in sources.items()})
        rows.append(row)
    write(OUT/'source-seal.json',rows)
    print('[run-contract] run_name='+OUT.name+' pairs_input_spec=five-consumed-fit-families-existing-js-ts-and-python resume_from=none resume_stage=none decode=deterministic-source-normalization eval_dataset_paths=hash-bound-development-tests device=cpu schedule=no-training runtime_mode=cpu sweep_mode=none',flush=True)
    catalog=[]
    for row in rows:
        pair=pairs[row['uid']];problem=Problem(uid=pair['uid'],source='lcd',source_id=pair['uid'].split(':')[1],title='',slug=pair['problem_family'],statement=pair['input']['statement'],io_mode='functional',entry={'class':'Solution','method':row['method']},params=pair['input']['params'],hidden_tests_path='tests/'+pair['uid'].replace(':','__')+'.json')
        tests,_=development_tests.select(row['uid'],load_hidden_tests(problem));assert mine.digest(tests)==row['independent_tests_sha256']
        verdicts={};implementations=[]
        for label,meta in row['sources'].items():
            source=(OUT/meta['file']).read_text();assert sha(OUT/meta['file'])==meta['sha256']
            run=(lambda ts:validate.judge_problem(problem,source,ts,wall_seconds=8).to_dict()) if label.startswith('python') else lambda ts:js_judge(source,row['method'],ts)
            outcome={'public':run(pair['input']['public_examples']),'independent':run(tests)}
            if label.endswith('normalized'):
                preserved=[{'args':t['args'],'expected':t['args'][0],'compare':'arg:0'} for t in pair['input']['public_examples']]
                outcome['input_preservation']=run(preserved)
                implementations.append(dict(language=label.split('-')[0],source=meta,qualified=all(v['passed'] for v in outcome.values()),tests=outcome))
            verdicts[label]=outcome
        row['verdicts']=verdicts;write(OUT/(row['uid'].replace(':','-')+'-verdict.json'),row)
        catalog.append(dict(key=row['key'],implementations=implementations,scope='consumed development regression; not production approval'))
        print(json.dumps({'uid':row['uid'],'results':{k:{stage:(v['passed'],v['tests_passed'],v['tests_total'],v['reason']) for stage,v in value.items()} for k,value in verdicts.items()}}),flush=True)
    summary=dict(contract_sha256=sha(OUT/'contract.json'),source_seal_sha256=sha(OUT/'source-seal.json'),distinct_problems=len(rows),rows=rows,
                 qualified_by_language={language:sum(i['qualified'] for c in catalog for i in c['implementations'] if i['language']==language) for language in ('python','javascript')},
                 limits=['Five chosen consumed fit families; no broad/random coverage or new autonomous success.','No failed implementation replaced or dependency silently supplied.','Qualification is finite independent-test agreement in declared domains, not formal proof.','Original Python1a catalog and protected reservation unchanged.'])
    write(OUT/'catalog.json',catalog);write(OUT/'summary.json',summary);write(FIND/'summary.json',summary);write(FIND/'contract.json',contract)

if __name__=='__main__':main()
