"""Metadata-only source-to-guide queue; never admits, executes, or splits sources.

The operator supplies pinned catalogue/receipt/access inputs. Imported source
references are observations, not qualification or permission. Unknown exposure
and grouping remain unknown: this inventory cannot manufacture a fresh holdout.
"""
import argparse
from collections import Counter
import copy
import json
from pathlib import Path
import re

from .boundary_policy import validate_policy
from .catalogue import BINDINGS, LANGUAGES, digest, hash_value, validate
from .public_batch_adapter import bounded_regular_read, pinned, sha
from ..algsolve import authoring_variants


def project(universe, catalogue, receipts, policy, aliases, census, exposure):
    validation = validate(universe, catalogue, receipts)
    ids = set(universe['eligible_problem_ids'])
    if (ids != policy.authorized | policy.protected | policy.unknown or
            set(universe['protected_problem_ids']) != policy.protected):
        raise ValueError('catalogue and permission universe disagree')
    if any(pid not in ids for pid in aliases.values()) or not set(exposure) <= ids:
        raise ValueError('alias or exposure outside universe')
    observations = {}
    for row in census['problems']:
        pid = row['global_id']
        if pid not in ids or pid in observations:
            raise ValueError('duplicate or unknown census identity')
        observations[pid] = row
    if set(observations) != ids:
        raise ValueError('census must preserve the complete denominator')
    by_id = {row['problem_id']: row for row in catalogue['problems']}
    alias_groups = {pid: [] for pid in ids}
    for alias, pid in aliases.items():
        alias_groups[pid].append(alias)
    problems = []
    for pid in sorted(ids):
        permission = ('protected' if pid in policy.protected else
                      'source_access_authorized' if pid in policy.authorized else 'unresolved')
        slots = {}
        for language in LANGUAGES:
            impl = by_id[pid]['implementations'][language]
            observed = observations[pid]['implementations'][language]
            qualified = impl['status'] == 'qualified'
            blockers = []
            if permission != 'source_access_authorized':
                blockers.append('protected' if permission == 'protected' else 'permission_unresolved')
            if not qualified:
                blockers.append('qualification_not_established')
            # A bound hash is not a current byte check, browser adapter or license.
            blockers.extend(['source_bytes_not_rechecked', 'license_record_not_joined',
                             'browser_adapter_acceptance_not_joined',
                             'determinism_and_host_api_review_not_joined'])
            slots[language] = {
                'canonical_variant_id': impl.get('canonical_variant_id'),
                'bindings': {key: impl.get(key) for key in BINDINGS},
                'qualification': {
                    'status': impl['status'], 'reason': impl.get('reason'),
                    'receipt_sha256': impl.get('receipt_sha256'),
                    'receipt_binding_checked': qualified,
                    'evidence_class': impl.get('evidence_class'),
                    'contract_scope': impl.get('contract_scope'),
                    'caveats': impl.get('caveats', []),
                    'judge_reexecuted': False,
                },
                'interface': impl.get('interface'),
                'provenance_sha256': digest(impl['provenance']) if qualified else None,
                'source_observation': {
                    'availability': observed['availability'],
                    'references': observed['evidence'],
                    'confers_permission_or_qualification': False,
                },
                'adapter': None, 'license': None,
                'encoding': {'status': 'not_joined'},
                'publication': {'status': 'not_joined'},
                'blockers': blockers,
                'development_corpus_admitted': False,
                'browser_guide_admitted': False,
            }
        problems.append({
            'problem_id': pid, 'aliases': sorted(alias_groups[pid]),
            'permission': permission,
            'permission_binding': {'policy_sha256': policy.policy_sha256,
                                   'proof_sha256': policy.proof_sha256},
            'exposure': {'status': 'previously_exposed' if pid in exposure else 'unknown',
                         'records': exposure.get(pid, []), 'freshness_established': False},
            'grouping': {'problem_and_languages_together': True,
                         'near_duplicate_closure': 'not_reviewed'},
            'stratification': {'family': None, 'difficulty': None, 'import_batch': None},
            'split': None, 'implementations': slots,
        })
    reasons = Counter(reason for row in problems for slot in row['implementations'].values()
                      for reason in slot['blockers'])
    summary = {
        'problems': len(problems), 'language_slots': len(problems) * len(LANGUAGES),
        'permissions': dict(Counter(row['permission'] for row in problems)),
        'exposure': dict(Counter(row['exposure']['status'] for row in problems)),
        'catalogue': validation, 'slot_blockers': dict(sorted(reasons.items())),
        'development_corpus_admitted': 0, 'browser_guides_admitted': 0,
        'source_payload_reads': 0, 'case_payload_reads': 0, 'candidate_executions': 0,
        'split_frozen': False, 'fresh_confirmation_created': False,
        'remaining': ['Join source/license/adapter and host-API evidence for permitted slots.',
                      'Resolve family/difficulty/batch metadata and near-duplicate closure.',
                      'Extend exposure records; unknown never means fresh.',
                      'Only then freeze the permitted corpus and assign grouped splits.'],
    }
    return {'schema': 'gamma.source-to-guide-inventory.v1', 'summary': summary,
            'problems': problems}


