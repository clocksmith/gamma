"""Metadata-only pending import into the shared catalogue schema.

This adapter does not qualify sources, load source/case payloads, join numeric
IDs to historical slugs, or redefine the full catalogue universe. Its standalone
snapshot is explicitly the already-authorized development400 slice.
"""
import argparse
import hashlib
import json
from pathlib import Path
from .catalogue import digest, hash_value, validate

MISSING_BINDINGS = (
    'independent normative problem contract',
    'canonical typed interface bound to that normative contract',
    'source-specific runtime, tests and effects receipt bindings',
    'trusted normative-typed-effects verifier attestation',
    'numeric development ID to full-catalogue authoritative UID join',
)


def adapt_development(reconciliation, transfer_receipt, filtered_metadata_bytes):
    if reconciliation.get('schema') != 'gamma.python.catalogue-metadata-reconciliation.v1':
        raise ValueError('wrong Python reconciliation schema')
    if reconciliation.get('case_payload_reads') != 0 or reconciliation.get('protected_payload_reads') != 0:
        raise ValueError('metadata-only evidence boundary violated')
    metadata_hash = hashlib.sha256(filtered_metadata_bytes).hexdigest()
    if metadata_hash != transfer_receipt.get('filtered_metadata_sha256'):
        raise ValueError('filtered metadata provenance mismatch')
    partition = transfer_receipt.get('partition', {})
    fit, validation = partition.get('dev_fit', []), partition.get('dev_val', [])
    if len(fit) != 300 or len(validation) != 100 or len(set(fit+validation)) != 400:
        raise ValueError('fixed authorized development400 partition required')
    if transfer_receipt.get('final_heldout_payload_files_opened') != 0 or transfer_receipt.get('protected_payload_files_opened') != 0:
        raise ValueError('protected boundary mismatch')
    ids = set(fit+validation)
    metadata = json.loads(filtered_metadata_bytes)
    if {row['id'] for row in metadata['rows']} != ids or len(metadata['rows']) != 400:
        raise ValueError('filtered metadata denominator mismatch')
    rows = reconciliation.get('rows', [])
    if len(rows) != 400 or {row['id'] for row in rows} != ids:
        raise ValueError('reconciliation omitted or added development identity')
    universe = {
        'schema': 'gamma.catalogue-universe.v1',
        'eligible_problem_ids': ['development400:'+str(pid) for pid in sorted(ids)],
        'protected_problem_ids': [],
        'metadata_sha256': metadata_hash,
        'eligibility_policy': 'Authorized development400 slice only, independently fixed300 fit+100 validation; not the full catalogue. Namespace is not a historical slug/UID join. Final100 and protected66 are outside this snapshot and remain closed.',
    }
    problems = []
    pending = blocked = compatible = 0
    for row in sorted(rows, key=lambda x:x['id']):
        pid = row['id']
        expected_partition = 'dev_fit' if pid in fit else 'dev_val'
        if row.get('partition') != expected_partition:
            raise ValueError('development partition drift')
        source = row.get('canonical_proposal')
        if source is not None:
            if row.get('current_dot_qualification') is not True or row.get('reference_compatibility_only') is not False:
                raise ValueError('inconsistent pending finite-replay evidence')
            if source.get('evidence_class') != 'finite-independent-frozen-replay' or source.get('entry_point') != 'solve':
                raise ValueError('unsupported source/interface evidence')
            if not hash_value(source.get('source_sha256')) or not hash_value(source.get('report_sha256')):
                raise ValueError('invalid source/report identity')
            implementation = {
                'status':'authored',
                'reason':'Finite replay exists, but normative catalogue receipt bindings are unresolved; not eligible for qualified serving.',
                'canonical_variant_id':'python:'+source['source_sha256'],
                'source_sha256':source['source_sha256'],
                'provenance':{'scope':'development400','partition':expected_partition,
                    'evidence_class':'finite-independent-frozen-replay',
                    'finite_replay_report_sha256':source['report_sha256'],
                    'declared_entrypoint':'solve','unresolved_bindings':list(MISSING_BINDINGS)},
            }
            pending += 1
        else:
            if row.get('current_dot_qualification') is not False or not hash_value(row.get('authored_source_sha256')):
                raise ValueError('inconsistent blocked source evidence')
            is_compat = row.get('reference_compatibility_only') is True
            compatible += is_compat
            implementation = {
                'status':'blocked',
                'reason':'Extra-contract reference compatibility only; normative domain unresolved.' if is_compat else 'Authored source has unresolved domain/qualification gap; no normative answer admission.',
                'source_sha256':row['authored_source_sha256'],
                'provenance':{'scope':'development400','partition':expected_partition,
                    'evidence_class':'reference-compatibility-metadata' if is_compat else 'authored-unqualified',
                    'unresolved_bindings':list(MISSING_BINDINGS)},
            }
            blocked += 1
        problems.append({'problem_id':'development400:'+str(pid),'implementations':{
            'python':implementation,
            'javascript':{'status':'missing','reason':'JavaScript evidence not imported by this Python-only adapter; not a claim of global absence.'},
        }})
    catalogue = {'schema':'gamma.dual-language-catalogue.v1','universe_sha256':digest(universe),'problems':problems}
    result = validate(universe,catalogue,{})
    summary = {'schema':'gamma.python-development-pending-import.v1',
               'scope':'development400-only, not full corpus','authored_pending':pending,
               'blocked':blocked,'compatibility_only':compatible,'qualified':0,
               'missing_bindings':list(MISSING_BINDINGS),'validation':result,
               'case_payload_reads':0,'source_payload_reads':0,'protected_payload_reads':0}
    return universe,catalogue,summary


def main():
    p=argparse.ArgumentParser()
    for name in ('reconciliation','transfer-receipt','filtered-metadata','output'):
        p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args()
    values=adapt_development(json.loads(a.reconciliation.read_bytes()),json.loads(a.transfer_receipt.read_bytes()),a.filtered_metadata.read_bytes())
    a.output.mkdir(parents=True,exist_ok=False)
    for name,value in zip(('universe.json','catalogue.json','summary.json'),values):
        (a.output/name).write_text(json.dumps(value,sort_keys=True,indent=2)+'\n')
    print(json.dumps(values[-1],sort_keys=True))

if __name__=='__main__':main()
