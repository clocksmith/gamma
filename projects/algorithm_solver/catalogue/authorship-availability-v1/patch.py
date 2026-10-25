"""Reusable existing-catalogue authorship inventory; never source/qualification.

Operator-pinned inputs and live boundary checks are mandatory. The CLI previews
only aggregate metadata; it neither changes a registry/config nor creates locators.
"""
import argparse,copy,json,re
from pathlib import Path,PurePosixPath
from projects.algorithm_solver.catalogue.catalogue import validate,digest,BINDINGS
from projects.algorithm_solver.catalogue.recognition_documents import pinned_metadata
from projects.algorithm_solver.catalogue.boundary_policy import authorize_before_open

ITEM_FIELDS={'git_blob_object_id','git_object_hash_algorithm','language','owner_commit','problem_id','repository_path','source_sha256_known_from_this_inventory'}
HEX40=re.compile(r'[0-9a-f]{40}\Z');HEX64=re.compile(r'[0-9a-f]{64}\Z');ID=re.compile(r'leetcode:([1-9][0-9]*)\Z')
REASON='Exact owner Git blob inventoried under current live authorization; normative contract/source-specific typed/effect qualification not established. No source-serving locator or qualification receipt created.'

def inventory_items(patch,universe):
    if patch.get('schema')!='gamma.existing-catalogue-authorship-patch.v1':raise ValueError('patch schema')
    for key in ('qualification_created','source_publication_authorized'):
        if patch.get(key)is not False:raise ValueError('inventory cannot create authority')
    for key in ('candidate_executions','source_payload_reads','statement_payload_reads'):
        if type(patch.get(key))is not int or patch[key]!=0:raise ValueError('metadata-only scope required')
    if patch.get('population')!=len(universe['eligible_problem_ids'])or patch.get('language_slots')!=2*len(universe['eligible_problem_ids']):raise ValueError('universe denominator changed')
    commit=patch.get('owner_commit')
    if not isinstance(commit,str)or not HEX40.fullmatch(commit):raise ValueError('exact owner Git commit required')
    items=patch.get('metadata_inventory');seen=set()
    if not isinstance(items,list)or not items:raise ValueError('nonempty inventory required')
    for item in items:
        if not isinstance(item,dict)or set(item)!=ITEM_FIELDS:raise ValueError('only whitelisted Git metadata fields')
        pid,lang=item['problem_id'],item['language']
        id_match=ID.fullmatch(pid)if isinstance(pid,str)else None
        if not id_match or pid not in universe['eligible_problem_ids']or lang not in ('javascript','python')or (pid,lang)in seen:raise ValueError('duplicate/unknown exact slot')
        seen.add((pid,lang));path=item['repository_path'];parts=PurePosixPath(path).parts if isinstance(path,str)else()
        suffix='js'if lang=='javascript'else'py'
        if (not parts or path.startswith('/')or '\\'in path or '..'in parts or '.'in path.split('/')or ''in path.split('/')or
            not path.startswith('projects/algorithm_solver/catalogue/authored/')or parts[-2]!=lang or parts[-1]!=id_match[1]+'.'+suffix):raise ValueError('identity-bound relative Git path required')
        if (item['owner_commit']!=commit or item['git_object_hash_algorithm']!='sha1'or
            not isinstance(item['git_blob_object_id'],str)or not HEX40.fullmatch(item['git_blob_object_id'])or item['source_sha256_known_from_this_inventory']is not False):raise ValueError('Git identity is not source-byte qualification')
    blocked=patch.get('declared_blocked')
    if not isinstance(blocked,dict)or any(pid not in {x[0]for x in seen}or not isinstance(reason,str)or not reason for pid,reason in blocked.items()):raise ValueError('explicit inventory-scoped blockers required')
    return items


