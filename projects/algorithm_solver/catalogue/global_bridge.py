"""Rebind verified development identities into the complete metadata universe.

Exact numeric aliases preserve qualification scope; this is not a new judge pass.
External hash anchors authenticate the metadata/access-policy inputs. No source,
statement, case or output payload is read.
"""
import copy
import hashlib
import json
from .catalogue import digest, validate


def import_global(development_universe_raw, development_catalogue, verified_receipts,
                  global_universe_raw, aliases_raw, access_policy_raw, trusted_hashes):
    raw_inputs = {'development_universe':development_universe_raw,
                  'global_universe':global_universe_raw, 'aliases':aliases_raw,
                  'access_policy':access_policy_raw}
    for name,raw in raw_inputs.items():
        if hashlib.sha256(raw).hexdigest() != trusted_hashes.get(name):
            raise ValueError('external metadata anchor mismatch: '+name)
    old=json.loads(development_universe_raw); universe=json.loads(global_universe_raw)
    aliases=json.loads(aliases_raw); policy=json.loads(access_policy_raw)
    validate(old,development_catalogue,verified_receipts)
    if aliases.get('schema')!='gamma.numeric-id-alias-map.v1' or aliases.get('source_payload_reads')!=0 or aliases.get('case_payload_reads')!=0:
        raise ValueError('not a metadata-only exact alias map')
    if aliases.get('from_universe_sha256')!=trusted_hashes['development_universe'] or aliases.get('to_universe_sha256')!=trusted_hashes['global_universe']:
        raise ValueError('alias universe identity mismatch')
    mapping=aliases['aliases'];all_ids=set(universe['eligible_problem_ids']);protected=set(universe['protected_problem_ids'])
    allowed=policy.get('authorized_existing_source_problem_ids')
    if not isinstance(allowed,list) or any(not isinstance(x,str) for x in allowed) or len(allowed)!=len(set(allowed)):
        raise ValueError('explicit unique source-access identities required')
    if policy.get('schema')!='gamma.all4081-source-access-policy.v1' or policy.get('new_source_access_authorized') is not False or policy.get('source_publication_authorized') is not False:
        raise ValueError('unexpected source access/publication scope')
    if policy.get('population_size')!=len(all_ids) or policy.get('language_slots')!=2*len(all_ids) or policy.get('outside_authorized_count')!=len(all_ids)-len(allowed):
        raise ValueError('access policy denominator differs')
    if set(mapping)!=set(old['eligible_problem_ids']) or len(set(mapping.values()))!=len(mapping) or set(mapping.values())!=set(allowed) or not set(allowed)<=all_ids or set(allowed)&protected:
        raise ValueError('alias/authorization/coverage mismatch')
    for before,after in mapping.items():
        if not before.startswith('development400:') or not after.startswith('leetcode:') or before.split(':',1)[1]!=after.split(':',1)[1] or not after.split(':',1)[1].isdecimal():
            raise ValueError('only exact numeric identity rebinding is permitted')
    old_rows={row['problem_id']:row for row in development_catalogue['problems']};reverse={v:k for k,v in mapping.items()}
    receipts={};rows=[]
    for pid in universe['eligible_problem_ids']:
        if pid not in reverse:
            status='protected' if pid in protected else 'blocked'
            reason='Reserved source access remains closed.' if status=='protected' else 'Metadata only: source availability, broader reservation membership, provenance and publication permission require separate review; no source access authorized.'
            rows.append({'problem_id':pid,'implementations':{lang:{'status':status,'reason':reason}for lang in ('javascript','python')}})
            continue
        before=reverse[pid];implementations=copy.deepcopy(old_rows[before]['implementations'])
        for language,impl in implementations.items():
            if impl['status']!='qualified':continue
            original_id=impl['receipt_sha256'];receipt=copy.deepcopy(verified_receipts[original_id])
            provenance={'original_provenance':impl['provenance'],'identity_rebinding':{'from_problem_id':before,'to_problem_id':pid,'original_receipt_sha256':original_id,'alias_manifest_sha256':trusted_hashes['aliases'],'access_policy_sha256':trusted_hashes['access_policy'],'qualification_scope_unchanged':True}}
            impl['provenance']=provenance;receipt['problem_id']=pid;receipt['provenance_sha256']=digest(provenance)
            receipt['identity_rebinding_only']=True;receipt['original_receipt_sha256']=original_id
            rid=digest(receipt);impl['receipt_sha256']=rid;receipts[rid]=receipt
        rows.append({'problem_id':pid,'implementations':implementations})
    catalogue={'schema':'gamma.dual-language-catalogue.v2','universe_sha256':digest(universe),'evidence_policy':copy.deepcopy(development_catalogue['evidence_policy']),'problems':rows}
    summary=validate(universe,catalogue,receipts)
    summary.update(identity_aliases=len(mapping),new_source_access=False,new_candidate_executions=0,new_case_reads=0,source_publication_authorized=False)
    return catalogue,receipts,summary
