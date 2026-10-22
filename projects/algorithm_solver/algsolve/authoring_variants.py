"""Read-only authoring-variant catalog. Not a qualification or admission ledger."""
import argparse
import hashlib
import json
from pathlib import Path


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
