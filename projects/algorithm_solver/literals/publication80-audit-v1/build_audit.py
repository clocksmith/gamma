"""Rebuild a metadata-only rights/provenance inventory; never read program bodies."""
from __future__ import annotations

import hashlib
import json
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
LIT = HERE.parent
ALG = LIT.parent


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    inputs: dict[str, str] = {}

    def read(relative: str):
        path = ALG / relative
        inputs[relative] = sha(path)
        return json.loads(path.read_text())

    cohort = dict(read('literals/guides-joint80-8-v2/published-8-v1-sources.json'))
    assert len(cohort) == 80
    attribution = {r['id']: r for r in read('literals/clusters-v1/ATTRIBUTION.json')['entries']}
    additional = {r['id']: r for r in read('literals/scale-v2/additional-provenance.json')['rows']}
    assert not attribution.keys() & additional.keys()
    assert attribution.keys() | additional.keys() == cohort.keys()
    manifests = read('literals/scale-v2/generated/manifest.json')['rows']
    originals = {r['id']: r for r in manifests if r['variant'] == 'original'}
    compact = {r['id']: r for r in manifests if r['variant'] == 'compact'}
    cluster_originals = {}
    for phase in ('fit-generated-v1', 'heldback-generated'):
        # These are historical metadata manifests only, not any reserved source set.
        rows = read(f'literals/clusters-v1/{phase}/manifest.json')['rows']
        cluster_originals.update({r['id']: r for r in rows if r['variant'] == 'original'})
    rewrites = {r['id']: r for r in read('literals/style150-v1/evidence/results.json')['rewrites']['rows']}
    doocs = read('findings/source-corpus-js-py-128-v3/summary.json')['rows'][0]
    assert doocs['uid'] == 'lcd:1046'
    metadata = read('literals/notices/UPSTREAM-LICENSE-METADATA.json')
    read('literals/publication80-audit-v1/upstream-checks.json')
    rows = []
    for pid, published_hash in sorted(cohort.items()):
        assert compact[pid]['sha256'] == published_hash
        assert compact[pid]['original_sha256'] == originals[pid]['sha256']
        assert pid in rewrites and rewrites[pid]['passed']
        row = {
            'problem_id': pid,
            'published_compact_sha256': published_hash,
            'normalized_original_sha256': originals[pid]['sha256'],
            'published_lineage_record': 'literals/scale-v2/generated/manifest.json',
            'style150_rewrite_inventory': {
                'sha256': rewrites[pid]['sha256'],
                'qualification_passed_as_recorded': rewrites[pid]['passed'],
                'qualification_checks_as_recorded': rewrites[pid]['checks'],
                'record': 'literals/style150-v1/evidence/results.json',
                'release_selection': False,
            },
            'new_rewrite_publication_cleared': False,
            'open_items': ['G1', 'G2', 'G6'],
        }
        if pid in attribution:
            a = attribution[pid]
            assert cluster_originals[pid]['sha256'] == originals[pid]['sha256']
            row.update({
                'origin_class': 'lcd_reference_derived',
                'provenance_record': 'literals/clusters-v1/ATTRIBUTION.json',
                'problem_url': a['attribution_as_recorded'][0],
                'selected_reference_uid': a['selected_reference_uid'],
                'selected_reference_sha256': a['selected_reference_sha256'],
                'upstream_snapshot': a['source_dataset_snapshot'],
                'reported_license_metadata': a['license_metadata_as_recorded'],
                'license_assignment': 'Unresolved source-specific scope of HF Apache-2.0 versus linked GitHub MIT; merged doocs notice alone is not assignment.',
                'adaptations_as_recorded': [a['changes'], a['experiment_changes']],
            })
            row['open_items'].append('G3')
        else:
            a = additional[pid]
            assert a['source_sha256'] == originals[pid]['sha256']
            row.update({
                'provenance_record': 'literals/scale-v2/additional-provenance.json',
                'problem_url': 'https://leetcode.com/problems/' + a['key'].removeprefix('lc:'),
            })
            if pid == 1046:
                d = doocs['source_provenance']
                assert doocs['sources']['javascript-normalized']['sha256'] == originals[pid]['sha256']
                row.update({
                    'origin_class': 'doocs_reference_derived',
                    'resolved_provenance_record': 'findings/source-corpus-js-py-128-v3/summary.json',
                    'selected_reference_sha256': d['javascript_sha256'],
                    'upstream_snapshot': 'doocs/leetcode@' + d['javascript_upstream_revision'],
                    'upstream_source_url': 'https://github.com/doocs/leetcode/blob/' + d['javascript_upstream_revision'] + '/solution/1000-1099/1046.Last%20Stone%20Weight/Solution.js',
                    'reported_license_metadata': [d['javascript_license']],
                    'adaptation_as_recorded': d['adaptation'],
                    'license_assignment': 'Recorded doocs source provenance; CC-BY-SA-4.0 notice and separate README commercial-authorization language need publication review.',
                })
                row['open_items'].append('G5')
            else:
                provenance = a['source_provenance']
                seal_path = provenance.get('owner_source_seal', provenance.get('original_source_seal'))
                seal_hash = provenance.get('owner_source_seal_sha256', provenance.get('original_source_seal_sha256'))
                assert seal_path and seal_hash
                candidates = (ALG / seal_path, Path('/home/x/deco/gamma/projects/algorithm_solver') / seal_path)
                local = next((p for p in candidates if p.exists()), None)
                seal_verified = local is not None and sha(local) == seal_hash
                row.update({
                    'origin_class': 'owner_supplied_agent_candidate',
                    'provenance_kind': provenance['kind'],
                    'owner_source_seal_record': seal_path,
                    'owner_source_seal_sha256': seal_hash,
                    'owner_source_seal_hash_verified': seal_verified,
                    'reference_attribution_as_recorded': provenance['reference_attribution'],
                    'reported_license_metadata': provenance.get('reference_license', []),
                    'license_assignment': 'Reference metadata is not proof of copied origin or a grant for the owner-supplied candidate; author/input/permission scope is unresolved.',
                })
                row['open_items'].append('G4')
        rows.append(row)
    counts = Counter(r['origin_class'] for r in rows)
    assert counts == {'lcd_reference_derived': 60, 'owner_supplied_agent_candidate': 19, 'doocs_reference_derived': 1}
    assert all(r.get('owner_source_seal_hash_verified', True) for r in rows)
    assert all(r['published_compact_sha256'] != r['style150_rewrite_inventory']['sha256'] for r in rows)
    notice_checks = []
    for evidence in metadata['evidence']:
        filename = 'LeetCodeDataset-HF-card.md' if 'huggingface' in evidence['url'] else 'LeetCodeDataset-GitHub-MIT.txt'
        relative = 'literals/notices/licenses/' + filename
        assert sha(ALG / relative) == evidence['sha256']
        notice_checks.append({'path': relative, 'sha256': evidence['sha256'], 'hash_matches_prior_receipt': True})
    output = {
        'schema': 'gamma.publication80.metadata-audit.v1',
        'date_utc': '2026-10-23',
        'scope': 'Exact live JavaScript 80 cohort; metadata-only inventory for a future owner publication decision. No source bodies, statements, tests, dictionaries, sequences, held-out or protected data were read.',
        'source_execution_performed': False,
        'new_publication_authorized': False,
        'cohort_count': len(rows),
        'origin_counts': dict(sorted(counts.items())),
        'published_compact_hashes_match_manifest': 80,
        'normalized_original_lineage_hashes_match': 80,
        'style150_rewrite_inventory_rows': 80,
        'style150_rewrites_distinct_from_published_compact': 80,
        'owner_candidate_seals_verified': 19,
        'new_rewrites_cleared_for_publication': 0,
        'notice_checks': notice_checks,
        'input_metadata_sha256': dict(sorted(inputs.items())),
        'rows': rows,
    }
    (HERE / 'audit.json').write_text(json.dumps(output, indent=2, sort_keys=True) + '\n')
    print(json.dumps({k: v for k, v in output.items() if k.endswith('count') or k.endswith('counts') or isinstance(v, int)}, sort_keys=True))


if __name__ == '__main__':
    main()