def reconcile_source_evidence(result, *, authoring_catalog=None, source_evidence=(), historical_guides=()):
    """Join supplied metadata by exact identity; never upgrade authoring records.

    Authoring identities remain owned by authoring_variants. Evidence documents
    are retained verbatim, not interpreted as new qualification or legal grants.
    A successful hash join establishes applicability, not acceptance. Historical
    guide sources remain separate even when the canonical problem is qualified.
    This function follows no source, evidence or provenance path.
    """
    if 'source_evidence_reconciliation' in result['summary']:
        raise ValueError('reconcile a new inventory snapshot, not a previously joined one')
    result = copy.deepcopy(result)
    if authoring_catalog is not None and (
            not isinstance(authoring_catalog, dict) or
            authoring_catalog.get('schema') != 'gamma.authoring-variant-catalog-pilot.v1' or
            not isinstance(authoring_catalog.get('variants'), list)):
        raise ValueError('existing authoring variant catalogue required')
    if authoring_catalog is not None:
        records = authoring_catalog['variants']
        if any(not isinstance(record, dict) or type(record.get('problem_id')) is not int or
               record['problem_id'] < 1 or record.get('language') not in LANGUAGES or
               not isinstance(record.get('qualification'), dict) for record in records):
            raise ValueError('invalid authoring record identity')
        variant_ids = [record.get('variant_id') for record in records]
        if any(not hash_value(value) for value in variant_ids) or len(variant_ids) != len(set(variant_ids)):
            raise ValueError('invalid or duplicate authoring variant identity')
    if not isinstance(source_evidence, (list, tuple)) or not isinstance(historical_guides, (list, tuple)):
        raise ValueError('explicit evidence and historical guide lists required')
    slots = {(row['problem_id'], language): (row, slot)
             for row in result['problems'] for language, slot in row['implementations'].items()}
    kinds = {'license': ('license', 'license_record_not_joined', 'license_acceptance_not_established'),
             'browser_adapter': ('adapter', 'browser_adapter_acceptance_not_joined', 'browser_adapter_acceptance_not_established'),
             'host_api': ('host_api', 'determinism_and_host_api_review_not_joined', 'determinism_and_host_api_acceptance_not_established')}
    for (pid, language), (problem, slot) in slots.items():
        matches = ()
        if authoring_catalog is not None and re.fullmatch(r'leetcode:[1-9][0-9]*', pid, re.ASCII):
            matches = authoring_variants.query(authoring_catalog, int(pid.split(':')[1]), language)
        joined = []
        for record in matches:
            identity = {key: record.get(key) for key in ('problem_id', 'language', 'source_sha256',
                                                       'semantics_sha256', 'problem_contract_sha256')}
            if (any(not hash_value(identity[key]) for key in ('source_sha256', 'semantics_sha256', 'problem_contract_sha256')) or
                    record.get('variant_id') != authoring_variants.sha(authoring_variants.canonical(identity).encode()) or
                    record.get('qualification', {}).get('status') != 'unknown'):
                raise ValueError('invalid or reclassified authoring record')
            same_source = record['source_sha256'] == slot['bindings']['source_sha256']
            same_contract = record['problem_contract_sha256'] == slot['bindings']['problem_contract_sha256']
            bound = same_source and same_contract and slot['qualification']['receipt_binding_checked']
            joined.append({'record': copy.deepcopy(record),
                           'canonical_source_match': same_source, 'canonical_contract_match': same_contract,
                           'canonical_qualification_receipt_sha256': slot['qualification']['receipt_sha256'] if bound else None,
                           'qualification_join': 'exact_existing_canonical_receipt' if bound else 'not_joined',
                           'confers_permission_or_admission': False})
        slot['authoring_variants'] = {'status': 'queried' if authoring_catalog is not None else 'not_supplied',
                                     'records': joined, 'exhaustive_inventory': False}
        slot['historical_guides'] = []
        slot['historical_guide_inventory_complete'] = False
        slot['source_evidence_joins'] = []

    counts = Counter()
    seen = set()
    for record in source_evidence:
        if (not isinstance(record, dict) or
                set(record) != {'problem_id', 'language', 'kind', 'bindings', 'evidence'} or
                not isinstance(record.get('problem_id'), str) or record.get('language') not in LANGUAGES or
                record.get('kind') not in kinds or
                not isinstance(record.get('bindings'), dict) or set(record['bindings']) != set(BINDINGS) or
                any(not hash_value(record['bindings'][key]) for key in BINDINGS) or
                not isinstance(record.get('evidence'), dict) or not record['evidence']):
            raise ValueError('source-specific evidence with complete exact bindings required')
        key = (record['problem_id'], record['language'])
        if key not in slots:
            raise ValueError('source evidence outside inventory')
        identity = digest(record)
        if identity in seen:
            raise ValueError('duplicate source evidence')
        seen.add(identity)
        problem, slot = slots[key]
        mismatch = [field for field in BINDINGS if record['bindings'][field] != slot['bindings'][field]]
        reason = ('permission_not_authorized' if problem['permission'] != 'source_access_authorized' else
                  'qualification_not_established' if not slot['qualification']['receipt_binding_checked'] else
                  'canonical_binding_mismatch' if mismatch else None)
        join = {'kind': record['kind'], 'record_sha256': identity,
                'status': 'not_joined' if reason else 'exact_binding_joined', 'reason': reason,
                'mismatching_bindings': mismatch, 'record': copy.deepcopy(record),
                'acceptance_evaluated': False, 'confers_permission_or_qualification': False}
        slot['source_evidence_joins'].append(join)
        counts[join['status']] += 1
        if reason is None:
            field, old_blocker, next_blocker = kinds[record['kind']]
            if slot.get(field) is None:
                slot[field] = {'status': 'exact_binding_joined', 'record_sha256': [], 'acceptance_evaluated': False}
            slot[field]['record_sha256'].append(identity)
            if old_blocker in slot['blockers']:
                slot['blockers'].remove(old_blocker)
            if next_blocker not in slot['blockers']:
                slot['blockers'].append(next_blocker)

    seen = set()
    for guide in historical_guides:
        if (not isinstance(guide, dict) or
                set(guide) != {'problem_id', 'language', 'source_sha256', 'profile_id', 'evidence'} or
                not isinstance(guide.get('problem_id'), str) or guide.get('language') not in LANGUAGES or
                not hash_value(guide.get('source_sha256')) or
                not isinstance(guide.get('profile_id'), str) or not guide['profile_id'] or
                not isinstance(guide.get('evidence'), dict)):
            raise ValueError('exact historical guide metadata required')
        key = (guide['problem_id'], guide['language'])
        if key not in slots or digest(guide) in seen:
            raise ValueError('duplicate or unknown historical guide')
        seen.add(digest(guide))
        slot = slots[key][1]
        slot['historical_guides'].append({'record': copy.deepcopy(guide),
            'canonical_source_match': guide['source_sha256'] == slot['bindings']['source_sha256'],
            'qualification_join': 'not_joined', 'historical_evidence_retained': True,
            'canonical_evidence_transplanted': False})
    result['summary']['source_evidence_reconciliation'] = {
        'authoring_catalog_supplied': authoring_catalog is not None,
        'authoring_records': sum(len(slot['authoring_variants']['records']) for _, slot in slots.values()),
        'historical_guides': len(historical_guides), 'evidence_records': len(source_evidence),
        **dict(sorted(counts.items())), 'qualification_created': False, 'admission_performed': False}
    result['summary']['slot_blockers'] = dict(sorted(Counter(
        reason for _, slot in slots.values() for reason in slot['blockers']).items()))
    return result


