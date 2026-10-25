import copy
import unittest
from .catalogue import digest, validate
from . import test_catalogue
from .retrieval import KnownCatalogue


class EvidencePolicy(unittest.TestCase):
    def fixture(self):
        u,c,r=test_catalogue.Catalogue().fixture(); c['schema']='gamma.dual-language-catalogue.v2'
        c['evidence_policy']={'schema':'gamma.catalogue-evidence-policy.v1','allowed_classes':['normative-typed-effects','frozen-admitted-typed-effects'],'scope_rule':'exact-bound-contract-only'}
        for row in c['problems']:
            for language,impl in row['implementations'].items():
                receipt=copy.deepcopy(r[impl['receipt_sha256']])
                kind='frozen-admitted-typed-effects' if language=='python' else 'normative-typed-effects'
                scope='Exact source and ordered interface under the hash-bound frozen admitted contract.'
                caveats=['Finite admitted-domain evidence, not proof of a broader normative domain.'] if language=='python' else []
                for key,value in [('evidence_class',kind),('contract_scope',scope),('caveats',caveats)]: impl[key]=value;receipt[key]=value
                rid=digest(receipt);r[rid]=receipt;impl['receipt_sha256']=rid
        return u,c,r

    def test_explicit_scope_returned_and_counted(self):
        u,c,r=self.fixture(); result=validate(u,c,r)
        self.assertEqual(result['qualified_by_evidence_class']['python']['frozen-admitted-typed-effects'],2)
        value=KnownCatalogue(u,c,r).retrieve('a')['implementations']['python']
        self.assertEqual(value['evidence_class'],'frozen-admitted-typed-effects');self.assertTrue(value['caveats'])

    def test_v1_does_not_silently_expand_policy(self):
        u,c,r=self.fixture();c['schema']='gamma.dual-language-catalogue.v1';del c['evidence_policy']
        with self.assertRaises(ValueError):validate(u,c,r)

    def test_normative_only_policy_rejects_admitted_class(self):
        u,c,r=self.fixture();c['evidence_policy']['allowed_classes']=['normative-typed-effects']
        with self.assertRaises(ValueError):validate(u,c,r)

    def test_scope_not_silently_broadened(self):
        u,c,r=self.fixture();c['problems'][0]['implementations']['python']['contract_scope']='all possible inputs'
        with self.assertRaises(ValueError):validate(u,c,r)

    def test_compatibility_class_cannot_be_enabled(self):
        u,c,r=self.fixture();c['evidence_policy']['allowed_classes'].append('reference-compatibility')
        with self.assertRaises(ValueError):validate(u,c,r)

if __name__=='__main__':unittest.main()
