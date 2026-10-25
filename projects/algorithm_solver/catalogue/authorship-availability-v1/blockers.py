"""Linked contract-availability correction; preserve Git provenance/qualification."""
import argparse,copy,json
from pathlib import Path
from projects.algorithm_solver.catalogue.catalogue import validate,digest
from projects.algorithm_solver.catalogue.recognition_documents import pinned_metadata,encoded,sha
from projects.algorithm_solver.catalogue.boundary_policy import authorize_before_open


def validate_authority(patch,review,worklist):
    if patch.get('schema')!='gamma.catalogue-contract-blocker-patch.v1':raise ValueError('blocker patch schema')
    ids=patch.get('problem_ids')
    if ids!=['leetcode:2792']or patch.get('languages')!=['javascript','python']:raise ValueError('exact reviewed2792 two-slot correction')
    if review.get('independent_review')is not True or 2792 not in review.get('blocked_ids',[])or 2792 in review.get('ids',[]):raise ValueError('independent locked-contract review required')
    if '2792'not in worklist.get('blocked_ids',{})or 2792 in worklist.get('wave_ids',[])or '1788'not in worklist.get('previous_blocked_ids',{}):raise ValueError('worklist blockers inconsistent')
    if review.get('freeze_sha256')!=patch['authority_freeze']['sha256']:raise ValueError('review/freeze binding')
    if not isinstance(patch.get('reason'),str)or not patch['reason']:raise ValueError('explicit contract blocker reason required')
    for key in ('qualification_created','source_publication_authorized'):
        if patch.get(key)is not False:raise ValueError('no new authority')
    for key in ('source_payload_reads','statement_payload_reads','candidate_executions'):
        if type(patch.get(key))is not int or patch[key]!=0:raise ValueError('metadata-only correction')


def correct(universe,catalogue,receipts,patch,patch_sha,*,authorize):
    before=validate(universe,catalogue,receipts);original=copy.deepcopy(catalogue);receipt_copy=copy.deepcopy(receipts)
    ids=patch['problem_ids'];languages=patch['languages'];oldrows={r['problem_id']:r for r in catalogue['problems']}
    for pid in ids:
        if pid not in oldrows or pid in universe['protected_problem_ids']:raise PermissionError('unknown/protected correction identity')
        for lang in languages:
            old=oldrows[pid]['implementations'][lang]
            if old['status']in('qualified','protected'):raise ValueError('correction cannot change qualified/protected slots')
            authorize(pid,lang)
    out=copy.deepcopy(catalogue);rows={r['problem_id']:r for r in out['problems']};changes=[]
    for pid in ids:
        for lang in languages:
            old=oldrows[pid]['implementations'][lang];impl=rows[pid]['implementations'][lang];provenance=impl.get('provenance')
            if not isinstance(provenance,dict)or provenance.get('owner_git_metadata',{}).get('inventory_patch_sha256')!=patch['predecessor_inventory_patch_sha256']:raise ValueError('original inventoried Git provenance required')
            prior=provenance.get('contract_availability_blocker')
            if prior is not None:
                if prior.get('patch_sha256')==patch_sha and old['status']=='blocked':continue
                raise ValueError('conflicting blocker correction needs new linked review')
            if old['status']!='authored':raise ValueError('exact authored prestate required')
            provenance['contract_availability_blocker']={'kind':'official-contract-unavailable','reason':patch['reason'],
                'authority_review_sha256':patch['authority_review']['sha256'],'worklist_sha256':patch['worklist']['sha256'],
                'patch_sha256':patch_sha,'previous_status':old['status'],'previous_reason':old['reason'],
                'source_payload_read':False,'statement_payload_read':False,'qualification_created':False}
            impl['status']='blocked';impl['reason']=patch['reason']
            # Existing bindings, failed attempts and owner Git inventory survive.
            for key,value in old.items():
                if key not in ('status','reason','provenance')and impl.get(key)!=value:raise ValueError('existing implementation binding changed')
            for key,value in old['provenance'].items():
                if impl['provenance'].get(key)!=value:raise ValueError('existing source/failure provenance changed')
            changes.append({'problem_id':pid,'language':lang,'old_status':old['status'],'new_status':'blocked'})
    after=validate(universe,out,receipts)
    if before['qualified_by_evidence_class']!=after['qualified_by_evidence_class']or receipts!=receipt_copy or catalogue!=original:raise ValueError('qualification/receipt/input change')
    changed={(c['problem_id'],c['language'])for c in changes}
    for pid,row in oldrows.items():
        for lang,old in row['implementations'].items():
            if (pid,lang)not in changed and rows[pid]['implementations'][lang]!=old:raise ValueError('unrelated slot changed')
    return out,{'schema':'gamma.catalogue-contract-blocker-audit.v1','changed_slots':changes,'changed_slot_count':len(changes),
        'patch_sha256':patch_sha,'base_catalogue_value_sha256':digest(catalogue),'result_catalogue_value_sha256':digest(out),
        'before':before,'after':after,'receipt_count_preserved':len(receipts),'owner_git_provenance_preserved':True,
        'unrelated_slots_preserved':True,'qualification_created':False,'source_locators_added':0,'source_payload_reads':0,
        'statement_payload_reads':0,'candidate_executions':0,'recognition_qualified':False}


