"""Pinned fitting selection over existing admission and authoring owners.

Operator-approved fitting policy is an external trust input. Source acquisition,
qualification and fitting membership remain separate; unknown joins fail closed.
No source locator in an authoring/provenance record is followed.
"""
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))
from projects.algorithm_solver.algsolve import authoring_variants as owner
from projects.algorithm_solver.catalogue.catalogue import BINDINGS, hash_value
from projects.algorithm_solver.catalogue.guide_admission import reconcile_development_replay
from projects.algorithm_solver.catalogue.known_spec_service import (
    KnownSpecService, _boundary_snapshot, _strict_spec,
)

MAX_VARIANTS = 4096
MAX_SOURCE_BYTES = 32 * 1024**2


def require(condition, message):
    if not condition:
        raise ValueError(message)


def fields(value, names):
    require(isinstance(value, dict) and set(value) == set(names), 'unexpected fitting fields')


def load_development_replay(config, config_sha256):
    """Historical exact JS fitting needs no newly invented authoring ledger."""
    fields(config, ('schema', 'language', 'service', 'source_contract', 'qualification_contract'))
    require(config['language'] == 'javascript', 'historical contract authorizes exact JavaScript sources only')
    service_config, source_contract, qualification = (
        _strict_spec(config[k]) for k in ('service', 'source_contract', 'qualification_contract'))
    service = KnownSpecService.from_config(config['service']['path'], config['service']['sha256'])
    gate = _strict_spec(service_config['source_access']['boundary_gate'])
    boundary = _boundary_snapshot(gate)
    aliases = _strict_spec(service_config['source_access']['aliases'])
    key_aliases = _strict_spec({'path': gate['artifact_paths']['identity_aliases'],
                                'sha256': gate['trusted_hashes']['identity_aliases']})
    catalogue = _strict_spec(service_config['catalogue'])
    joined = reconcile_development_replay(catalogue, aliases, key_aliases, source_contract,
        qualification, config['source_contract']['sha256'], boundary)
    selected = [row for row in joined['problems'] if row['implementations']['javascript']['eligible']]
    require(0 < len(selected) <= MAX_VARIANTS, 'no bounded eligible historical replay population')
    # Complete metadata selection precedes every source open. KnownSpecService
    # repeats the live source gate, hash and current receipt checks on each read.
    sources, memberships, size = {}, [], 0
    for row in selected:
        gid = row['problem_id']; slot = row['implementations']['javascript']
        require(gid in service_config['source_access']['authorized_problem_ids'], 'outside service source grant')
        boundary.authorize(gid, language='javascript', payload_kind='source')
    for row in selected:
        gid = row['problem_id']; slot = row['implementations']['javascript']
        value = service.request(gid, language='javascript', include_source=True)
        artifact = value.get('artifact', {}); text = artifact.get('source_utf8')
        require(artifact.get('status') == 'materialized' and isinstance(text, str) and text.strip() and
                owner.sha(text.encode()) == artifact.get('source_sha256') == slot['bindings']['source_sha256'],
                'guarded historical exact source bytes unavailable')
        size += len(text.encode()); require(size <= MAX_SOURCE_BYTES, 'fitting source byte budget exceeded')
        sources[int(gid.split(':')[1])] = {slot['canonical_variant_id']: text}
        memberships.append({'problem_id': gid, 'membership': row['historical_membership'],
            'canonical_group_members': row['canonical_group_members'], 'canonical_variant_id': slot['canonical_variant_id'],
            'source_sha256': slot['bindings']['source_sha256'],
            'problem_contract_sha256': slot['bindings']['problem_contract_sha256'],
            'receipt_sha256': slot['receipt_sha256'], 'sidecar_semantics_sha256': None})
    return sources, {'schema': 'gamma.idiom-development-replay-inputs.v1', 'language': 'javascript',
        'config_sha256': config_sha256, 'inputs': {k + '_sha256': config[k]['sha256']
            for k in ('service', 'source_contract', 'qualification_contract')},
        'problem_count': len(sources), 'source_count': len(sources), 'source_bytes': size,
        'memberships': memberships, 'historical_join': joined, 'source_rewrites': 0, 'candidate_executions': 0,
        'qualification_created': False, 'corpus_admission_created': False,
        'browser_admission_created': False, 'publication_authorized': False,
        'fresh_confirmation_created': False, 'unseen_generalization_evaluated': False}


