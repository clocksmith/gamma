"""Opt-in outer-order correction for the two pinned subset contracts only.

Historical tests, expected values and the shared wave helper are never edited.
This minimal correction ignores outer collection order; inner element order,
types and multiplicities retain the existing comparator's strict semantics.
"""
from dataclasses import replace
from algsolve import validate

CONTRACTS = {
    ('lcd:78', 'subsets', 'subsets'),
    ('lcd:90', 'subsets-ii', 'subsetsWithDup'),
}


def prepare(problem, raw_tests):
    identity = (problem.uid, problem.slug, problem.entry.get('method'))
    if identity not in CONTRACTS:
        raise ValueError('Unreviewed subset comparison identity')
    if not raw_tests or any(t.get('kwargs') or t.get('compare', 'return') != 'return'
                            for t in raw_tests):
        raise ValueError('Unsupported test contract')
    return [replace(test, compare='return:unordered_outer')
            for test in validate.functional_tests(raw_tests)]
