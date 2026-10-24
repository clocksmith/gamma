"""Adapter around immutable measured potential-lift code; no optimizer."""
import hashlib
import json
import prototype


def execute(inputs, expected_old):
    texts, banned, pool = inputs['texts'], inputs['banned'], inputs['pool']
    shared = prototype.full._suffix.build_pool(texts, banned)
    extras = sorted({word for word in inputs['seed'] if len(word) > 1}-set(shared))
    assert pool == sorted(set(shared) | set(extras) | set(inputs['alphabet']))
    assert len(shared) == expected_old['shared_learned_entries']
    assert len(extras) == expected_old['seed_extra_entries']
    assert hashlib.sha256(json.dumps(extras, ensure_ascii=True).encode()).hexdigest() == expected_old['seed_extras_sha256']
    lift = prototype.Lift(texts, banned, pool, inputs['q'], inputs['seed'], inputs['alphabet'],
                          inputs['denominator'], old_source_hashes=inputs['source_hashes'], old_banned=banned)
    index = lift.index
    shape = {'source_characters': len(index.positions), 'full_groups': len(index.groups),
             'full_distinct_entries': index.distinct_allowed_entries,
             'exact_ban_occurrences': sum(len(s) for rows in index.banned_ends.values() for s in rows)}
    assert shape == inputs['geometry']
    result = lift.certificate(256)
    cert = inputs['parent_certificate']
    assert cert['denominator'] == inputs['denominator']
    assert [result['path_numerators'][pid] for pid in sorted(texts)] == cert['per_program_path_numerators']
    assert sum(result['path_numerators'].values()) == cert['relaxed_paths_numerator']
    assert result['old_charge'] == cert['top_capacity_numerator']
    assert result['old_numerator'] == cert['numerator']
    assert -(-result['old_numerator']//result['denominator']) == cert['integer_lower_bound'] > 0
    assert result['old_occurrences'] == expected_old['occurrences']
    assert result['rows'][0]['integer_lower_bound'] >= cert['integer_lower_bound']
    assert [row['k'] for row in result['rows']] == list(range(257))
    return result, shape