def load_fitting_inputs(config_path, config_sha256):
    """Preflight EVERY selected metadata row before any guarded source request."""
    config = _strict_spec({'path': str(config_path), 'sha256': config_sha256})
    if config.get('schema') == 'gamma.idiom-development-replay-config.v1':
        return load_development_replay(config, config_sha256)
    fields(config, ('schema', 'language', 'service', 'admission', 'authoring_catalog', 'fitting_policy'))
    require(config['schema'] == 'gamma.idiom-fitting-config.v1' and
            config['language'] in ('javascript', 'python'), 'explicit fitting schema and language required')
    language = config['language']
    service_config, admission, catalog, policy = (
        _strict_spec(config[name]) for name in ('service', 'admission', 'authoring_catalog', 'fitting_policy'))
    require(admission.get('schema') == 'gamma.source-to-guide-inventory.v1' and
            admission.get('inputs', {}).get('service_sha256') == config['service']['sha256'],
            'admission must bind this exact service')
    require(catalog.get('schema') == 'gamma.authoring-variant-catalog-pilot.v1' and
            isinstance(catalog.get('variants'), list), 'existing authoring variant catalogue required')
    fields(policy, ('schema', 'authority', 'reference', 'purpose', 'inputs', 'variants'))
    require(policy['schema'] == 'gamma.idiom-fitting-policy.v1' and
            policy['purpose'] == 'development-fitting' and
            all(isinstance(policy[k], str) and policy[k].strip() for k in ('authority', 'reference')),
            'externally reviewed fitting authority/reference required')
    require(policy['inputs'] == {name + '_sha256': config[name]['sha256']
                                for name in ('service', 'admission', 'authoring_catalog')},
            'fitting policy input pins differ')
    require(isinstance(policy['variants'], list) and 0 < len(policy['variants']) <= MAX_VARIANTS,
            'bounded nonempty fitting population required')
    service = KnownSpecService.from_config(config['service']['path'], config['service']['sha256'])
    boundary = _boundary_snapshot(_strict_spec(service_config['source_access']['boundary_gate']))
    canonical = _strict_spec(service_config['catalogue'])
    canonical = {row['problem_id']: row for row in canonical['problems']}
    problems = admission.get('problems')
    require(isinstance(problems, list), 'admission problem records required')
    by_id = {row['problem_id']: row for row in problems}
    require(len(by_id) == len(problems) and set(by_id) == set(canonical),
            'admission must preserve the complete canonical population')
    ids = [record.get('variant_id') for record in catalog['variants']]
    require(all(hash_value(v) for v in ids) and len(ids) == len(set(ids)),
            'invalid or duplicated authoring identities')
    selected, seen, byte_variants = [], set(), set()
    for selection in policy['variants']:
        fields(selection, ('problem_id', 'language', 'variant_id', 'membership', 'group_id'))
        pid = selection['problem_id']
        require(type(pid) is int and pid > 0 and selection['language'] == language and
                hash_value(selection['variant_id']), 'exact selected identity/language required')
        gid = 'leetcode:' + str(pid)
        require(gid in by_id, 'selected identity outside admission')
        problem = by_id[gid]
        # Boundary authorization is metadata-only here; KnownSpecService repeats
        # its live per-open gate immediately before the actual source read.
        boundary.authorize(gid, language=language, payload_kind='source')
        require(gid in service_config['source_access']['authorized_problem_ids'] and
                problem.get('permission') == 'source_access_authorized' and
                problem.get('permission_binding') == {
                    'policy_sha256': boundary.policy_sha256, 'proof_sha256': boundary.proof_sha256},
                'exact source permission binding required')
        require(selection['membership'] == problem.get('split') == 'development_fit' and
                problem.get('exposure', {}).get('status') == 'previously_exposed',
                'explicit already-exposed development_fit membership required')
        grouping = problem.get('grouping', {})
        require(isinstance(selection['group_id'], str) and selection['group_id'].strip() and
                grouping.get('group_id') == selection['group_id'] and
                grouping.get('problem_and_languages_together') is True and
                grouping.get('near_duplicate_closure') == 'reviewed',
                'reviewed grouping and preserved group membership required')
        group = [row for row in problems if row.get('grouping', {}).get('group_id') == selection['group_id']]
        require(all(row.get('split') == 'development_fit' and
                    row.get('exposure', {}).get('status') == 'previously_exposed' and
                    row.get('permission') == 'source_access_authorized' and
                    row.get('grouping', {}).get('problem_and_languages_together') is True and
                    row.get('grouping', {}).get('near_duplicate_closure') == 'reviewed' for row in group),
                'fitting group crosses heldout, unknown or closed membership')
        matches = [record for record in owner.query(catalog, pid, language)
                   if record['variant_id'] == selection['variant_id']]
        require(len(matches) == 1, 'selected variant not in existing authoring owner')
        record = matches[0]
        identity = {key: record.get(key) for key in ('problem_id', 'language', 'source_sha256',
                                                   'semantics_sha256', 'problem_contract_sha256')}
        require(all(hash_value(identity[k]) for k in ('source_sha256', 'semantics_sha256', 'problem_contract_sha256')) and
                owner.sha(owner.canonical(identity).encode()) == record['variant_id'] and
                record.get('qualification', {}).get('status') == 'unknown',
                'invalid or reclassified authoring identity')
        slot = problem['implementations'][language]
        impl = canonical[gid]['implementations'][language]
        stage = admission.get('development_admission')
        if stage is not None:
            require(stage.get('schema') == 'gamma.exact-development-source-admission.v1' and
                    stage.get('qualification_created') is False and
                    stage.get('browser_guides_admitted') == 0 and
                    stage.get('inputs', {}).get('service') == config['service'],
                    'exact development admission stage required')
            adapter = slot.get('development_adapter') or {}
            license_record = (slot.get('development_license') or {}).get('verified_reference', {})
            development_complete = (slot.get('development_blockers') == [] and
                license_record.get('bindings') == slot['bindings'] and
                adapter.get('kind') == 'existing_qualified_solve_interface' and
                adapter.get('language') == language and
                adapter.get('interface_sha256') == impl['interface_sha256'] and
                adapter.get('qualified_runtime_sha256') == impl['runtime_sha256'])
        else:
            development_complete = (slot.get('blockers') == [] and
                                    slot.get('license') is not None and slot.get('adapter') is not None)
        require(slot.get('development_corpus_admitted') is True and development_complete,
                'completed source-to-guide development admission required; metadata joins alone are insufficient')
        require(impl['status'] == 'qualified' and
                slot.get('qualification', {}).get('receipt_binding_checked') is True and
                slot['qualification'].get('receipt_sha256') == impl['receipt_sha256'] and
                slot.get('bindings') == {k: impl[k] for k in BINDINGS} and
                record['source_sha256'] == impl['source_sha256'] and
                record['problem_contract_sha256'] == impl['problem_contract_sha256'],
                'exact existing canonical qualification join required')
        key = (pid, record['source_sha256'])
        require(record['variant_id'] not in seen and key not in byte_variants,
                'duplicate selected variant or source bytes')
        seen.add(record['variant_id']); byte_variants.add(key)
        selected.append((selection, record))
    sources, memberships, total_bytes = {}, [], 0
    for selection, record in selected:
        pid = selection['problem_id']
        value = service.request('leetcode:' + str(pid), language=language, include_source=True)
        artifact = value.get('artifact', {})
        text = artifact.get('source_utf8')
        require(artifact.get('status') == 'materialized' and isinstance(text, str) and text.strip() and
                owner.sha(text.encode()) == artifact.get('source_sha256') == record['source_sha256'],
                'guarded exact source bytes unavailable')
        total_bytes += len(text.encode())
        require(total_bytes <= MAX_SOURCE_BYTES, 'fitting source byte budget exceeded')
        sources.setdefault(pid, {})[record['variant_id']] = text
        memberships.append(dict(selection, source_sha256=record['source_sha256'],
                                semantics_sha256=record['semantics_sha256'],
                                problem_contract_sha256=record['problem_contract_sha256']))
    return sources, {'schema': 'gamma.idiom-fitting-inputs.v1', 'language': language,
        'config_sha256': config_sha256,
        'inputs': {name + '_sha256': config[name]['sha256'] for name in
                   ('service', 'admission', 'authoring_catalog', 'fitting_policy')},
        'problem_count': len(sources), 'source_count': len(selected), 'source_bytes': total_bytes,
        'memberships': memberships, 'source_rewrites': 0, 'candidate_executions': 0,
        'qualification_created': False, 'corpus_admission_created': False,
        'browser_admission_created': False, 'publication_authorized': False}
