"""Prospective adoption of reviewed official-domain source qualification.

Separate from historical admitted/probe receipts. The frozen public-domain host
verifier is actually replayed before adoption; no candidate executes. Inputs are
validated against the exact frozen official-domain predicate before any future
public-query execution. Metadata retrieval alone is not candidate execution.
"""
import argparse,copy,hashlib,importlib.util,json,sys
from pathlib import Path
from .catalogue import BINDINGS,digest,validate,hash_value
HERE=Path(__file__).resolve().parent
FOUNDATION=HERE/'public-domain-qualification-v2'
IDS=(120,931,955,988,1005,1007,1071,1106,1122,1160,1170,1514,1942,2192)
sha=lambda raw:hashlib.sha256(raw).hexdigest()
def load_module(name,path):
 spec=importlib.util.spec_from_file_location(name,path);result=importlib.util.module_from_spec(spec);spec.loader.exec_module(result);return result

def frozen_verifier():
 """Resolve only reviewed sibling modules; never a caller-supplied import path."""
 saved={name:sys.modules.get(name)for name in ('oracle','cases','qualify')}
 try:
  for name in saved:sys.modules[name]=load_module('foundation_bridge_'+name,FOUNDATION/(name+'.py'))
  result=load_module('foundation_bridge_verify',FOUNDATION/'verify.py')
 finally:
  for name,old in saved.items():
   if old is None:sys.modules.pop(name,None)
   else:sys.modules[name]=old
 return result

def validate_foundation_inputs(implementation,args):
 """Required fail-closed gate before executing a prospective foundation answer."""
 if implementation.get('status')!='qualified'or implementation.get('evidence_class')!='normative-typed-effects':raise ValueError('not a normative foundation artifact')
 foundation=implementation.get('provenance',{}).get('public_foundation',{})
 contract=foundation.get('problem_contract')
 if not isinstance(contract,dict)or digest(contract)!=implementation.get('problem_contract_sha256'):raise ValueError('official-domain contract binding changed')
 predicate=contract.get('input_validator',{})
 if predicate.get('entrypoint')!='validate'or predicate.get('numeric_problem_id')not in IDS or contract.get('official_problem_id')!=predicate.get('numeric_problem_id'):raise ValueError('unsupported frozen input predicate')
 path=FOUNDATION/'oracle.py'
 if sha(path.read_bytes())!=predicate.get('module_sha256'):raise ValueError('frozen input validator code changed')
 module=load_module('foundation_bound_input_validator',path)
 module.validate(predicate['numeric_problem_id'],args)
 return {'accepted':True,'problem_contract_sha256':implementation['problem_contract_sha256'],'validator_sha256':predicate['module_sha256'],'candidate_executed':False}

def replace_canonicals(universe,catalogue,receipts,new_implementations,new_receipts):
 """Copy-only deliberate policy successor; preserve every old receipt/slot."""
 before=validate(universe,catalogue,receipts)
 result=copy.deepcopy(catalogue);retained=copy.deepcopy(receipts);rows={r['problem_id']:r for r in result['problems']}
 protected=set(universe['protected_problem_ids'])
 result['schema']='gamma.dual-language-catalogue.v2'
 result['evidence_policy']={'schema':'gamma.catalogue-evidence-policy.v1','allowed_classes':['frozen-admitted-typed-effects','normative-typed-effects'],'scope_rule':'exact-bound-contract-only'}
 for (pid,language),impl in new_implementations.items():
  if pid in protected or pid not in rows:raise ValueError('protected or unknown identity cannot be adopted')
  if language not in ('javascript','python'):raise ValueError('unsupported language')
  old=rows[pid]['implementations'][language]
  if language=='javascript'and old.get('source_sha256')!=impl['source_sha256']:raise ValueError('JS canonical bytes must remain identical')
  prior=impl['provenance']['previous_canonical']
  if prior.get('implementation_sha256')!=digest(old)or prior.get('receipt_sha256')!=old.get('receipt_sha256'):raise ValueError('previous canonical archival binding mismatch')
  rows[pid]['implementations'][language]=copy.deepcopy(impl)
 for rid,receipt in new_receipts.items():
  if rid in retained and retained[rid]!=receipt:raise ValueError('immutable prior receipt collision')
  retained[rid]=copy.deepcopy(receipt)
 after=validate(universe,result,retained)
 if before['eligible_problems']!=after['eligible_problems']:raise ValueError('universe denominator changed')
 return result,retained,after

