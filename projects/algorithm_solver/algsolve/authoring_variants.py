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
