"""Freeze statement-admitted historical cases, corrections, and public examples.

Every original vector and exclusion remains in a separate ledger. Selection is
input-domain based; neither candidate outputs nor prior pass flags decide it.
"""
import argparse
import ast
from copy import deepcopy
import html
import json
from pathlib import Path
import re

from . import imported_qualification as q
from . import imported_case_admission as admission
from . import imported_clean_domains as clean
from . import imported_result_contracts as results
from . import verify_imported_semantics as independent
from .boundary_policy import authorize_before_open
from .known_spec_service import KnownSpecService, _boundary_snapshot

ORIGINAL_SHA = '956e15f937b9f457014eaac7d91939209ba3901f3f4f5f9e93b53f41ed037e43'
TREE_ARGUMENTS = {783,814,938,958,998,1026,1339,1372,1382,1609,2236,2385,2583,2792}
LIST_ARGUMENTS = {876,1290,2074,2807,2816}


class Names(ast.NodeTransformer):
    def visit_Name(self,node):
        if node.id not in ('true','false','null'):raise ValueError('unsupported bare example token')
        return ast.copy_location(ast.Constant({'true':True,'false':False,'null':None}[node.id]),node)


def validate(pid,args):
    return (admission.validate if pid in admission.DOMAIN_IDS else clean.validate)(pid,args)


def examples(pid,raw):
    markup=re.sub(r'<table\b[^>]*>.*?</table>','',raw.decode(),flags=re.S)
    text=re.sub(r'</?(?:p|pre|div|li|ul|ol|br)\b[^>]*>','\n',markup)
    text=html.unescape(re.sub('<[^>]*>','',text)).replace('\xa0',' ')
    if pid==2061:text=text.replace('\u200b','')  # zero-width layout marks after example output
    cases=[]
    for match in re.finditer(r'Input:\s*(.*?)\s*Output:\s*(.*?)(?=Explanation:|Explantion:|Example\s*\d+:|Constraints:|$)',text,re.S):
        call=ast.parse('f('+match[1].strip()+')',mode='eval').body
        if not isinstance(call,ast.Call) or call.args or not call.keywords or any(k.arg is None for k in call.keywords):raise ValueError('ordered named public arguments required')
        args=[ast.literal_eval(Names().visit(k.value))for k in call.keywords]
        want=ast.literal_eval(Names().visit(ast.parse(match[2].strip(),mode='eval')).body)
        if pid in TREE_ARGUMENTS:args[0]={'__tree_node__':args[0]} if args[0]is not None else None
        if pid in LIST_ARGUMENTS:args[0]={'__list_node__':args[0]}
        if pid==1305:args=[{'__tree_node__':v} if v is not None else None for v in args]
        if pid in results.NODE_RETURNS:
            key='__tree_node__' if results.NODE_RETURNS[pid]=='TreeNode' else '__list_node__'
            want={key:want} if want is not None else None
        validate(pid,args)
        cases.append({'args':args,'expected':want,'compare':'return'})
    if not cases:raise ValueError(f'{pid}: no public examples')
    return cases


