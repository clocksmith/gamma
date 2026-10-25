import unittest
from .facet_bitset import FacetBitsetIndex
from .interpretation_gate import identity_decision


class FacetBitsets(unittest.TestCase):
    def test_missing_contract_and_query_facts_survive(self):
        index = FacetBitsetIndex(['one', 'unlimited', 'unknown'],
                 {'one': {'transactions': 'one'}, 'unlimited': {'transactions': 'unlimited'}, 'unknown': {}})
        self.assertEqual(index.candidates({}), frozenset(index.ids))
        self.assertEqual(index.candidates({'transactions': 'one'}), frozenset(('one', 'unknown')))
        self.assertEqual(index.candidates({'unstated': 'new'}), frozenset(index.ids))

    def test_catalogue_singleton_cannot_close_open_world(self):
        index = FacetBitsetIndex(['a'], {'a': {'kind': 'tree'}})
        e = index.envelope({'kind': 'tree'}, analysis_contract_sha256='a'*64,
                           query_sha256='b'*64, universe_sha256='c'*64)
        self.assertEqual(identity_decision(e)['reason'], 'outside_catalogue_interpretation_possible')

    def test_complete_4081_denominator_including_unknowns(self):
        ids = [str(i) for i in range(4081)]
        facts = {pid: {} for pid in ids}
        facts['0'] = {'return': 'string'}
        facts['1'] = {'return': 'integer'}
        index = FacetBitsetIndex(ids, facts)
        result = index.candidates({'return': 'string'})
        self.assertEqual(len(result), 4080)
        self.assertIn('4080', result)
        self.assertNotIn('1', result)

    def test_no_silent_population_omission_or_nonexclusive_sets(self):
        with self.assertRaises(ValueError):
            FacetBitsetIndex(['a','b'], {'a': {}})
        with self.assertRaises(ValueError):
            FacetBitsetIndex(['a'], {'a': {'kind': ['tree','graph']}})

    def test_exhaustive_scalar_oracle_agreement(self):
        from itertools import product
        for values in product((None,'x','y'), repeat=4):
            ids = list('abcd')
            facts = {pid: {} if value is None else {'f': value} for pid, value in zip(ids, values)}
            index = FacetBitsetIndex(ids, facts)
            for query in ('x','y','z'):
                want = frozenset(pid for pid in ids if 'f' not in facts[pid] or facts[pid]['f']==query)
                self.assertEqual(index.candidates({'f':query}), want)
