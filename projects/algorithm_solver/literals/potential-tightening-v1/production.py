"""Paired fixed-potential construction; supplied inputs only, no optimizer."""
import hashlib
import json
import binding as b
import tighten


def reconcile50(inputs, paired, shape, expected):
    """Bind rebuilt scientific50 proof to the independently accepted public50."""
    proof = paired['lifted']; paths = proof['path_numerators']
    assert expected['complete'] is True and expected['validation_loaded'] is False
    assert expected['all257_independently_replayed'] is expected['old_certificate_independently_replayed'] is expected['suffix_potential_proof_checked'] is True
    scalar = {'bindings_sha256': b.digest(inputs['bindings']),
              'source_identity_sha256': b.digest(inputs['source_hashes']),
              'banned_set_sha256': b.digest(sorted(inputs['banned'])),
              'parent_certificate_sha256': b.digest(inputs['parent_certificate']),
              'old_occurrence_order_sha256': proof['occurrence_sha256'],
              'old_path_terms_sha256': b.digest([paths[pid] for pid in sorted(paths)]),
              'checked_proof_sha256': paired['digests']['lifted_proof_sha256'],
              'top_entries_sha256': paired['digests']['lifted_top_entries_sha256'],
              'fit_problems': len(inputs['texts']), 'old_pool_entries': len(inputs['pool']),
              'seed_entries': len(inputs['seed']), 'old_occurrences': proof['old_occurrences'],
              'geometry': shape, 'denominator': proof['denominator'],
              'path_numerator': sum(paths.values()), 'old_charge': proof['old_charge'],
              'old_numerator': proof['old_numerator'],
              'old_integer_lower_bound': -(-proof['old_numerator']//proof['denominator']),
              'class_counts': {str(k): v for k, v in proof['class_counts'].items()},
              'rows': proof['rows'],
              'largest_positive_k': max((row['k'] for row in proof['rows'] if row['integer_lower_bound'] > 0), default=None)}
    for key, value in scalar.items(): b.strict_equal(expected[key], value)


def execute(inputs, expected_old, expected50):
    texts, banned, pool = inputs['texts'], inputs['banned'], inputs['pool']
    model = tighten.Tighten(texts, banned, pool, inputs['q'], inputs['seed'], inputs['alphabet'],
        inputs['denominator'], old_source_hashes=inputs['source_hashes'], old_banned=banned,
        expected_occurrence_sha256=expected50['old_occurrence_order_sha256'],
        expected_old_certificate=inputs['parent_certificate'])
    # Exact interval completeness is proved by Tighten's old-pool mapping. This
    # avoids building the entire old shared string pool a second time. Absent
    # learned seed extras remain counted, though they have zero occurrence weight.
    support = {eid: model.support[gid] for (gid, length), eid in model.old_entry_ids.items()}
    shared = {word for eid, word in enumerate(pool) if len(word) > 1 and support.get(eid) == 2}
    extras = sorted({word for word in inputs['seed'] if len(word) > 1}-shared)
    assert pool == sorted(shared | set(extras) | set(inputs['alphabet']))
    rebuilt_old = {'shared_learned_entries': len(shared), 'seed_extra_entries': len(extras),
                   'pool_entries': len(pool), 'maximum_entry_length': max(map(len, pool)),
                   'occurrences': model.old_occurrences,
                   'seed_extras_sha256': hashlib.sha256(json.dumps(extras, ensure_ascii=True).encode()).hexdigest()}
    for key, value in rebuilt_old.items(): b.strict_equal(expected_old[key], value)
    index = model.index
    shape = {'source_characters': len(index.positions), 'full_groups': len(index.groups),
             'full_distinct_entries': index.distinct_allowed_entries,
             'exact_ban_occurrences': sum(len(s) for rows in index.banned_ends.values() for s in rows)}
    b.strict_equal(inputs['geometry'], shape)
    result = model.certificate(256)
    assert result['lifted']['old_numerator'] > 0
    assert [r['k'] for r in result['tightened']['rows']] == list(range(257))
    reconcile50(inputs, result, shape, expected50)
    return result, shape