def prepare(args):
    KnownSpecService.from_config(args.config,args.config_sha256)
    config=q.decode(q.read(args.config));gate=q.decode(q.read(config['source_access']['boundary_gate']['path']))
    boundary=_boundary_snapshot(gate)
    original_raw=q.read(args.original/'contract.json')
    if q.sha(original_raw)!=ORIGINAL_SHA:raise ValueError('original frozen population differs')
    original=q.decode(original_raw)
    replacements=q.decode(q.read(args.replacements)) if args.replacements else []
    replacement_map={(r['id'],r['language']):r for r in replacements}
    if len(replacement_map)!=len(replacements):raise ValueError('duplicate source replacement authority')
    supplements=q.decode(q.read(args.supplements)) if args.supplements else []
    for supplement in supplements:
        if q.file_hash(supplement['path'])!=supplement['sha256']:raise ValueError('supplement drift')
    by_id={j['id']:j for j in original['jobs']}
    if len(by_id)!=358 or len(original['jobs'])!=716:raise ValueError('incomplete original population')
    cases_by_id={};decisions={};example_counts={}
    for pid,job in sorted(by_id.items()):
        identity=f'leetcode:{pid}'
        if identity not in boundary.authorized:raise PermissionError('original identity no longer permitted')
        authorize_before_open(identity,gate['artifact_paths'],gate['trusted_hashes'],language='python',payload_kind='statement')
        statement=q.read(job['statement']['path'])
        if q.sha(statement)!=job['statement']['sha256']:raise ValueError('pinned statement differs')
        # This is the explicit user-authorized qualification-case scope. The
        # recovered source policy alone does not confer access to protected cases.
        authorize_before_open(identity,gate['artifact_paths'],gate['trusted_hashes'],language='python')
        raw=q.read(args.original/job['tests'])
        if q.sha(raw)!=job['tests_raw_sha256']:raise ValueError('original test bytes differ')
        original_cases=q.decode(raw);accepted=[];ledger=[]
        for i,case in enumerate(original_cases):
            if pid in admission.DOMAIN_IDS:
                decision=admission.admit_case(pid,case)
            else:
                try:
                    if set(case)!={'args','expected','compare'} or case['compare']!='return':raise ValueError('unsupported case fields')
                    clean.validate(pid,case['args'])
                    decision={'status':'statement-domain-admitted','original':deepcopy(case)}
                except ValueError as error:
                    decision={'status':'rejected-domain','original':deepcopy(case),'reason':str(error)}
            decision['original_index']=i
            if decision['status']!='rejected-domain':
                selected=deepcopy(decision.get('case',case));validate(pid,selected['args'])
                decision['frozen_case_index']=len(accepted);accepted.append(selected)
            ledger.append(decision)
        public=examples(pid,statement);example_counts[str(pid)]=len(public)
        accepted.extend(public)
        for item in supplements:
            if item['id']==pid and item['kind']=='cases':
                extra=q.decode(q.read(item['path']))
                for case in extra:validate(pid,case['args'])
                accepted.extend(extra)
        if not accepted:raise ValueError('no independently admitted cases')
        # Enforce every resource packet boundary before launching any source.
        list(q.batches(accepted))
        cases_by_id[pid]=accepted
        decisions[pid]={'id':pid,'statement':job['statement'],'original_tests_raw_sha256':job['tests_raw_sha256'],
                       'decisions':ledger,'public_examples':public,
                       'supplements':[s for s in supplements if s['id']==pid]}
    args.output.mkdir(parents=True,exist_ok=False)
    for name in ('sources','tests','admission'): (args.output/name).mkdir()
    jobs=[]
    for old in original['jobs']:
        job=deepcopy(old);pid=job['id'];lang=job['language'];identity=f'leetcode:{pid}'
        authorize_before_open(identity,gate['artifact_paths'],gate['trusted_hashes'],language=lang)
        source=q.read(job['original_source'],1024**2);source_sha=q.sha(source)
        if source_sha!=old['source_sha256']:
            replacement=replacement_map.get((pid,lang),{})
            if replacement.get('old_sha256')!=old['source_sha256'] or replacement.get('new_sha256')!=source_sha or not replacement.get('independent_review'):
                raise ValueError('unreviewed candidate replacement')
            job['previous_source_sha256']=old['source_sha256'];job['source_replacement']=replacement
        (args.output/job['source']).write_bytes(source)
        q.write(args.output/job['tests'],cases_by_id[pid]);q.write(args.output/'admission'/f'{pid}.json',decisions[pid])
        job.update(source_sha256=source_sha,tests_raw_sha256=q.file_hash(args.output/job['tests']),
                   tests_canonical_sha256=q.canonical_tests_hash(cases_by_id[pid]),case_count=len(cases_by_id[pid]),
                   domain_validator='imported358-v1',comparison_policy=f'problem:{pid}',
                   admission_sha256=q.file_hash(args.output/'admission'/f'{pid}.json'))
        jobs.append(job)
    modules=(admission,clean,results,independent)
    contract={'schema':'gamma.imported-independent-execution.v1','jobs':jobs,'pending':[],
              'service_config':str(args.config.resolve()),'service_config_sha256':args.config_sha256,
              'original_freeze_sha256':ORIGINAL_SHA,'runtime':q.runtime(),'code':q.code_pins(),'limits':q.LIMITS,
              'additional_code':{str(Path(m.__file__).resolve()):q.file_hash(m.__file__)for m in modules},
              'max_packet_bytes':q.MAX_PACKET,'public_examples_checked':example_counts,
              'test_authority':'Pinned historical independent cases admitted by statement domain; corrections independently derived; pinned public examples and reviewed supplementary cases appended.',
              'effects':'read-only arguments and no return aliases, except876requires original middle-node identity',
              'comparison':'problem-specific typed return contracts; explicit nonunique outputs and absolute numeric tolerances',
              'supplements':supplements,'source_replacements':replacements,
              'scope':'Finite independent statement-domain typed/local-effect checks plus independent static algorithm review; no universal correctness or full-domain runtime proof.',
              'automatic_promotion':False,'protected_access':False}
    contract['additional_code'][str(Path(__file__).resolve())]=q.file_hash(__file__)
    q.write(args.output/'contract.json',contract)
    return {'jobs':len(jobs),'checks':sum(j['case_count']for j in jobs),'public_examples':sum(example_counts.values()),'contract_sha256':q.file_hash(args.output/'contract.json')}


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ('config','original','output'):parser.add_argument('--'+name,type=Path,required=True)
    parser.add_argument('--config-sha256',required=True)
    for name in ('replacements','supplements'):parser.add_argument('--'+name,type=Path)
    print(json.dumps(prepare(parser.parse_args())))