def build(config, *, verify_sources=False):
    """Follow only explicit pinned metadata descriptors, never source references."""
    if (not {'service', 'source_census'} <= set(config) or
            set(config) - {'service', 'source_census', 'authoring_catalog', 'source_evidence', 'historical_guides'}):
        raise ValueError('unexpected inventory configuration fields')
    service = pinned(config['service'])[0]
    if service.get('schema') != 'gamma.known-spec-service.v2':
        raise ValueError('pinned service v2 required')
    inputs = {name: pinned(service[name])[0]
              for name in ('universe', 'catalogue', 'verified_receipts')}
    gate = pinned(service['source_access']['boundary_gate'])[0]
    raw = {name: bounded_regular_read(path, maximum_bytes=8*1024**2)
           for name, path in gate['artifact_paths'].items()}
    policy = validate_policy(raw, gate['trusted_hashes'])
    aliases = json.loads(raw['identity_aliases'])['by_key']
    # This existing map records historical development membership, not freshness.
    historic = pinned(service['source_access']['aliases'])[0]
    exposure = {pid: [{'kind': 'historical_development_membership', 'alias': alias,
                      'artifact_sha256': service['source_access']['aliases']['sha256']}]
                for alias, pid in historic['aliases'].items()}
    census = pinned(config['source_census'])[0]
    result = project(inputs['universe'], inputs['catalogue'], inputs['verified_receipts'],
                     policy, aliases, census, exposure)
    result['inputs'] = {'service_sha256': config['service']['sha256'],
                       'source_census_sha256': config['source_census']['sha256'],
                       'catalogue_sha256': service['catalogue']['sha256'],
                       'receipts_sha256': service['verified_receipts']['sha256'],
                       'boundary_gate_sha256': service['source_access']['boundary_gate']['sha256'],
                       'historical_exposure_sha256': service['source_access']['aliases']['sha256']}
    result['inputs']['code_sha256'] = {
        name: sha((Path(__file__).parent/name).read_bytes()) for name in
        ('guide_admission.py', 'catalogue.py', 'boundary_policy.py', 'public_batch_adapter.py',
         'known_spec_service.py', 'materialize.py', 'retrieval.py')}
    joins = {}
    for name in ('authoring_catalog', 'source_evidence', 'historical_guides'):
        if name in config:
            joins[name] = pinned(config[name])[0]
            result['inputs'][name + '_sha256'] = config[name]['sha256']
    if joins:
        result = reconcile_source_evidence(result, **joins)
        result['inputs']['code_sha256']['authoring_variants.py'] = sha(Path(authoring_variants.__file__).read_bytes())
    if verify_sources:
        from .known_spec_service import KnownSpecService
        verify_source_bindings(result, KnownSpecService(service))
    return result