def adopt(a):
 base=a.base;universe_raw=(base/'universe.json').read_bytes();catalogue_raw=(base/'catalogue.json').read_bytes();receipts_raw=(base/'verified-receipts.json').read_bytes();anchors_raw=(base/'anchors.json').read_bytes()
 if sha(catalogue_raw)!=a.trusted_base_catalogue_sha256:raise ValueError('base catalogue anchor mismatch')
 universe=json.loads(universe_raw);catalogue=json.loads(catalogue_raw);receipts=json.loads(receipts_raw);anchors=json.loads(anchors_raw)
 baseline_summary=validate(universe,catalogue,receipts)
 if len(universe['eligible_problem_ids'])!=4081 or len(universe['protected_problem_ids'])!=166:raise ValueError('full owner population/protection scope changed')
 if baseline_summary['language_counts']['javascript']['qualified']!=400 or baseline_summary['language_counts']['python']['qualified']!=378:raise ValueError('expected predecessor source coverage changed')
 verifier_raw=a.verified.read_bytes()
 if sha(verifier_raw)!=a.trusted_verifier_sha256:raise ValueError('independent foundation verifier anchor mismatch')
 recorded=json.loads(verifier_raw);verifier=frozen_verifier();replayed=verifier.verify(a.report)
 if replayed!=recorded or replayed['passed_source_language_pairs']!=28:raise ValueError('full independent public observation replay differs')
 run_raw=(a.report.parent/'contract.json').read_bytes();run=json.loads(run_raw);freeze_path=Path(run['freeze']);freeze_raw=(freeze_path/'contract.json').read_bytes();freeze=json.loads(freeze_raw)
 review_raw=(a.report.parent/'review.json').read_bytes();review=json.loads(review_raw)
 if replayed['freeze_sha256']!=sha(freeze_raw)or replayed['review_sha256']!=sha(review_raw):raise ValueError('reviewed contract identity changed')
 cases=json.loads((freeze_path/'public-cases.json').read_bytes());public=Path(freeze['public_contract_directory']);rows={r['problem_id']:r for r in catalogue['problems']}
 new={};new_receipts={};descriptors={};locators={};public_contracts={}
 validator_hash=freeze['code_sha256']['catalogue/public-domain-qualification-v2/oracle.py']
 for pid in IDS:
  gid=f'leetcode:{pid}'
  oldjs=rows[gid]['implementations']['javascript'];mapping=oldjs.get('provenance',{}).get('identity_rebinding',{})
  if mapping.get('from_problem_id')!=f'development400:{pid}'or mapping.get('to_problem_id')!=gid or mapping.get('alias_manifest_sha256')!=anchors['aliases']:raise ValueError('authoritative numeric/global identity join missing')
  official_raw=(public/f'{pid}.json').read_bytes();official=json.loads(official_raw)
  if official['problem_id']!=str(pid)or official['source'].get('identity_verified_from_official_page')is not True:raise ValueError('official numeric identity mismatch')
  public_contracts[gid]=official
  per_cases=cases[str(pid)];test_hash=sha(verifier.q.encoded(per_cases))
  for language in ('javascript','python'):
   key=f'{language}:{pid}';source=freeze['sources'][key];old=rows[gid]['implementations'][language]
   outcome=next(x for x in replayed['outcomes']if x['id']==pid and x['language']==language)
   if outcome['source_sha256']!=source['sha256']or outcome['passed']is not True:raise ValueError('source-specific independent verdict missing')
   local_effects={'authority':'explicit independently reviewed local catalogue profile, not official statement requirement',
    'input_mutation':'none',
    'return_alias':'no mutable input/result alias',
    'outside_domain':'unqualified; fail validation before candidate execution',
    'numeric_policy':'plain JSON mathematical integers exclude bool; 1514 probabilities are finite numeric real values in [0,1], with 1 and 1.0 equivalent under transport effects',
    'result_comparison':'finite numeric absolute error <=1e-5; booleans rejected'if pid==1514 else'exact typed ordered structure'}
   contract={'schema':'gamma.reviewed-official-foundation-contract.v2','problem_id':gid,'official_problem_id':pid,
    'official_contract_sha256':sha(official_raw),'official_source':official['source'],'official_preconditions':official['constraints'],
    'official_result':official['result'],'official_complexity':official['complexity'],
    'canonical_parameters':official['interface_proposal']['parameters'],'calling_convention':'solve ordered positional',
    'local_policy':local_effects,'review_sha256':sha(review_raw),'qualification_freeze_sha256':sha(freeze_raw),
    'input_validator':{'module_sha256':validator_hash,'entrypoint':'validate','numeric_problem_id':pid,'must_run_before_public_query_or_candidate_execution':True},
    'finite_oracle_scope':('exhaustive column subsets for width<=12; independently justified equal/uniform larger fixtures only; not an arbitrary-input oracle service'if pid==955 else'only the frozen finite corpus; arbitrary-input oracle evaluation is not authorized'),
    'tree_transport':('canonical trimmed BFS tag, no orphan nodes, 1..8500 nodes, integer labels0..25; separately pinned iterative alias traversal'if pid==988 else None)}
   ch=digest(contract);interface={'schema':'gamma.call-interface.v1','entrypoint':'solve','arguments':'ordered-positional','typed_contract':ch}
   runtime={'language':language,'runtime':freeze['node_runtime']if language=='javascript'else{'python_executable_sha256':freeze['python_runtime_sha256']},'limits':freeze['limits'],
    'sandbox_sha256':freeze['code_sha256']['algsolve/judge/sandbox.py'],'runner_sha256':freeze['code_sha256']['catalogue/public-domain-qualification-v2/qualify.py']}
   harness='catalogue/public-domain-qualification-v2/harness.cjs'if language=='javascript'else'catalogue/public-domain-qualification-v2/harness.py'
   effects={'local_policy':local_effects,'harness_sha256':freeze['code_sha256'][harness],'oracle_and_input_validator_sha256':validator_hash,'independent_verifier_sha256':freeze['code_sha256']['catalogue/public-domain-qualification-v2/verify.py'],'review_sha256':sha(review_raw)}
   previous={'implementation_sha256':digest(old),'receipt_sha256':old.get('receipt_sha256'),'evidence_class':old.get('evidence_class'),'status':old['status'],'source_sha256':old.get('source_sha256'),'base_catalogue_sha256':sha(catalogue_raw)}
   provenance={'public_foundation':{'problem_contract':contract,'per_problem_tests_sha256':test_hash,'tests':len(per_cases),'report_sha256':replayed['report_sha256'],'independent_verification_sha256':sha(verifier_raw),'source_freeze_sha256':sha(freeze_raw),'source_provenance':source,'review_sha256':sha(review_raw)},
    'previous_canonical':previous,'identity_rebinding':mapping,'historical_receipts_unchanged':True,'automatic_historical_pass_upgrade':False}
   scope=f'Official problem {pid} valid-input domain only; reviewed ordered solve interface and explicit local effects. '+'Inputs preserved; no mutable input/result aliases.'
   caveats=['Finite independent in-domain cases are evidence, not a universal correctness theorem.','Official preconditions are bound and must be checked by the frozen input validator before candidate execution or public-query checking.','Local effects are explicit catalogue policy where the official statement is silent.','Historical admitted failures/probes and M1 evidence remain unchanged; recognition/current-serving qualification is separate.']
   if pid==955:caveats.append('The frozen test oracle is partial beyond width12, except independently justified equal/uniform boundary families; domain validation is full but this is not an arbitrary-input oracle service.')
   if pid==1514:caveats.append('Official output tolerance is absolute error <=1e-5, not historical exact comparison; finite real input probabilities compare numerically across JSON integer/float spellings. Arbitrary-input host oracle checks need separate resource controls.')
   if pid==988:caveats.append('Tree transport uses canonical trimmed BFS without orphan nodes and iterative alias-path observation; depth8500 is tested.')
   impl={'status':'qualified','canonical_variant_id':language+':'+source['sha256'],'source_sha256':source['sha256'],'problem_contract_sha256':ch,'interface':interface,'interface_sha256':digest(interface),'runtime_sha256':digest(runtime),'tests_sha256':test_hash,'effects_sha256':digest(effects),'evidence_class':'normative-typed-effects','contract_scope':scope,'caveats':caveats,'provenance':provenance}
   receipt={k:impl[k]for k in (*BINDINGS,'canonical_variant_id','evidence_class','contract_scope','caveats')}
   receipt.update(problem_id=gid,language=language,verdict='qualified',independent_verifier=True,provenance_sha256=digest(provenance),original_independent_verification_sha256=sha(verifier_raw),review_sha256=sha(review_raw),per_problem_case_count=len(per_cases),verification_mode='actual replay of all frozen public raw observations plus independently approved clauses/source/local-policy review')
   rid=digest(receipt);impl['receipt_sha256']=rid;new[(gid,language)]=impl;new_receipts[rid]=receipt;descriptors[key]={'problem_contract':contract,'runtime':runtime,'effects':effects};locators.setdefault(gid,{})[language]=str(freeze_path/source['path'])
 updated,all_receipts,summary=replace_canonicals(universe,catalogue,receipts,new,new_receipts)
 if summary['language_counts']['javascript']['qualified']!=400 or summary['language_counts']['python']['qualified']!=392:raise ValueError('prospective coverage mismatch')
 a.output.mkdir(parents=True,exist_ok=False)
 audit={'schema':'gamma.public-foundation.adoption.v2','base_catalogue_sha256':sha(catalogue_raw),'base_receipts_sha256':sha(receipts_raw),'universe_sha256':sha(universe_raw),'anchors_sha256':sha(anchors_raw),'independent_verifier_sha256':sha(verifier_raw),'review_sha256':sha(review_raw),'adopted_source_language_pairs':28,'previous_receipts_preserved':len(receipts),'new_receipts':len(new_receipts),'historical_m1_qualified':False,'protected_source_or_case_reads':0,'new_candidate_executions':0,'adapter_sha256':sha(Path(__file__).read_bytes())}
 for name,value in [('catalogue.json',updated),('verified-receipts.json',all_receipts),('summary.json',summary),('adoption.json',audit),('foundation-binding-descriptors.json',descriptors),('foundation-source-locators.json',{'schema':'gamma.dual.source-locators.v1','problems':locators})]:
  (a.output/name).write_text(json.dumps(value,sort_keys=True,indent=2)+'\n')
 (a.output/'universe.json').write_bytes(universe_raw);(a.output/'anchors.json').write_bytes(anchors_raw)
 return summary

if __name__=='__main__':
 p=argparse.ArgumentParser()
 for name in ('base','report','verified','output'):p.add_argument('--'+name,type=Path,required=True)
 for name in ('trusted-base-catalogue-sha256','trusted-verifier-sha256'):p.add_argument('--'+name,required=True)
 print(json.dumps(adopt(p.parse_args()),sort_keys=True))
