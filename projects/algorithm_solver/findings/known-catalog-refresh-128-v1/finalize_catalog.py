"""One-time documented loader-only rebind of fresh v2 qualification evidence."""
import ast
import copy
import json
from pathlib import Path
from datetime import datetime,timezone
from algsolve import library_audit as audit
from algsolve.approved_library import build
from algsolve.catalog_refresh import check
from algsolve.qualification_environment import capture,verify
from algsolve.records import LANE_ROOT

source=LANE_ROOT/'runs/catalog-refresh-128-v2'
target=LANE_ROOT/'runs/catalog-refresh-128-v4'
old_contract=json.loads((source/'contract.json').read_text())
summary=json.loads((source/'summary.json').read_text())
assert summary['complete'] and summary['independent_classified']==3288
assert not target.exists()
# Only the optional loader verification policy changes existing runtime source.
changed=[]
for name,sha in old_contract['files_sha256'].items():
    if audit.sha(LANE_ROOT/name)!=sha:changed.append(name)
assert changed==['algsolve/approved_library.py'],changed
old_source=(source/'approved_library-frozen-v2.py').read_text()
assert audit.sha(source/'approved_library-frozen-v2.py')==old_contract['files_sha256']['algsolve/approved_library.py']
old_tree=ast.parse(old_source);new_tree=ast.parse((LANE_ROOT/'algsolve/approved_library.py').read_text())
def functions(tree):
    return {n.name:ast.dump(n,include_attributes=False) for n in tree.body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef))}
def methods(tree):
    cls=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='ApprovedLibrary')
    return functions(cls)
old_funcs,new_funcs=functions(old_tree),functions(new_tree)
assert {k for k in old_funcs if old_funcs[k]!=new_funcs[k]}=={'build'}
old_methods,new_methods=methods(old_tree),methods(new_tree)
assert {k for k in old_methods if old_methods[k]!=new_methods[k]}=={'verify_runtime'}
environment=capture();during=json.loads((source/'environment-during.json').read_text())
for field in ['interpreter','executables','stdlib_root','stdlib_files_sha256','stdlib_tree_sha256']:
    assert during[field]==environment[field],field
supplemental=json.loads((source/'supplemental-runtime.json').read_text())
assert audit.sha(LANE_ROOT/'algsolve/test_corrections.py')==supplemental['test_corrections_sha256']
for path,sha in supplemental['sandbox_executables'].items():assert audit.sha(Path(path))==sha
verify(environment)
# Original scoring evidence remains untouched. Copies are explicitly chained,
# not represented as another independent run.
target.mkdir()
for name in ['inventory.jsonl','public.jsonl','public-seal.json','answers.jsonl','summary.json']:
    (target/name).write_bytes((source/name).read_bytes())
contract=copy.deepcopy(old_contract)
contract['schema']='algsolve.catalog-refresh.runtime-gated-v4'
for section in ['files_sha256','runtime_files_sha256']:
    for name in ['algsolve/approved_library.py','algsolve/qualification_environment.py','algsolve/test_corrections.py']:
        contract[section][name]=audit.sha(LANE_ROOT/name)
contract['execution_evidence']='fresh v2; unchanged stored source/tests/judge/public decisions; no additional independent run'
contract['runtime_environment']=environment
contract['rebound_utc']=datetime.now(timezone.utc).isoformat()
audit.write(target/'contract.json',contract)
receipt={'schema':'algsolve.catalog-rebind.v1','recorded_utc':contract['rebound_utc'],
    'original_contract_sha256':audit.sha(source/'contract.json'),'rebound_contract_sha256':audit.sha(target/'contract.json'),
    'independent_answers_sha256':audit.sha(source/'answers.jsonl'),'independent_verdicts_rerun':False,
    'changed_existing_source':changed,'changed_top_level_functions':['approved_library.build: optional receipt field only'],
    'changed_methods':['ApprovedLibrary.verify_runtime: additional fail-closed gate only'],
    'unchanged_execution':'answer, query parser, selected stored source, tests, corrections, judge, harness, sandbox, limits',
    'environment_capture':'first captured during v2, rechecked before final serving verification; not pre-v2 frozen',
    'during_environment_sha256':audit.sha(source/'environment-during.json'),
    'environment':environment}
audit.write(target/'rebind-receipt.json',receipt)
_,entries,_=check(target)
manifest=build(entries,audit.rows(target/'inventory.jsonl'),audit.rows(target/'answers.jsonl'),
    evidence={name:audit.sha(target/name) for name in ['contract.json','inventory.jsonl','public-seal.json','answers.jsonl','rebind-receipt.json']},
    runtime_files=contract['runtime_files_sha256'],answer_policy=contract['answer_policy'],runtime_environment=environment)
old=json.loads((source/'approved-library.json').read_text())
assert all(manifest[k]==old[k] for k in ['approved','excluded','counts','answer_policy','identity_policy'])
audit.write(target/'approved-library.json',manifest)
print(json.dumps({'counts':manifest['counts'],'rebind':receipt['changed_existing_source'],'independent_verdicts_rerun':False},indent=2))
