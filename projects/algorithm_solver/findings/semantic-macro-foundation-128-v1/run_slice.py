"""Freeze the first dual-language macro slice, then score existing development tests."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time
from algsolve import semantic_macros as macros, validate
from algsolve.records import LANE_ROOT as ROOT, Problem, load_hidden_tests
from algsolve.synth import typed_codec, development_tests, mine
from algsolve.judge import sandbox, judge

OUT=ROOT/'runs/semantic-macro-foundation-128-v1'
FIND=ROOT/'findings/semantic-macro-foundation-128-v1'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write(path,value):
    with path.open('x') as f:json.dump(value,f,indent=2);f.write('\n')

def run_js(source,tests):
    ts=validate.functional_tests(tests)
    calls={'method':'numIdenticalPairs','params':[['p0','List[int]']],'calls':[{'args':t.args} for t in ts]}
    result=sandbox.run(['/usr/bin/node','--jitless','--max-old-space-size=64','harness.cjs'],files={
        'harness.cjs':(ROOT/'algsolve/editor_harness.cjs').read_text(),'candidate.cjs':source,'calls.json':json.dumps(calls)},
        limits=sandbox.Limits(wall_seconds=8,cpu_seconds=3,memory_bytes=1024**3,max_output_bytes=65536))
    return judge._score_functional(result,ts).to_dict()


def main():
    OUT.mkdir()
    corpus=ROOT/'runs/typed-real-dev-v5/pairs.jsonl'
    assert sha(corpus)=='566d6b440d7fdd16bac0b86114b5e8dd35ba8bd646b6bd304f8cfbc5e201330e'
    pair=next(json.loads(line) for line in corpus.read_text().splitlines() if json.loads(line)['uid']=='lcd:1512' and json.loads(line)['variant']=='frequency_map')
    retained=ROOT/'runs/typed-gpu-reuse-fit-128-v2/score-cuda-lcd_1512.json'
    prior=json.loads(retained.read_text());assert prior['routes']['raw']['accepted_correct'] and prior['routes']['raw']['final_graph']==prior['routes']['guard_candidate']['final_graph']
    contract=dict(run=OUT.name,goals_sha256=sha(ROOT/'contracts/semantic_macro_goals_v1.json'),
        sources_sha256={str(p.relative_to(ROOT)):sha(p) for p in [ROOT/'algsolve/semantic_macros.py',Path(__file__),ROOT/'algsolve/editor_harness.cjs',ROOT/'algsolve/judge/sandbox.py',ROOT/'algsolve/judge/judge.py']},
        original_corpus_sha256=sha(corpus),retained_predictor_receipt_sha256=sha(retained),
        independent_tests_sha256=pair['provenance']['independent_tests_sha256'],
        scope='One already-consumed fit problem, two known algorithms, two languages. Manual deterministic macro transcription; no new autonomous prediction, mining campaign or generalization.',
        implementations=['python-map','python-pair_scan','javascript-map','javascript-pair_scan'],
        language_qualification='Separate per implementation; failures retained. No JavaScript production catalog or recognizer promotion.',
        codebook='12 active entries including explicit block close, 244 reserved in each separately versioned language profile. Demonstration vocabulary, not selected/optimal256.',
        limits=dict(cpu_threads=4,memory_bytes=8*1024**3,wall_seconds=180,artifact_disk_bytes=5*1024**3),
        training=False,downloads=False,protected_scoring=False,deployment=False)
    write(OUT/'contract.json',contract)
    rows=[]
    for language in macros.LANGUAGES:
        profile={'id':f'{language}-semantic-macros-v1','version':macros.VERSION,'language':language,
                 'implementation_sha256':sha(ROOT/'algsolve/semantic_macros.py'),
                 'entries':[{'id':i,'bits':format(i,'08b'),'name':macros.ENTRIES[i][0],'operands':macros.ENTRIES[i][1]} if i<len(macros.ENTRIES) else {'id':i,'bits':format(i,'08b'),'reserved':True} for i in range(256)],
                 'operand_grammar':{'o':'one-byte fresh binding','b':'one-byte existing binding','e':'tag0 + one-byte binding, or tag1 + canonical zigzag unsigned varint'},
                 'signature':'one list[int] p0 -> int; exact Number-safe integer semantics with runtime input/overflow checks'}
        write(OUT/f'{language}-codebook.json',profile)
        for kind in ('map','pair_scan'):
            record=macros.good_pairs(language,kind);stream=macros.encode(record);decoded=macros.decode(stream)
            assert record==decoded and macros.encode(decoded)==stream
            source=macros.expand(decoded);stem=f'{language}-{kind}';suffix='py' if language=='python' else 'js'
            (OUT/f'{stem}.{suffix}').write_text(source)
            (OUT/f'{stem}.bin').write_bytes(stream);write(OUT/f'{stem}.json',record)
            graph=pair['target']['program'] if kind=='map' else prior['routes']['raw']['final_graph']
            write(OUT/f'{stem}-origin-graph.json',graph)
            rows.append(dict(id=stem,language=language,algorithm=kind,source_file=f'{stem}.{suffix}',source_sha256=sha(OUT/f'{stem}.{suffix}'),stream_sha256=sha(OUT/f'{stem}.bin'),
                origin='authored map reference' if kind=='map' else 'retained correct raw predictor pair scan; guarded graph identical',
                original_graph_sha256=typed_codec.digest(graph),cost=macros.costs(record),roundtrip=True))
    write(OUT/'source-seal.json',rows)
    print('[run-contract] run_name='+OUT.name+' pairs_input_spec=one-consumed-fit-problem-two-algorithms-two-languages resume_from=none resume_stage=none decode=deterministic-macro-expansion eval_dataset_paths=hash-bound-lcd1512-independent device=cpu schedule=no-training runtime_mode=cpu sweep_mode=none',flush=True)
    problem=Problem(uid='lcd:1512',source='lcd',source_id='1512',title='Number of Good Pairs',slug='number-of-good-pairs',statement=pair['input']['statement'],io_mode='functional',entry={'class':'Solution','method':'numIdenticalPairs'},params=[['p0','List[int]']],hidden_tests_path='tests/lcd__1512.json')
    tests,_=development_tests.select('lcd:1512',load_hidden_tests(problem));assert mine.digest(tests)==contract['independent_tests_sha256']
    public=pair['input']['public_examples']
    preservation=[{'args':[a],'expected':a,'compare':'arg:0'} for a in ([1,2,3,1,1,3],[1],[1,1,1,1],[2,1,2])]
    for row in rows:
        source=(OUT/row['source_file']).read_text();assert sha(OUT/row['source_file'])==row['source_sha256']
        run=(lambda tests:validate.judge_problem(problem,source,tests,wall_seconds=8).to_dict()) if row['language']=='python' else lambda tests:run_js(source,tests)
        row['public']=run(public);row['independent']=run(tests);row['input_preservation']=run(preservation)
        write(OUT/f"{row['id']}-verdict.json",row)
        print(json.dumps({k:row[k] for k in ['id','cost','public','independent','input_preservation']}),flush=True)
    # Explicit numeric/type guards are software checks, not extra independent LC cases.
    checks=[]
    for language in macros.LANGUAGES:
        record=macros.good_pairs(language,'map')
        record['instructions']=[{'op':'var_int','args':[1,{'int':macros.MAX_INTEGER}]},{'op':'add','args':[2,{'ref':1},{'int':1}]},{'op':'return','args':[{'ref':2}]}]
        source=macros.expand(record)
        tail="\nlet rejected = 0; for (const values of [[], [true], [1.5], [9007199254740992]]) { try { numIdenticalPairs(values); } catch (e) { rejected++; } } if (rejected !== 4) throw new Error('guard failure'); console.log('4 guards passed');\n" if language=='javascript' else "\nrejected = 0\nfor values in ([], [True], [1.5], [9007199254740992]):\n    try:\n        Solution().numIdenticalPairs(values)\n    except (ValueError, TypeError):\n        rejected += 1\nassert rejected == 4\nprint('4 guards passed')\n"
        filename='candidate.cjs' if language=='javascript' else 'candidate.py';argv=['/usr/bin/node','--jitless','--max-old-space-size=64',filename] if language=='javascript' else [sandbox.PYTHON,'-I','-S',filename]
        result=sandbox.run(argv,files={filename:source+tail},limits=sandbox.Limits(wall_seconds=5,memory_bytes=1024**3))
        checks.append(dict(language=language,passed=result.ok,stdout=result.stdout.decode(),stderr=result.stderr.decode(),exit_code=result.exit_code))
    write(OUT/'numeric-guards.json',checks)
    summary=dict(contract_sha256=sha(OUT/'contract.json'),source_seal_sha256=sha(OUT/'source-seal.json'),rows=rows,numeric_guards=checks,
        qualified_implementations=sum(all(r[k]['passed'] for k in ('public','independent','input_preservation')) for r in rows),
        distinct_problems=1,algorithms=2,languages=2,autonomous_new_solves=0,
        limits=['Development regression only; existing102 cases already consumed.','Two manual macro sequences; no newly learned macro selection.','Codebook has12 active entries, not256 completed/optimal entries.','No protected/family generalization or human effort result.'])
    write(OUT/'summary.json',summary);write(FIND/'summary.json',summary);write(FIND/'contract.json',contract)
    assert summary['qualified_implementations']==4 and all(r['passed'] for r in checks)

if __name__=='__main__':main()
