"""Read-only authoring-variant catalog. Not a qualification or admission ledger."""
import argparse
import hashlib
import json
from pathlib import Path
import re


def sha(data):
    return hashlib.sha256(data).hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False)


def read_pinned(root, relative, expected):
    p = Path(relative)
    if p.is_absolute() or '..' in p.parts:
        raise ValueError('Unsafe path')
    target = root / p
    if target.is_symlink() or not target.resolve().is_relative_to(root.resolve()):
        raise ValueError('Path escapes input root')
    data = target.read_bytes()
    if sha(data) != expected:
        raise ValueError('Hash mismatch: ' + relative)
    return data


def build(manifests):
    variants = {}
    problem_contracts = {}
    for manifest in map(Path, manifests):
        root = manifest.parent
        raw = manifest.read_bytes()
        m = json.loads(raw)
        packet_bytes = read_pinned(root, 'assignment.public-safe.json', m['assignment_sha256'])
        packet = json.loads(packet_bytes)
        problems = {}
        for problem in packet['problems']:
            pid = problem['id']
            if type(pid) is not int or pid <= 0 or pid in problems:
                raise ValueError('Invalid or duplicate packet problem ID')
            problems[pid] = problem
        files = {}
        for item in m['files']:
            if item['path'] in files:
                raise ValueError('Duplicate manifest file path')
            files[item['path']] = item['sha256']
        if not m['source_inventory']:
            raise ValueError('Empty source inventory')
        for row in m['source_inventory']:
            pid, language = row['id'], row['language']
            if type(pid) is not int or pid not in problems or language not in ('javascript', 'python'):
                raise ValueError('Invalid source identity')
            path = Path(row['path'])
            suffix = '.js' if language == 'javascript' else '.py'
            if path.suffix != suffix or not path.stem.isascii() or not path.stem.isdecimal() or int(path.stem) != pid:
                raise ValueError('Source filename/identity mismatch')
            if files.get(row['path']) != row['sha256']:
                raise ValueError('Source reference mismatch')
            read_pinned(root, row['path'], row['sha256'])
            sem_path = row.get('semantics_path', str(path.with_suffix('.semantics.json')))
            sem_hash = row.get('semantics_sha256', files.get(sem_path))
            if not sem_hash or files.get(sem_path) != sem_hash:
                raise ValueError('Contract reference mismatch')
            json.loads(read_pinned(root, sem_path, sem_hash))
            problem = problems[pid]
            # Explicit public behavioral contract; full packet remains hash-linked.
            required = ('external_interface', 'statement_constraints_snapshot', 'return_domain')
            contract = {key: problem[key] for key in required}
            optional = ('objective_summary', 'domain_facts', 'comparison',
                        'mutation_alias_contract', 'numeric_complexity_contract',
                        'mutation_alias_review', 'public_fixed_constant')
            contract.update({key: problem[key] for key in optional if key in problem})
            contract_hash = sha(canonical(contract).encode())
            if pid in problem_contracts and problem_contracts[pid] != contract_hash:
                raise ValueError('Problem contract mismatch across inputs')
            problem_contracts[pid] = contract_hash
            identity = {'problem_id': pid, 'language': language, 'source_sha256': row['sha256'],
                        'semantics_sha256': sem_hash, 'problem_contract_sha256': contract_hash}
            variant_id = sha(canonical(identity).encode())
            provenance = {'manifest_sha256': sha(raw), 'assignment_sha256': sha(packet_bytes),
                          'source_path': row['path'], 'semantics_path': sem_path}
            record = variants.setdefault(variant_id, dict(identity, variant_id=variant_id,
                        qualification={'status': 'unknown', 'reason': 'Authoring artifacts are not qualification receipts'},
                        provenance=[]))
            if provenance not in record['provenance']:
                record['provenance'].append(provenance)
    records = sorted(variants.values(), key=lambda r: (r['problem_id'], r['language'], r['variant_id']))
    index = {}
    for record in records:
        record['provenance'].sort(key=canonical)
        index.setdefault(str(record['problem_id']), {}).setdefault(record['language'], []).append(record['variant_id'])
    return {'schema': 'gamma.authoring-variant-catalog-pilot.v1', 'preferred_variant': None,
            'qualification_policy': 'Unknown only. This pilot accepts no qualification receipts and confers no admission.',
            'unique_problem_count': len(index), 'variant_count': len(records), 'index': index, 'variants': records}


