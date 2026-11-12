"""Draft a fresh BITS evaluation pool from metadata only (no statements, tests or
solutions are read).

  python -m algsolve.synth.bits_fresh_pool --dataset-ids <file of LCD question ids> \
      --family-review contracts/bits_step1_family_review_v1.json --size 120 --out <draft json>

Candidates: problem-index rows marked known_corpus_nonreserved_pending_independent_review,
LeetCode source, not paid, not design, present in the pinned LeetCodeDataset
(identity only). Excluded, with the reason recorded: every row connected to the
existing reservation boundary or to any of the 236 BITS step 1 candidates through
key, slug stem (sibling_base), family label, related problems or structural group.
The remaining rows are ordered by SHA-256 of their key and the first ``size`` are
the draft. Nothing is frozen until the owner approves the draft.

These rows have never been used by BITS training, the teacher, retrieval, tuning
or the pilot evaluations, but the repository catalogue holds authored reference
solutions for many of them; "fresh" is relative to BITS, not to the repository.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from ..records import LANE_ROOT
from ..splits import sibling_base
from .semantic_allowlist import compile_committed_allowlist_and_boundary


RESERVED_STATUSES = {'historical_reserved382', 'final100_exact_id_reserved', 'unresolved_global_identity_alias_metadata_only',
                     'outside-4081-freeze', 'hack2hire-public-preview', 'previously_authorized_400'}


def draft(dataset_ids, family_review, size):
    """Components over the same identity tokens as the allowlist compiler; taint only from
    reservations, the 400 previously authorized rows (all BITS candidates) and BITS families."""
    from .semantic_allowlist import _row_identity_tokens
    compiled = compile_committed_allowlist_and_boundary()
    audit = compiled['audit']
    lane = LANE_ROOT
    rows = [json.loads(line) for line in (lane / 'catalogue/PROBLEM_INDEX.jsonl').read_text().splitlines() if line.strip()]
    parent = {}
    def find(t):
        parent.setdefault(t, t)
        while parent[t] != t:
            parent[t] = parent[parent[t]]; t = parent[t]
        return t
    def union(tokens):
        tokens = list(tokens)
        if not tokens: return
        first = find(tokens[0])
        for other in tokens[1:]:
            right = find(other)
            if first != right:
                low, high = sorted((first, right)); parent[high] = low; first = low
    tainted = set()
    for r in rows:
        tokens = _row_identity_tokens(r); union(tokens)
        if r.get('boundary_status') in RESERVED_STATUSES:
            tainted.update(tokens)
    sample = json.loads((lane / 'contracts/sample_manifest.json').read_text())
    confirmation = json.loads((lane / 'contracts/typed_confirmation_v1.json').read_text())
    waves = json.loads((lane / 'contracts/js_corpus_reservations_v1.json').read_text())
    library = json.loads((lane / 'findings/known-lookup-release-v2/approved-library.json').read_text())
    extra = []
    for q in sample['recognition'] + sample['recognition_dev']:
        if q.get('target'):
            extra.append(['id:' + q['target']] + (['fam:' + sibling_base(q['target'][3:])] if q['target'].startswith('lc:') else []))
    for uids in sample['solving'].values():
        extra += [['id:' + u] for u in uids]
    for key in sample['near_duplicates']['dropped_index_entries']:
        extra.append(['id:' + key] + (['fam:' + sibling_base(key[3:])] if key.startswith('lc:') else []))
    for pair in sample['near_duplicates']['sibling_pairs_kept']:
        extra.append(['id:' + pair['index_key'], 'id:' + pair['pool_uid']])
    for e in confirmation['reservation']['pool']:
        extra.append(['id:' + e['key'], 'fam:' + e['family'], 'fam:' + sibling_base(e['key'].removeprefix('lc:')), *('id:' + m for m in e['members'])])
    for item in confirmation['development']['identities']:
        extra.append(['id:' + item['uid'], 'fam:' + item['family'], 'fam:' + sibling_base(item['family'])])
    for wave in waves['waves']:
        for w in wave['rows']:
            n = int(w['id'])
            extra.append([f'id:lcd:{n}', f'id:leetcode:{n}', f'id:doocs:{n:04d}', 'id:' + w['key'], 'fam:' + w['family'],
                          'fam:' + sibling_base(w['key'].removeprefix('lc:'))])
    for key, reason in library['excluded'].items():
        if reason == 'protected_composition_alias':
            extra.append(['id:' + key] + (['fam:' + sibling_base(key[3:])] if key.startswith('lc:') else []))
    for uid, family in family_review['family_by_uid'].items():
        extra.append(['id:' + uid, 'fam:' + family])
    for tokens in extra:
        union(tokens); tainted.update(tokens)
    tainted_roots = {find(t) for t in tainted}
    kept, excluded = [], {}
    for r in rows:
        if r.get('boundary_status') != 'known_corpus_nonreserved_pending_independent_review':
            continue
        reason = ('not_leetcode' if r['source'] != 'leetcode' else 'paid' if r.get('paid_only') else 'design' if r.get('design')
                  else 'absent_from_pinned_dataset' if r['id'] not in dataset_ids
                  else 'connected_to_reserved_or_bits' if any(find(t) in tainted_roots for t in _row_identity_tokens(r)) else None)
        if reason:
            excluded[reason] = excluded.get(reason, 0) + 1
        else:
            kept.append(r)
    kept.sort(key=lambda r: hashlib.sha256(r['key'].encode()).hexdigest())
    chosen = kept[:size]
    return {
        'schema': 'algsolve.bits-fresh-pool-draft.v1', 'status': 'draft_not_frozen',
        'size': size, 'eligible_after_exclusions': len(kept), 'excluded_by_reason': excluded,
        'taint_sources': sorted(RESERVED_STATUSES) + ['sample_manifest', 'typed_confirmation_v1', 'js_corpus_reservations_v1',
                                                      'approved-library protected aliases', 'BITS family review'],
        'boundary_sha256': audit['boundary_sha256'],
        'family_review_sha256': hashlib.sha256(json.dumps(family_review, sort_keys=True).encode()).hexdigest(),
        'order': 'ascending SHA-256 of problem-index key',
        'rows': [{'uid': 'lcd:' + r['id'], 'key': r['key'], 'slug': r['slug'], 'difficulty': r.get('difficulty'),
                  'stem': sibling_base(r['slug'])} for r in chosen],
        'caveat': 'Fresh relative to BITS; the repository catalogue holds authored solutions for many of these rows.',
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--dataset-ids', required=True, type=Path)
    parser.add_argument('--family-review', required=True, type=Path)
    parser.add_argument('--size', type=int, default=120)
    parser.add_argument('--out', required=True, type=Path)
    args = parser.parse_args()
    ids = set(args.dataset_ids.read_text().split())
    result = draft(ids, json.loads(args.family_review.read_text()), args.size)
    with args.out.open('x', encoding='utf-8') as stream:
        stream.write(json.dumps(result, indent=1, sort_keys=True) + '\n')
    print(json.dumps({k: result[k] for k in ('eligible_after_exclusions', 'excluded_by_reason', 'size')}))


if __name__ == '__main__':
    main()