def prepare(config_spec,patch_spec,output):
    patch=pinned_metadata(patch_spec);config=pinned_metadata(config_spec)
    root=Path(__file__).resolve().parent
    for name,pin in patch['mechanism_code_sha256'].items():
        if sha((root/name).read_bytes())!=pin:raise ValueError('blocker mechanism code drift')
    for name,pin in patch['dependency_code_sha256'].items():
        if sha((root.parent/name).read_bytes())!=pin:raise ValueError('catalogue/gate dependency drift')
    if config_spec['sha256']!=patch['base_config_sha256']or config['catalogue']['sha256']!=patch['base_catalogue_sha256']:raise ValueError('exactv21 base identity')
    if config['source_access']['boundary_gate']!=patch['boundary_gate']:raise ValueError('boundary cannot change')
    review=pinned_metadata(patch['authority_review']);worklist=pinned_metadata(patch['worklist']);validate_authority(patch,review,worklist)
    # The authority freeze is metadata only: prove its exact byte identity and
    # the worklist pin, without opening any2792 source/statement/cases/locators.
    authority=pinned_metadata(patch['authority_freeze'])
    worklist_matches=[h for name,h in authority['statement_sha256'].items()if name.endswith('/worklist.json')]
    if worklist_matches!=[patch['worklist']['sha256']]:raise ValueError('worklist not pinned by exact reviewed freeze')
    gate=pinned_metadata(patch['boundary_gate']);u=pinned_metadata(config['universe']);cat=pinned_metadata(config['catalogue']);receipts=pinned_metadata(config['verified_receipts'])
    def authorize(pid,lang):authorize_before_open(pid,gate['artifact_paths'],gate['trusted_hashes'],language=lang,payload_kind='source')
    out,audit=correct(u,cat,receipts,patch,patch_spec['sha256'],authorize=authorize)
    output=Path(output);output.mkdir(exist_ok=False)
    raw=encoded(out);(output/'catalogue.json').write_bytes(raw)
    successor=copy.deepcopy(config);successor['catalogue']={'path':str((output/'catalogue.json').resolve()),'sha256':sha(raw)}
    (output/'config.json').write_bytes(encoded(successor));(output/'audit.json').write_bytes(encoded(audit))
    summary={'schema':'gamma.catalogue-contract-blocker-candidate.v1','status':'prepared_not_installed','base_config_sha256':config_spec['sha256'],
        'candidate_config_sha256':sha(encoded(successor)),'candidate_catalogue_sha256':sha(raw),'patch_sha256':patch_spec['sha256'],
        'changed_slot_count':len(audit['changed_slots']),'changed_slots':audit['changed_slots'],'qualified_artifacts':{lang:audit['after']['language_counts'][lang]['qualified']for lang in ('javascript','python')},
        'receipt_count_preserved':len(receipts),'source_access_config_unchanged':successor['source_access']==config['source_access'],
        'universe_descriptor_unchanged':successor['universe']==config['universe'],'receipt_descriptor_unchanged':successor['verified_receipts']==config['verified_receipts'],
        'qualification_created':False,'source_payload_reads':0,'statement_payload_reads':0,'source_locators_added':0,'candidate_executions':0,'recognition_qualified':False}
    (output/'summary.json').write_bytes(encoded(summary));return summary

if __name__=='__main__':
    p=argparse.ArgumentParser()
    for name in ('config','config-sha256','patch','patch-sha256','output'):p.add_argument('--'+name,required=True)
    a=p.parse_args();print(json.dumps(prepare({'path':str(Path(a.config).resolve()),'sha256':a.config_sha256},{'path':str(Path(a.patch).resolve()),'sha256':a.patch_sha256},a.output),sort_keys=True))