def query(catalog, problem_id, language):
    """Return all matches, never select or rank a preferred implementation."""
    return tuple(record for record in catalog['variants']
                 if record['problem_id'] == problem_id and record['language'] == language)


def from_canonical_contracts(raw, expected_sha256):
    """Index existing canonical source/contract pairs without inventing sidecars.

    A complete, hash-matching qualification contract can supply the semantic
    artifact for an unchanged canonical source. It is explicitly identified as
    that artifact, never relabeled as a source-author's algorithm sidecar. The
    original canonical ID is retained in provenance. Registry status stays
    unknown; receipt validation and admission remain outside this owner.
    Missing historical contract payloads remain unresolved.
    """
    if len(raw) > 32 * 1024**2 or sha(raw) != expected_sha256:
        raise ValueError('Pinned bounded canonical metadata required')
    metadata = json.loads(raw)
    records, unresolved, seen = [], [], set()
    kinds = ('public_batch', 'admitted_qualification', 'fresh_qualification', 'public_foundation')
    valid_hash = lambda value: isinstance(value, str) and re.fullmatch(r'[0-9a-f]{64}', value)
    for row in metadata['problems']:
        gid = row['problem_id']
        if not isinstance(gid, str) or not re.fullmatch(r'leetcode:[1-9][0-9]*', gid) or gid in seen:
            raise ValueError('Unique canonical problem identities required')
        seen.add(gid)
        for language in ('javascript', 'python'):
            implementation = row['implementations'][language]
            if implementation.get('status') != 'qualified':
                continue
            payloads = [(kind, implementation.get('provenance', {}).get(kind, {}).get('problem_contract'))
                        for kind in kinds]
            payloads = [(kind, payload) for kind, payload in payloads if payload is not None]
            if not payloads:
                unresolved.append({'problem_id': gid, 'language': language,
                                   'reason': 'complete_canonical_contract_payload_unavailable'})
                continue
            if len(payloads) != 1:
                raise ValueError('Ambiguous canonical contract payload')
            kind, payload = payloads[0]
            # Match the canonical catalogue's JSON hash convention exactly.
            contract_hash = sha(json.dumps(payload, sort_keys=True, separators=(',', ':'),
                                           allow_nan=False).encode())
            if (not isinstance(payload, dict) or not payload or
                    contract_hash != implementation.get('problem_contract_sha256') or
                    not valid_hash(implementation.get('source_sha256')) or
                    not valid_hash(implementation.get('receipt_sha256')) or
                    implementation.get('canonical_variant_id') != language + ':' + implementation['source_sha256']):
                raise ValueError('Exact canonical source and complete semantic contract required')
            identity = {'problem_id': int(gid.split(':')[1]), 'language': language,
                        'source_sha256': implementation['source_sha256'],
                        'semantics_sha256': contract_hash, 'problem_contract_sha256': contract_hash}
            records.append(dict(identity, variant_id=sha(canonical(identity).encode()),
                qualification={'status': 'unknown', 'reason': 'Registry metadata does not verify qualification receipts'},
                provenance=[{'canonical_catalogue_sha256': expected_sha256,
                    'canonical_variant_id': implementation['canonical_variant_id'],
                    'semantic_artifact_kind': 'existing_canonical_qualification_contract',
                    'semantic_payload_location': f'provenance.{kind}.problem_contract',
                    'canonical_receipt_reference': implementation['receipt_sha256'],
                    'authoring_sidecar_created': False}]))
    records.sort(key=lambda r: (r['problem_id'], r['language'], r['variant_id']))
    index = {}
    for record in records:
        index.setdefault(str(record['problem_id']), {}).setdefault(record['language'], []).append(record['variant_id'])
    return {'schema': 'gamma.authoring-variant-catalog-pilot.v1', 'preferred_variant': None,
            'qualification_policy': 'Unknown only; exact canonical contracts are metadata, not new qualification.',
            'unique_problem_count': len(index), 'variant_count': len(records),
            'index': index, 'variants': records, 'unresolved_canonical_slots': unresolved,
            'qualification_created': False, 'source_payloads_opened': 0}


