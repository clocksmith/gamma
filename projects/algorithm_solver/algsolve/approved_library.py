"""Bind approved stored answers to completed, independently checked evidence.

The catalog qualifies stored references, not recognition of a new question.
Unapproved entries remain retrieval candidates so exclusion cannot silently
redirect a request to a different, approved sibling.
"""
from __future__ import annotations

import argparse
from collections import Counter
from dataclasses import asdict
import hashlib
import json
from pathlib import Path


# Development policy: all four recorded sibling errors had gaps below 0.011.
# This conservative round boundary is fixed before independent scoring; it is
# not a calibrated error probability and does not prove semantic equivalence.
MIN_SIBLING_MARGIN = 0.02


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'),
                                     allow_nan=False).encode()).hexdigest()


def code_hash(code):
    return hashlib.sha256(code.encode()).hexdigest()


def selected_reference(entry):
    return (next((r for r in entry.references if r.get('validated')), None)
            or next(iter(entry.references), None))


def entry_hash(entry):
    return digest(asdict(entry))


def build(entries, inventory, results, *, evidence):
    from .library_audit import independent_status
    by_key = {e.key: e for e in entries}
    inv = {r['key']: r for r in inventory}
    observed = {r['key']: r for r in results}
    eligible = {k for k, r in inv.items() if not r.get('excluded')}
    if len(inv) != len(inventory) or len(observed) != len(results) or len(by_key) != len(entries):
        raise ValueError('Duplicate identities in approval inputs')
    if set(by_key) != eligible or set(observed) != eligible:
        raise ValueError('Approval requires a complete eligible-library audit')
    approved, excluded = {}, {}
    for key, row in inv.items():
        if row.get('excluded'):
            excluded[key] = row['excluded']
            continue
        entry, result = by_key[key], observed[key]
        reference = selected_reference(entry)
        stored = result['stored_solution']
        verdicts = stored.get('verdicts', [])
        source_hash = code_hash(reference['code']) if reference else None
        recorded = next((r for r in row['references'] if r['code_sha256'] == source_hash), None)
        reason = None
        if not all(row.get(f) for f in ('identity_valid', 'provenance_present', 'interface_compatible')):
            reason = 'invalid_identity_provenance_or_interface'
        elif recorded is None:
            raise ValueError('Reference changed since inventory: ' + key)
        elif stored['status'] != 'passed':
            classified = independent_status(verdicts)
            reason = classified if classified in ('infrastructure_error', 'unusable_independent_tests') else stored['status']
        elif not verdicts or any(not v.get('passed') or v.get('tests_passed', 0) <= 0 for v in verdicts):
            reason = 'missing_positive_independent_verdicts'
        elif not result['accepted_and_correct'] or result['result'].get('code_sha256') != source_hash:
            reason = 'exact_answer_path_not_qualified'
        if reason:
            excluded[key] = reason
            continue
        approved[key] = {'entry_sha256': entry_hash(entry), 'code_sha256': source_hash,
                         'reference_uid': reference.get('uid'),
                         'independent_test_sets': row['independent_test_sets'],
                         'independent_verdicts': verdicts,
                         'exact_answer_sha256': digest(result)}
    body = {'schema': 'algsolve.approved-library.v1',
            'scope': 'stored-answer qualification; recognition release is separately gated',
            'identity_policy': {'minimum_sibling_margin': MIN_SIBLING_MARGIN,
                                'basis': 'previously inspected recognition failures; development only'},
            'evidence': evidence, 'approved': approved, 'excluded': excluded,
            'counts': {'inventory': len(inv), 'approved': len(approved), 'excluded': len(excluded),
                       'exclusion_reasons': dict(Counter(excluded.values()))}}
    return dict(body, sha256=digest(body))


