"""Fresh global prices plus required owner allocation; original inputs only."""
import hashlib
import json
import binding as b
import caps
import integration as integ


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


def execute(inputs,c,cohort):
    expected_old=c['old_arms'][cohort];expected50=c['parent50_arms'][cohort]
    expected53=c['parent53_arms'][cohort];expected57=c['parent57_arms'][cohort]
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
    reconcile50(inputs,result['base57']['base'],shape,expected50)
    reconcile53(inputs,result['base57']['base'],shape,expected53)
    assert b.digest(caps.scientific57(result['base57']))==expected57['scientific_proof_sha256']
    assert b.digest(result['base57'])==expected57['production_proof_sha256']
    for key in ('rows','deltas_vs53'):b.strict_equal(result['base57'][key],expected57[key])
    for key in ('owner_caps','owner_top_entries','owner_entry_counts','owner_prefixes','capped_prefixes',
                'one_owner_prefix','marginal_choices','shared_prefix'):
        assert b.digest(result['base57'][key])==expected57[key+'_sha256']
    assert len(inputs['alphabet'])==len(set(inputs['alphabet']))==96 and all(len(ch)==1 for ch in inputs['alphabet'])
    assert set(inputs['alphabet'])<=set(pool) and not set(pool)&set(banned)
    assert all(set(text)<=set(inputs['alphabet']) for text in texts.values())
    cov=integ.coverage.production(texts,pool,banned)
    forced=integ.coverage_history(cov,inputs,c,cohort,'prefix_reachable')
    base=result['base57'];L=sum(base['base']['tightened']['path_numerators'].values())
    required=integ.allocation.allocate(base['capped_prefixes'],base['shared_prefix'],forced,L,inputs['denominator'])
    integ.required_history(required,base,cov,c,cohort,'prefix_reachable')
    same=integ.identity(result,inputs['source_hashes'],banned)
    assert same['source_identity_sha256']==c['context61_arms'][cohort]['source_identity_sha256']
    assert same['banned_set_sha256']==c['context61_arms'][cohort]['banned_set_sha256']
    rows=integ.combine(result,required,global_identity=same,required_identity=dict(same))
    proof={'global':result,'coverage':cov,'required':required,'rows':rows}
    proof['digests']={key+'_sha256':integ.digest(value) for key,value in proof.items()}
    return proof,shape