def _identity_json(raw, expected_sha256, maximum):
    """Decode an operator-pinned metadata value without opening any locator."""
    if (type(raw) is not bytes or len(raw) > maximum or
            not isinstance(expected_sha256, str) or
            not re.fullmatch(r'[0-9a-f]{64}', expected_sha256) or sha(raw) != expected_sha256):
        raise ValueError('Pinned bounded identity metadata required')
    def unique(pairs):
        value = {}
        for key, item in pairs:
            if key in value:
                raise ValueError('Duplicate identity metadata field')
            value[key] = item
        return value
    return json.loads(raw, object_pairs_hook=unique,
                      parse_constant=lambda _: (_ for _ in ()).throw(ValueError('Nonfinite identity metadata')))


def _official_identity(value):
    fields = {'questionId', 'questionFrontendId', 'title', 'titleSlug', 'isPaidOnly', 'metaData'}
    if type(value) is not dict or set(value) != fields:
        raise ValueError('Exact official identity-only GraphQL fields required')
    for key in ('questionId', 'questionFrontendId'):
        if type(value[key]) is not str or not re.fullmatch(r'[1-9][0-9]*', value[key]):
            raise ValueError('Exact decimal official identity required')
    if (type(value['title']) is not str or not value['title'].strip() or
            type(value['titleSlug']) is not str or
            not re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*', value['titleSlug']) or
            type(value['isPaidOnly']) is not bool or
            (value['metaData'] is not None and type(value['metaData']) is not str)):
        raise ValueError('Malformed official title, slug, paid flag or signature metadata')
    signature = value['metaData']
    if signature is not None:
        decoded = _identity_json(signature.encode(), sha(signature.encode()), 1024 * 1024)
        if type(decoded) is not dict:
            raise ValueError('Official signature metadata must be an object')
    return {'question_id': value['questionId'], 'frontend_id': value['questionFrontendId'],
            'title': value['title'], 'title_slug': value['titleSlug'], 'is_paid_only': value['isPaidOnly'],
            'signature_metadata_sha256': sha(signature.encode()) if signature is not None else None}


def _identity_provenance(record, snapshots):
    provenance = record['provenance']
    manifest_pin, assignment_pin = provenance['manifest_sha256'], provenance['assignment_sha256']
    if any(type(pin) is not str or not re.fullmatch(r'[0-9a-f]{64}', pin)
           for pin in (manifest_pin, assignment_pin)):
        raise ValueError('Exact original provenance hashes required')
    for key in ('source_path', 'semantics_path'):
        value = provenance[key]
        if (type(value) is not str or not value or Path(value).is_absolute() or
                any(part in ('', '.', '..') for part in value.split('/'))):
            raise ValueError('Exact relative original source and semantics paths required')
    source = Path(provenance['source_path'])
    suffix = '.js' if record['language'] == 'javascript' else '.py'
    if (source.suffix != suffix or not source.stem.isascii() or not source.stem.isdecimal() or
            int(source.stem) != record['original_problem_id']):
        raise ValueError('Original source filename and identity must remain bound')
    if manifest_pin not in snapshots or assignment_pin not in snapshots:
        raise ValueError('Pinned original manifest and assignment snapshots required')
    manifest = _identity_json(snapshots[manifest_pin], manifest_pin, 8 * 1024 * 1024)
    packet = _identity_json(snapshots[assignment_pin], assignment_pin, 8 * 1024 * 1024)
    if (type(manifest) is not dict or manifest.get('assignment_sha256') != assignment_pin or
            type(manifest.get('files')) is not list or type(manifest.get('source_inventory')) is not list or
            type(packet) is not dict or type(packet.get('problems')) is not list):
        raise ValueError('Original assignment and source manifest binding required')
    problems = {}
    for problem in packet['problems']:
        if (type(problem) is not dict or type(problem.get('id')) is not int or
                problem['id'] <= 0 or problem['id'] in problems):
            raise ValueError('Ambiguous original assignment identity')
        problems[problem['id']] = problem
    problem = problems.get(record['original_problem_id'])
    if problem is None or problem.get('slug') != record['delivered_slug']:
        raise ValueError('Delivered slug must match the exact original assignment')
    required = ('external_interface', 'statement_constraints_snapshot', 'return_domain')
    if any(key not in problem for key in required):
        raise ValueError('Original authoring contract fields required')
    contract = {key: problem[key] for key in required}
    optional = ('objective_summary', 'domain_facts', 'comparison', 'mutation_alias_contract',
                'numeric_complexity_contract', 'mutation_alias_review', 'public_fixed_constant')
    contract.update({key: problem[key] for key in optional if key in problem})
    if sha(canonical(contract).encode()) != record['problem_contract_sha256']:
        raise ValueError('Original assignment contract identity mismatch')
    files = {}
    for item in manifest['files']:
        if type(item) is not dict or type(item.get('path')) is not str or item['path'] in files:
            raise ValueError('Ambiguous original manifest file identity')
        files[item['path']] = item.get('sha256')
    source_path, semantics_path = provenance['source_path'], provenance['semantics_path']
    if (files.get(source_path) != record['source_sha256'] or
            files.get(semantics_path) != record['semantics_sha256']):
        raise ValueError('Original source or semantics manifest identity mismatch')
    matches = [row for row in manifest['source_inventory'] if type(row) is dict and
               type(row.get('id')) is int and row['id'] == record['original_problem_id'] and
               row.get('language') == record['language'] and row.get('path') == source_path and
               row.get('sha256') == record['source_sha256'] and
               row.get('semantics_path', str(Path(source_path).with_suffix('.semantics.json'))) == semantics_path and
               row.get('semantics_sha256', files.get(semantics_path)) == record['semantics_sha256']]
    if len(matches) != 1:
        raise ValueError('Exact original source inventory row required')


