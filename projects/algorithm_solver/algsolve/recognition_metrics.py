"""Identity/correctness separated, including grouped uncertainty and failures."""
from collections import defaultdict
import math

import numpy as np


def wilson(successes, total):
    if not total:
        return None
    z = 1.959963984540054
    p = successes / total
    denominator = 1 + z*z/total
    center = (p + z*z/(2*total)) / denominator
    delta = z*math.sqrt(p*(1-p)/total + z*z/(4*total*total))/denominator
    return [max(0., center-delta), min(1., center+delta)]


def measures(items):
    total = len(items)
    if not total:
        return {'queries': 0}
    flags = ('accepted', 'accepted_and_correct', 'wrong_acceptance', 'accepted_unqualified',
             'identity_correct', 'top_five')
    result = {'queries': total, 'abstentions': sum(not r['accepted'] for r in items),
              'questions_total': sum(r['questions'] for r in items)}
    for key in flags:
        count = sum(bool(r[key]) for r in items)
        result[key] = {'count': count, 'rate': count/total, 'wilson_95': wilson(count, total)}
    retrieved = [r for r in items if r['retrieval_executed']]
    result['conditional_top_five'] = {'retrieved_queries': len(retrieved),
                                     'count': sum(r['top_five'] for r in retrieved)}
    times = [r['result']['seconds'] for r in items]
    result['warm_seconds'] = {'p50': float(np.percentile(times, 50)),
                              'p95': float(np.percentile(times, 95)), 'maximum': max(times)}
    families = defaultdict(list)
    for row in items:
        families[row['family']].append(row)
    groups = list(families.values())
    rng = np.random.default_rng(20261018)
    values = {key: [] for key in ('accepted_and_correct', 'wrong_acceptance', 'abstention', 'top_five',
                                  'questions', 'warm_p50', 'warm_p95')}
    for _ in range(2000):
        sample = [r for i in rng.integers(0, len(groups), len(groups)) for r in groups[i]]
        n = len(sample)
        for key in ('accepted_and_correct', 'wrong_acceptance', 'top_five'):
            values[key].append(sum(r[key] for r in sample)/n)
        values['abstention'].append(sum(not r['accepted'] for r in sample)/n)
        values['questions'].append(sum(r['questions'] for r in sample)/n)
        ts = [r['result']['seconds'] for r in sample]
        p50, p95 = np.percentile(ts, [50, 95])
        values['warm_p50'].append(p50)
        values['warm_p95'].append(p95)
    result['family_bootstrap_95'] = {key: [float(x) for x in np.percentile(v, [2.5, 97.5])]
                                     for key, v in values.items()}
    result['family_count'] = len(groups)
    return result


def summarize_results(rows):
    result = {'overall': measures(rows),
              'uncertainty': '95% family-cluster bootstrap, 2000 resamples, seed 20261018; Wilson marginal intervals also shown. '
                             'Descriptive resampling only for the exact library census; neither interval covers missing or weak tests.'}
    for field in ('kind', 'difficulty'):
        groups = defaultdict(list)
        for row in rows:
            groups[row[field] or 'unknown'].append(row)
        result['by_' + field] = {key: measures(items) for key, items in groups.items()}
    return result
