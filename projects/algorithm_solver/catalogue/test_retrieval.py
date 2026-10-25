import unittest
from . import test_catalogue
from .retrieval import KnownCatalogue


class Retrieval(unittest.TestCase):
    def test_one_identity_two_independently_bound_languages(self):
        library = KnownCatalogue(*test_catalogue.Catalogue().fixture()); value = library.retrieve('a')
        self.assertEqual(set(value['implementations']), {'javascript', 'python'})
        for language in ('javascript', 'python'):
            self.assertEqual(library.select_language(value, language)['problem_id'], 'a')

    def test_unavailable_never_redirects(self):
        u, c, r = test_catalogue.Catalogue().fixture()
        c['problems'][0]['implementations']['python'] = {'status': 'missing', 'reason': 'no authored source'}
        library = KnownCatalogue(u, c, r); value = library.retrieve('a')
        self.assertEqual(set(value['implementations']), {'javascript'})
        self.assertEqual(library.select_language(value, 'python')['status'], 'abstain')
        self.assertEqual(library.retrieve('similar a')['status'], 'abstain')

    def test_snapshot_and_return_values_do_not_mutate_registry(self):
        u, c, r = test_catalogue.Catalogue().fixture(); library = KnownCatalogue(u, c, r)
        c['problems'].clear(); value = library.retrieve('a'); value['implementations'].clear()
        self.assertEqual(len(library.retrieve('a')['implementations']), 2)

    def test_malformed_identity_abstains(self):
        library = KnownCatalogue(*test_catalogue.Catalogue().fixture())
        for identity in ([], {}, None, 123, ''):
            self.assertEqual(library.retrieve(identity)['reason'], 'invalid_problem_identity')

    def test_all_unqualified_abstains(self):
        u, c, r = test_catalogue.Catalogue().fixture()
        for language in ('javascript', 'python'):
            c['problems'][0]['implementations'][language] = {'status': 'blocked', 'reason': 'missing normative contract'}
        self.assertEqual(KnownCatalogue(u, c, r).retrieve('a')['reason'], 'no_qualified_implementation')

if __name__ == '__main__': unittest.main()