class ApprovedLibrary:
    def __init__(self, manifest):
        body = {k: v for k, v in manifest.items() if k != 'sha256'}
        if manifest.get('schema') != 'algsolve.approved-library.v1' or digest(body) != manifest.get('sha256'):
            raise ValueError('Invalid approved-library manifest')
        if set(manifest['approved']) & set(manifest['excluded']):
            raise ValueError('An entry cannot be both approved and excluded')
        self.manifest = manifest

    @classmethod
    def load(cls, path):
        return cls(json.loads(Path(path).read_text()))

    def check(self, entry):
        record = self.manifest['approved'].get(entry.key)
        if record is None:
            return {'approved': False, 'reason': self.manifest['excluded'].get(entry.key, 'not_in_manifest')}
        reference = selected_reference(entry)
        if (entry_hash(entry) != record['entry_sha256'] or reference is None
                or code_hash(reference['code']) != record['code_sha256']):
            return {'approved': False, 'reason': 'source_changed_since_qualification'}
        return {'approved': True, 'manifest_sha256': self.manifest['sha256'],
                'code_sha256': record['code_sha256'], 'reference_uid': record['reference_uid'],
                'independent_test_count': sum(v['tests_passed'] for v in record['independent_verdicts']),
                'scope': 'stored reference on its original problem; query identity checked separately'}

    def identity_check(self, entry, candidates, lookup, *, exact=False, minimum_margin=0.):
        from .splits import sibling_base
        if exact:
            return {'accepted': True, 'basis': 'exact statement and interface'}
        family = sibling_base(entry.slug)
        alternatives = [c for c in candidates[1:] if
                        sibling_base(lookup.entries[lookup.by_key[c['key']]].slug) == family]
        if alternatives and candidates[0]['score'] - max(c['score'] for c in alternatives) < max(MIN_SIBLING_MARGIN, minimum_margin):
            return {'accepted': False, 'reason': 'sibling_identity_ambiguous',
                    'alternatives': [entry.key] + [c['key'] for c in alternatives],
                    'detail': 'Similar versions remain unresolved; provide the full constraints and required output.'}
        return {'accepted': True, 'basis': 'sibling margin guard passed; retrieval acceptance is separate'}


def load_context(path):
    """CPU-only bounded lookup. Exact requests need no embedding model load."""
    import numpy as np
    from . import corpus
    from .embed import LazyCPUEmbedder
    from .lookup import LookupIndex, load_thresholds
    from .records import LANE_ROOT
    from .routes import Budget, Context
    catalog = ApprovedLibrary.load(path)
    entries = corpus.read_entries()
    keys = json.loads(corpus.KEYS_PATH.read_text())
    if keys != [e.key for e in entries]:
        raise ValueError('Corpus embedding key order differs')
    if set(keys) != set(catalog.manifest['approved']) | set(catalog.manifest['excluded']):
        raise ValueError('Library membership changed since qualification')
    allowed = [i for i, e in enumerate(entries) if catalog.manifest['excluded'].get(e.key)
               != 'protected_composition_alias']
    entries = [entries[i] for i in allowed]
    context = Context(generator=None, embedder=LazyCPUEmbedder(),
                      lookup=LookupIndex(entries, np.load(corpus.EMBEDDINGS_PATH)[allowed]),
                      thresholds=load_thresholds(), classifier=None, entries=entries,
                      budget=Budget.from_contract(json.loads((LANE_ROOT / 'contracts/run_contract.json').read_text())))
    context.statement_thresholds = json.loads((LANE_ROOT / 'contracts/statement_lookup_thresholds.json').read_text())
    return context, catalog


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('audit', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    from .library_audit import inputs, rows, sha
    _, entries, _, boundary = inputs()
    contract = json.loads((args.audit / 'contract.json').read_text())
    # Input identity is checked against the original snapshot, even when the
    # builder runs with newer code. It never reinterprets old test failures.
    from .records import LANE_ROOT
    for relative, expected in contract['inputs_sha256'].items():
        if sha(LANE_ROOT / relative) != expected:
            raise ValueError('Audit input changed: ' + relative)
    if digest(boundary) != contract['boundary_sha256']:
        raise ValueError('Protected boundary changed')
    manifest = build(entries, rows(args.audit / 'inventory.jsonl'), rows(args.audit / 'answers.jsonl'),
                     evidence={name: sha(args.audit / name) for name in
                               ('contract.json', 'inventory.jsonl', 'answers.jsonl')})
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open('x') as stream:
        stream.write(json.dumps(manifest, indent=2) + '\n')
    print(json.dumps({'sha256': manifest['sha256'], **manifest['counts']}, indent=2))


if __name__ == '__main__':
    main()