def apply_inventory(universe,catalogue,receipts,patch,patch_sha256,*,authorize):
    """Internal trusted authorize(pid, language) callback; not request-supplied flags.

    All live authorizations finish before any proposed update. Inputs are not
    mutated; caller retains separate authority to publish the returned catalogue.
    """
    if not isinstance(patch_sha256,str)or not HEX64.fullmatch(patch_sha256):raise ValueError('patch byte SHA required')
    before=validate(universe,catalogue,receipts);items=inventory_items(patch,universe)
    original=copy.deepcopy(catalogue);receipt_snapshot=copy.deepcopy(receipts)
    keyed={r['problem_id']:r for r in catalogue['problems']}
    for item in items:
        pid,lang=item['problem_id'],item['language']
        if pid in universe['protected_problem_ids']or keyed[pid]['implementations'][lang]['status']=='protected':raise PermissionError('protected slot cannot become authored')
        authorize(pid,lang)
    result=copy.deepcopy(catalogue);rows={r['problem_id']:r for r in result['problems']};changes=[];qualified=0;already=0
    for item in items:
        pid,lang=item['problem_id'],item['language'];old=keyed[pid]['implementations'][lang]
        if old['status']=='qualified':qualified+=1;continue
        proposed=copy.deepcopy(old);provenance=proposed.setdefault('provenance',{})
        if not isinstance(provenance,dict):raise ValueError('structured unqualified provenance required')
        evidence=dict(item,inventory_patch_sha256=patch_sha256,source_payload_read=False,qualification_created=False,source_publication_authorized=False)
        existing=provenance.get('owner_git_metadata')
        if existing is not None and existing!=evidence:raise ValueError('conflicting existing owner inventory requires linked review')
        status='blocked'if pid in patch['declared_blocked']else'authored'
        if existing==evidence and old['status']==status:already+=1;continue
        provenance['owner_git_metadata']=evidence
        if old['status']!=status:
            history=provenance.setdefault('availability_history',[])
            if not isinstance(history,list):raise ValueError('availability history type')
            history.append({'status':old['status'],'reason':old['reason'],'slot_sha256':digest(old)})
        proposed['status']=status
        if status=='blocked':
            declared=patch['declared_blocked'][pid]
            # Never discard an existing failure explanation, including1743 OOM.
            if old['reason']!=declared:provenance['declared_availability_blocker']=declared
            proposed['reason']=old['reason']if old['status']=='blocked'else declared
        elif old['status']!='authored':proposed['reason']=REASON
        for field in (*BINDINGS,'receipt_sha256','interface','canonical_variant_id','evidence_class','contract_scope','caveats'):
            if proposed.get(field)!=old.get(field):raise ValueError('inventory cannot invent/change qualification bindings')
        rows[pid]['implementations'][lang]=proposed
        changes.append({'problem_id':pid,'language':lang,'old_status':old['status'],'new_status':status})
    after=validate(universe,result,receipts)
    changed={(x['problem_id'],x['language'])for x in changes}
    for pid,row in keyed.items():
        for lang,old in row['implementations'].items():
            if (pid,lang)not in changed or old['status']=='qualified':
                if rows[pid]['implementations'][lang]!=old:raise ValueError('unlisted/qualified slot changed')
    if before['qualified_by_evidence_class']!=after['qualified_by_evidence_class']or receipts!=receipt_snapshot or catalogue!=original:raise ValueError('qualification/receipt/input mutation')
    return result,{'schema':'gamma.catalogue-authorship-metadata-preview.v1','changed_slots':changes,'changed_slot_count':len(changes),
        'qualified_inventory_slots_preserved':qualified,'already_applied_unqualified_slots':already,'receipt_count_preserved':len(receipts),
        'before':before,'after':after,'base_catalogue_value_sha256':digest(catalogue),'result_catalogue_value_sha256':digest(result),
        'patch_sha256':patch_sha256,'source_payload_reads':0,'statement_payload_reads':0,'candidate_executions':0,
        'qualification_created':False,'source_locators_added':0,'source_publication_authorized':False}


def preview(config_spec,patch_spec):
    patch=pinned_metadata(patch_spec);config=pinned_metadata(config_spec)
    if config['source_access']['boundary_gate']!=patch['boundary_gate']:raise ValueError('boundary change requires fresh review')
    gate=pinned_metadata(patch['boundary_gate']);universe=pinned_metadata(config['universe']);catalogue=pinned_metadata(config['catalogue']);receipts=pinned_metadata(config['verified_receipts'])
    def authorize(pid,language):
        authorize_before_open(pid,gate['artifact_paths'],gate['trusted_hashes'],language=language,payload_kind='source')
    return apply_inventory(universe,catalogue,receipts,patch,patch_spec['sha256'],authorize=authorize)

if __name__=='__main__':
    p=argparse.ArgumentParser()
    for name in ('config','config-sha256','patch','patch-sha256'):p.add_argument('--'+name,required=True)
    args=p.parse_args()
    _,audit=preview({'path':str(Path(args.config).resolve()),'sha256':args.config_sha256},{'path':str(Path(args.patch).resolve()),'sha256':args.patch_sha256})
    print(json.dumps(audit,sort_keys=True))
