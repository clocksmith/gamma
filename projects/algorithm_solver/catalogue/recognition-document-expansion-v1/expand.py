"""Lawful normative document expansion; all4081 competitors, no encoder/source."""
import argparse,json
from pathlib import Path
from projects.algorithm_solver.catalogue import boundary_policy
from projects.algorithm_solver.catalogue.catalogue import validate
from projects.algorithm_solver.catalogue.recognition_documents import pinned_metadata,encoded,sha,build


def identity_union(baseline_plan,statuses,expected):
    old=[r['problem_id']for r in baseline_plan['authorities']]
    if len(old)!=54 or len(set(old))!=54:raise ValueError('exact old54 authority IDs')
    ids=set(old)
    for status in statuses:
        additions=status.get('new_problem_ids')
        if not isinstance(additions,list)or len(additions)!=8 or len(set(additions))!=8 or ids.intersection(additions):raise ValueError('distinct eight-ID adoption metadata')
        ids.update(additions)
    if len(ids)!=expected:raise ValueError('expected normative denominator')
    return ids


def assemble(config,*,reader=pinned_metadata,authorize=boundary_policy.authorize_before_open):
    """All IDs come from metadata and get live authorization before catalogue read.

    Status metadata is not semantic authority. Existing normative qualification,
    canonical contract SHA, and verified catalogue receipts remain authoritative.
    No paths from source locators/provenance are followed.
    """
    old=reader(config['baseline_plan']);statuses=[reader(s)for s in config['adoption_statuses']]
    ids=identity_union(old,statuses,config['expected_normative'])
    service=reader(config['service']);gate=reader(old['boundary_gate'])
    if service['source_access']['boundary_gate']!=old['boundary_gate']:raise ValueError('same boundary required')
    for pid in sorted(ids):authorize(pid,gate['artifact_paths'],gate['trusted_hashes'],language='javascript',payload_kind='statement')
    # Read only operator-pinned combined artifacts AFTER the complete gate set.
    catalogue=reader(service['catalogue']);universe=reader(service['universe']);receipts=reader(service['verified_receipts'])
    validate(universe,catalogue,receipts)
    # Metadata-only classification outside the permitted set: never inspect its
    # semantic provenance, source paths or problem contracts.
    normative={r['problem_id']for r in catalogue['problems']if any(impl.get('status')=='qualified'and impl.get('evidence_class')=='normative-typed-effects'for impl in r['implementations'].values())}
    if normative!=ids:raise ValueError('metadata identity set differs from normative authority population')
    known={r['problem_id']:r for r in catalogue['problems']};old_pins={r['problem_id']:r['problem_contract_sha256']for r in old['authorities']}
    authorities=[]
    for pid in sorted(ids,key=lambda x:int(x.split(':')[1])):
        # The existing enrich adapter will independently gate every later open
        # and extract only its named semantic fields from the selected contract.
        impl=known[pid]['implementations']['javascript']
        if impl.get('status')!='qualified'or impl.get('evidence_class')!='normative-typed-effects':raise ValueError('exact JS normative contract required')
        contract_sha=impl['problem_contract_sha256']
        if pid in old_pins and contract_sha!=old_pins[pid]:raise ValueError('old semantic contract changed; separate successor required')
        authorities.append({'problem_id':pid,'kind':'normative-catalogue','language':'javascript','catalogue':service['catalogue'],'universe':service['universe'],'verified_receipts':service['verified_receipts'],'problem_contract_sha256':contract_sha})
    roots=sorted({str(Path(service[k]['path']).parent)for k in ('catalogue','universe','verified_receipts')})
    return dict(old,authorities=authorities,authority_roots=roots),ids


def check_expansion(old,new,ids):
    if old['population']!=4081 or new['population']!=4081 or old['stable_ids']!=new['stable_ids']:raise ValueError('complete competitor population/order changed')
    if len(set(new['stable_ids']))!=4081:raise ValueError('duplicate universe identity')
    oldrows={r['problem_id']:r for r in old['documents']};changed=[]
    for row in new['documents']:
        pid=row['problem_id'];prior=oldrows[pid]
        if prior['authority']['knowledge_class']!='title-only' and row['text']!=prior['text']:raise ValueError('old54 semantic text changed')
        if pid not in ids and (row['text']!=prior['text']or row['authority']['knowledge_class']!='title-only'):raise ValueError('unauthorized/title-only text changed')
        if row['text']!=prior['text']:changed.append(pid)
    if new['enriched']!=len(ids)or len(changed)!=len(ids)-54:raise ValueError('exact enrichment delta not preserved')
    return changed


def run(args):
    config=pinned_metadata({'path':str(args.config),'sha256':args.config_sha256})
    root=Path(__file__).resolve().parent
    for name,pin in config['code_sha256'].items():
        if sha((root/name).read_bytes())!=pin:raise ValueError('expansion code drift')
    for name,pin in config['dependency_code_sha256'].items():
        if sha((root.parent/name).read_bytes())!=pin:raise ValueError('document authority dependency drift')
    plan,ids=assemble(config)
    # Original document payload has only original54 authorized semantics; all102
    # IDs were gated before this combined open. Builder repeats gates per-open.
    gate=pinned_metadata(plan['boundary_gate'])
    for pid in sorted(ids):boundary_policy.authorize_before_open(pid,gate['artifact_paths'],gate['trusted_hashes'],language='javascript',payload_kind='statement')
    old=pinned_metadata(config['baseline_documents']);new=build(plan);changed=check_expansion(old,new,ids)
    output=Path(args.output);output.mkdir(exist_ok=False)
    (output/'plan.json').write_bytes(encoded(plan));(output/'documents.json').write_bytes(encoded(new))
    summary={'schema':'gamma.recognition-document-expansion-summary.v1','config_sha256':args.config_sha256,
        'plan_sha256':sha(encoded(plan)),'artifact_sha256':sha(encoded(new)),'population':4081,'enriched':len(ids),'title_only':4081-len(ids),
        'previous_authoritative_documents':54,'new_semantic_documents':len(changed),'changed_from_prior_documents':changed,
        'old54_text_unchanged':True,'all_ids_order_unchanged':True,'source_availability_filter':False,
        'candidate_source_reads':0,'case_reads':0,'encoder_invocations':0,'query_cohort_reads':0,'confirmation_read':False,
        'recognition_qualified':False,'authority_scope':'Existing reviewed normative catalogue contracts only; title-only identities stay competitors and unknown.'}
    (output/'summary.json').write_bytes(encoded(summary));print(json.dumps(summary,sort_keys=True))

if __name__=='__main__':
    p=argparse.ArgumentParser()
    for name in ('config','config-sha256','output'):p.add_argument('--'+name,required=True)
    run(p.parse_args())
