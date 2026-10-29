"""Focused intake safety checks, using synthetic public-metadata fixtures."""
import unittest
from bank import collect_category, Overlap, variant_rows

class IntakeTests(unittest.TestCase):
    def fetcher(self, pages):
        iterator = iter(pages)
        return lambda url: (next(iterator), 'fixture-hash')

    def page(self, number, total, ids):
        return {'status': {'code': 200}, 'data': {'page': number, 'total': total,
                'data': [{'id': i, 'type': 'ALGORITHM'} for i in ids]}}

    def test_complete_pagination(self):
        rows, receipts = collect_category('ALGORITHM', self.fetcher([
            self.page(1, 3, ['a','b']), self.page(2, 3, ['c'])]))
        self.assertEqual([r['id'] for r in rows], ['a','b','c'])
        self.assertEqual(len(receipts), 2)

    def test_bad_pagination_rejected(self):
        cases = [self.page(2, 3, ['b']), self.page(2, 3, []),
                 self.page(2, 4, ['c']), self.page(1, 3, ['c'])]
        for second in cases:
            with self.subTest(second=second), self.assertRaises(ValueError):
                collect_category('ALGORITHM', self.fetcher([self.page(1,3,['a','b']), second]))

    def test_variants_preserve_source_identity(self):
        self.assertEqual([v['id'] for v in variant_rows({'codingQuestions':[{'id':'a'},{'id':'b'}]})], ['a','b'])
        with self.assertRaises(ValueError):
            variant_rows({'codingQuestions':[{'id':'a'},{'id':'a'}]})

    def test_title_match_never_authorizes_merge(self):
        matcher=Overlap([{'id':'1','title':'Two Sum','url':'example','slug':'two-sum'}])
        exact=matcher.classify('Two Sum', 'coding')
        self.assertEqual(exact['status'],'exact_title_candidate')
        self.assertFalse(exact['merge_allowed'])
        self.assertEqual(matcher.classify('Two Sum','system-design')['status'], 'related_concept_title_candidate')
        unknown=matcher.classify('Referral Revenue System', 'coding')
        self.assertEqual(unknown['status'],'no_title_match_found')
        self.assertIn('does not establish novelty',unknown['evidence'])

if __name__ == '__main__':
    unittest.main()
