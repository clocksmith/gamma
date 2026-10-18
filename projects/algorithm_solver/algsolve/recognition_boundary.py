"""Metadata-only exclusion closure for recognition qualification.

The production index remains intact. This experiment removes reserved composer
families, member identities and recorded near-duplicate aliases before execution.
"""
from __future__ import annotations

from .splits import sibling_base


def exclusion_closure(entries, problem_metadata, reservation, near_duplicates):
    pool = reservation['reservation']['pool']
    keys = {r['key'] for r in pool}
    families = {r['family'] for r in pool}
    uids = {uid for r in pool for uid in r['members']}
    uids.update(r['judge_uid'] for r in pool if r.get('judge_uid'))
    changed = True
    while changed:
        before = (len(keys), len(families), len(uids))
        for p in problem_metadata:
            family = sibling_base(p['slug']) if p.get('slug') else ''
            if p['uid'] in uids or family in families:
                uids.add(p['uid'])
                if family:
                    families.add(family)
        for e in entries:
            family = sibling_base(e['slug'])
            if (e['key'] in keys or family in families or set(e['members']) & uids
                    or e.get('judge_uid') in uids):
                keys.add(e['key'])
                families.add(family)
                uids.update(e['members'])
        for pair in near_duplicates.get('pairs', []):
            if pair['index_key'] in keys or pair['pool_uid'] in uids:
                keys.add(pair['index_key'])
                uids.add(pair['pool_uid'])
        changed = before != (len(keys), len(families), len(uids))
    return {'keys': sorted(keys), 'families': sorted(families), 'uids': sorted(uids),
            'policy': 'transitive reserved family/member/recorded-near-duplicate closure; metadata only'}