def reconcile_official_identities(catalog_raw, catalog_sha256, evidence_raw, evidence_sha256,
                                  metadata_snapshots, provenance_snapshots):
    """Optional source-bound identity projection; never relabel the authoring catalog.

    Inputs are exact operator-pinned catalog/evidence bytes and identity-only
    official GraphQL snapshots and original manifest/assignment snapshots indexed
    by their SHA-256. Hashes bind evidence,
    not access authority. Original source, contract, assignment and manifest
    commitments must all match an existing variant and its actual provenance.
    No source/statement locator is followed. A frontend ID/title/signature is
    not a complete behavioral contract, qualification or canonical adoption.
    Missing official records stay unresolved. Multiple exact variants can map
    to one frontend identity without selecting or merging their implementations.
    """
    catalog = _identity_json(catalog_raw, catalog_sha256, 32 * 1024 * 1024)
    evidence = _identity_json(evidence_raw, evidence_sha256, 8 * 1024 * 1024)
    if (type(catalog) is not dict or catalog.get('schema') != 'gamma.authoring-variant-catalog-pilot.v1' or
            type(catalog.get('variants')) is not list or type(evidence) is not dict or
            set(evidence) != {'schema', 'authoring_catalog_sha256', 'records'} or
            evidence['schema'] != 'gamma.authoring-official-identity-evidence.v1' or
            evidence['authoring_catalog_sha256'] != catalog_sha256 or
            type(evidence['records']) is not list or type(metadata_snapshots) is not dict or
            type(provenance_snapshots) is not dict):
        raise ValueError('Exact authoring identity evidence schema and catalog binding required')
    identity_fields = ('problem_id', 'language', 'source_sha256', 'semantics_sha256', 'problem_contract_sha256')
    variants = {}
    for variant in catalog['variants']:
        if (type(variant) is not dict or type(variant.get('problem_id')) is not int or
                variant['problem_id'] <= 0 or variant.get('language') not in ('javascript', 'python') or
                type(variant.get('provenance')) is not list or
                type(variant.get('qualification')) is not dict or
                variant.get('qualification', {}).get('status') != 'unknown'):
            raise ValueError('Existing unknown-qualified exact authoring variants required')
        for name in ('variant_id', 'source_sha256', 'semantics_sha256', 'problem_contract_sha256'):
            if type(variant.get(name)) is not str or not re.fullmatch(r'[0-9a-f]{64}', variant[name]):
                raise ValueError('Invalid exact authoring identity hash')
        identity = {key: variant[key] for key in identity_fields}
        if variant['variant_id'] != sha(canonical(identity).encode()) or variant['variant_id'] in variants:
            raise ValueError('Duplicate or inconsistent authoring variant identity')
        variants[variant['variant_id']] = variant
    fields = {'variant_id', 'original_problem_id', 'language', 'source_sha256', 'semantics_sha256',
              'problem_contract_sha256', 'provenance', 'delivered_slug', 'queried_slug',
              'official_metadata_sha256', 'official_identity'}
    bindings, unresolved, seen = [], [], set()
    for record in evidence['records']:
        if type(record) is not dict or set(record) != fields:
            raise ValueError('Exact source-bound official identity record required')
        vid = record['variant_id']
        if type(vid) is not str or vid not in variants or vid in seen:
            raise ValueError('Unknown or ambiguous duplicate identity evidence')
        seen.add(vid); variant = variants[vid]
        if (type(record['original_problem_id']) is not int or
                record['original_problem_id'] != variant['problem_id'] or
                any(record[key] != variant[key] for key in identity_fields if key != 'problem_id') or
                type(record['provenance']) is not dict or
                set(record['provenance']) != {'manifest_sha256', 'assignment_sha256', 'source_path', 'semantics_path'} or
                record['provenance'] not in variant['provenance']):
            raise ValueError('Source, contract, assignment or manifest provenance mismatch')
        for key in ('delivered_slug', 'queried_slug'):
            if type(record[key]) is not str or not re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*', record[key]):
                raise ValueError('Explicit exact delivered and queried slugs required')
        _identity_provenance(record, provenance_snapshots)
        pin = record['official_metadata_sha256']
        if type(pin) is not str or pin not in metadata_snapshots:
            raise ValueError('Pinned official metadata snapshot unavailable')
        snapshot = _identity_json(metadata_snapshots[pin], pin, 1024 * 1024)
        if (type(snapshot) is not dict or set(snapshot) != {'data'} or
                type(snapshot['data']) is not dict or set(snapshot['data']) != {'question'}):
            raise ValueError('Identity-only GraphQL response required')
        question = snapshot['data']['question']
        if question is None:
            if record['official_identity'] is not None:
                raise ValueError('Missing official record cannot establish an identity')
            unresolved.append({'variant_id': vid, 'original_problem_id': variant['problem_id'],
                               'language': variant['language'], 'reason': 'official_question_not_found',
                               'official_metadata_sha256': pin})
            continue
        official = _official_identity(question)
        if canonical(record['official_identity']) != canonical(official):
            raise ValueError('Official response and claimed identity differ')
        bindings.append({**record, 'official_frontend_id': int(official['frontend_id']),
                         'numeric_identity_changed': variant['problem_id'] != int(official['frontend_id']),
                         'slug_changed': record['delivered_slug'] != official['title_slug'],
                         'semantic_contract_established': False, 'qualification_created': False,
                         'canonical_adoption_created': False})
    order = lambda row: (row['original_problem_id'], row['language'], row['variant_id'])
    return {'schema': 'gamma.authoring-official-identity-projection.v1',
            'authoring_catalog_sha256': catalog_sha256, 'identity_evidence_sha256': evidence_sha256,
            'bindings': sorted(bindings, key=order), 'unresolved': sorted(unresolved, key=order),
            'unexamined_variant_count': len(variants) - len(seen),
            'original_catalog_changed': False, 'source_payloads_opened': 0,
            'semantic_contract_established': False, 'qualification_created': False,
            'canonical_adoption_created': False}


def query_official_identity(catalog_raw, catalog_sha256, evidence_raw, evidence_sha256,
                           metadata_snapshots, provenance_snapshots, official_problem_id, language):
    """Return original variants through revalidated optional official identities."""
    if (type(official_problem_id) is not int or official_problem_id <= 0 or
            type(language) is not str or language not in ('javascript', 'python')):
        raise ValueError('Exact numeric official identity and language required')
    projection = reconcile_official_identities(catalog_raw, catalog_sha256, evidence_raw,
                                               evidence_sha256, metadata_snapshots, provenance_snapshots)
    catalog = _identity_json(catalog_raw, catalog_sha256, 32 * 1024 * 1024)
    matches = {row['variant_id'] for row in projection['bindings']
               if row['official_frontend_id'] == official_problem_id and row['language'] == language}
    return tuple(row for row in catalog['variants'] if row['variant_id'] in matches)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('manifests', nargs='+', type=Path)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    result = build(args.manifests)
    args.output.write_text(json.dumps(result, sort_keys=True, indent=2) + '\n',
                           encoding='utf-8', newline='\n')


if __name__ == '__main__':
    main()
