"""Fixed-penalty owner caps; original inputs only, no optimizer."""
import hashlib
import json
import binding as b
import caps


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



def reconcile53(inputs,base,shape,expected):
    proof=base['tightened'];paths=proof['path_numerators'];D=proof['denominator']
    values={'bindings_sha256':b.digest(inputs['bindings']),
        'source_identity_sha256':b.digest(inputs['source_hashes']),
        'banned_set_sha256':b.digest(sorted(inputs['banned'])),
        'parent_certificate_sha256':b.digest(inputs['parent_certificate']),
        'checked_proof_sha256':b.digest({key:base[key] for key in ('schema','lifted','tightened',
            'new_only_class_counts','new_only_top_entries','digests','reductions','deltas')}),
        'top_entries_sha256':base['digests']['tightened_top_entries_sha256'],
        'old_occurrence_order_sha256':proof['occurrence_sha256'],
        'old_path_terms_sha256':b.digest([paths[pid] for pid in sorted(paths)]),
        'fit_problems':len(inputs['texts']),'old_pool_entries':len(inputs['pool']),
        'seed_entries':len(inputs['seed']),'old_occurrences':proof['old_occurrences'],
        'geometry':shape,'denominator':D,'path_numerator':sum(paths.values()),
        'old_charge':proof['old_charge'],'old_numerator':proof['old_numerator'],
        'old_integer_lower_bound':-(-proof['old_numerator']//D),
        'class_counts':{str(k):v for k,v in proof['class_counts'].items()},
        'rows':proof['rows'],'lifted_rows':base['lifted']['rows'],'paired_digests':base['digests'],
        'reductions':base['reductions'],'deltas':base['deltas'],'new_only_class_counts':base['new_only_class_counts'],
        'largest_positive_k':max((r['k'] for r in proof['rows'] if r['integer_lower_bound']>0),default=None),
        'lifted_largest_positive_k':max((r['k'] for r in base['lifted']['rows'] if r['integer_lower_bound']>0),default=None)}
    for key,value in values.items():b.strict_equal(expected[key],value)


def execute(inputs,expected_old,expected50,expected53):
    texts,banned,pool=inputs['texts'],inputs['banned'],inputs['pool']
    result=caps.check(texts,banned,pool,inputs['q'],inputs['seed'],inputs['alphabet'],inputs['denominator'],
        expected_source_hashes=inputs['source_hashes'],expected_old_banned=banned,
        expected_occurrence_sha256=expected50['old_occurrence_order_sha256'],
        expected_old_certificate=inputs['parent_certificate'])
    # Explicitly charge a separate structural index for shape reconciliation;
    # the prototype owns its own complete old/shared identity proof.
    index=caps.parent.full.Index(texts,banned)
    shape={'source_characters':len(index.positions),'full_groups':len(index.groups),
           'full_distinct_entries':index.distinct_allowed_entries,
           'exact_ban_occurrences':sum(len(s) for rows in index.banned_ends.values() for s in rows)}
    b.strict_equal(shape,inputs['geometry'])
    extras=sorted(w for w in inputs['seed'] if len(w)>1 and sum(w in t for t in texts.values())<2)
    checks={'pool_entries':len(pool),'maximum_entry_length':max(map(len,pool)),
        'occurrences':len(inputs['q']),'shared_learned_entries':sum(len(w)>1 for w in pool)-len(extras),
        'seed_extra_entries':len(extras),
        'seed_extras_sha256':hashlib.sha256(json.dumps(extras,ensure_ascii=True).encode()).hexdigest()}
    for key,value in checks.items():b.strict_equal(expected_old[key],value)
    reconcile50(inputs,result['base'],shape,expected50)
    reconcile53(inputs,result['base'],shape,expected53)
    return result,shape
