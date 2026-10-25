import copy
import unittest
from .catalogue import digest, validate


class Catalogue(unittest.TestCase):
    def fixture(self):
        universe = {'schema': 'gamma.catalogue-universe.v1', 'eligible_problem_ids': ['a', 'b'],
                    'protected_problem_ids': [], 'metadata_sha256': 'a' * 64, 'eligibility_policy': 'frozen independently of source availability'}
        interface = {'schema': 'gamma.call-interface.v1', 'entrypoint': 'solve',
                     'arguments': 'ordered-positional', 'typed_contract': 'b' * 64}
        rows, receipts = [], {}
        for pid in universe['eligible_problem_ids']:
            languages = {}
            for language in ('javascript', 'python'):
                impl = dict.fromkeys(('source_sha256', 'problem_contract_sha256', 'runtime_sha256', 'tests_sha256', 'effects_sha256'), 'b' * 64)
                impl.update(interface=interface, interface_sha256=digest(interface), status='qualified', canonical_variant_id=pid + language, provenance='synthetic test')
                receipt = {key: impl[key] for key in ('source_sha256', 'problem_contract_sha256', 'interface_sha256', 'runtime_sha256', 'tests_sha256', 'effects_sha256')}
                receipt.update(canonical_variant_id=impl['canonical_variant_id'], provenance_sha256=digest(impl['provenance']), problem_id=pid, language=language, verdict='qualified', evidence_class='normative-typed-effects', independent_verifier=True)
                rid = digest(receipt); receipts[rid] = receipt; impl['receipt_sha256'] = rid
                languages[language] = impl
            rows.append({'problem_id': pid, 'implementations': languages})
        return universe, {'schema': 'gamma.dual-language-catalogue.v1', 'universe_sha256': digest(universe), 'problems': rows}, receipts

    def test_complete_is_not_recognition(self):
        result = validate(*self.fixture()); self.assertTrue(result['complete_dual_language_catalogue']); self.assertFalse(result['recognition_1a_1b_1c_qualified'])

    def test_missing_and_protected_retained(self):
        u, c, r = self.fixture()
        c['problems'][0]['implementations']['python'] = {'status': 'protected', 'reason': 'authorization required'}
        result = validate(u, c, r); self.assertEqual(result['eligible_problems'], 2); self.assertFalse(result['complete_dual_language_catalogue'])
        del c['problems'][0]
        with self.assertRaises(ValueError): validate(u, c, r)

    def test_stale_bindings_and_missing_verifier_fail(self):
        u, c, r = self.fixture()
        with self.assertRaises(ValueError): validate(u, c, {})
        c['problems'][0]['implementations']['python']['runtime_sha256'] = 'c' * 64
        with self.assertRaises(ValueError): validate(u, c, r)

    def test_compatibility_is_not_qualification(self):
        u, c, r = self.fixture(); impl = c['problems'][0]['implementations']['python']; receipt = copy.deepcopy(r[impl['receipt_sha256']]); receipt['evidence_class'] = 'reference-compatibility'; rid = digest(receipt); r[rid] = receipt; impl['receipt_sha256'] = rid
        with self.assertRaises(ValueError): validate(u, c, r)

    def test_duplicate_and_missing_language_rejected(self):
        u, c, r = self.fixture(); c['problems'].append(c['problems'][0])
        with self.assertRaises(ValueError): validate(u, c, r)
        u, c, r = self.fixture(); del c['problems'][0]['implementations']['javascript']
        with self.assertRaises(ValueError): validate(u, c, r)

    def test_universe_protection_cannot_be_overridden(self):
        u, c, r = self.fixture(); u['protected_problem_ids'] = ['a']; c['universe_sha256'] = digest(u)
        with self.assertRaises(ValueError): validate(u, c, r)

    def test_source_payload_is_not_metadata(self):
        u, c, r = self.fixture(); c['problems'][0]['implementations']['python']['source_code'] = 'not allowed'
        with self.assertRaises(ValueError): validate(u, c, r)

    def test_variant_identity_tamper_rejected(self):
        u, c, r = self.fixture(); c['problems'][0]['implementations']['python']['canonical_variant_id'] = 'other'
        with self.assertRaises(ValueError): validate(u, c, r)

    def test_string_universe_is_not_a_list_of_ids(self):
        u, c, r = self.fixture(); u['eligible_problem_ids'] = 'ab'; c['universe_sha256'] = digest(u)
        with self.assertRaises(ValueError): validate(u, c, r)

    def test_interface_tamper_rejected(self):
        u, c, r = self.fixture(); c['problems'][0]['implementations']['javascript']['interface'] = {'entrypoint': 'other'}
        with self.assertRaises(ValueError): validate(u, c, r)

if __name__ == '__main__': unittest.main()