def verify_source_bindings(result, service):
    """Use the existing identity-bound pre-open gate; no execution or AST mining."""
    attempts = 0
    outcomes = Counter()
    for problem in result['problems']:
        if problem['permission'] != 'source_access_authorized':
            continue
        for language, slot in problem['implementations'].items():
            if not slot['qualification']['receipt_binding_checked']:
                continue
            attempts += 1
            value = service.request(problem['problem_id'], language=language, include_source=True)
            artifact = value.get('artifact', {})
            if (artifact.get('status') == 'materialized' and
                    artifact.get('source_sha256') == slot['bindings']['source_sha256'] and
                    sha(artifact['source_utf8'].encode()) == slot['bindings']['source_sha256']):
                status = 'exact_bound_bytes_verified'
                slot['blockers'].remove('source_bytes_not_rechecked')
            else:
                status = 'source_binding_unavailable'
            slot['source_verification'] = {'status': status, 'reason': value.get('reason'),
                                           'executed': False}
            outcomes[status] += 1
    result['summary'].update(
        guarded_source_requests=attempts, source_verification=dict(outcomes),
        # A failed materialization may read bytes before rejecting a stale hash.
        source_payload_reads=attempts if outcomes.get('source_binding_unavailable', 0) == 0 else None,
        source_payload_read_upper_bound=attempts,
        slot_blockers=dict(sorted(Counter(reason for row in result['problems']
            for slot in row['implementations'].values() for reason in slot['blockers']).items())))


def save_snapshot(directory, result):
    """Private one-shot snapshot, detached hashes; refuses overwrite."""
    directory = Path(directory)
    directory.mkdir(mode=0o700, parents=False, exist_ok=False)
    hashes = {}
    for name, value in [('queue.json', result),
                        ('summary.json', {'schema': result['schema'], 'inputs': result.get('inputs', {}),
                                          **result['summary']})]:
        raw = (json.dumps(value, sort_keys=True, indent=2, allow_nan=False)+'\n').encode()
        with (directory/name).open('xb') as stream:
            stream.write(raw)
        hashes[name] = sha(raw)
    (directory/'SHA256SUMS').write_text(''.join(f'{value}  {name}\n' for name, value in hashes.items()))
    return hashes


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', required=True, type=Path)
    parser.add_argument('--config-sha256', required=True)
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--verify-sources', action='store_true',
                        help='Hash-check only permitted qualified sources through the existing service gate.')
    args = parser.parse_args()
    config = pinned({'path': str(args.config.resolve()), 'sha256': args.config_sha256})[0]
    result = build(config, verify_sources=args.verify_sources)
    print(json.dumps({'summary': result['summary'], 'sha256': save_snapshot(args.output, result)}, indent=2))


if __name__ == '__main__':
    main()
