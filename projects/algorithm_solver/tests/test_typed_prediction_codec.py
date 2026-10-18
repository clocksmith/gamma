import copy
import unittest

from algsolve.synth import typed_codec, typed_development, typed_support
from algsolve.synth.typed_prediction_codec import PredictionCodec, OPS, INPUTS


class PredictionCodecTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows=typed_development.proposed()
        cls.pairs=[{'learning_split':'development_fit','target':typed_codec.encode(r['program'],'fixture')} for r in cls.rows]
        cls.codec=PredictionCodec.fit(cls.pairs)

    def test_roundtrip_preserves_every_development_graph_structure_and_binding(self):
        for row in self.rows:
            with self.subTest(uid=row['uid'],variant=row['variant']):
                codes=self.codec.encode(row['program'])
                decoded=self.codec.decode(codes,row['program']['parameters'])
                self.assertEqual(typed_support.pattern(decoded),typed_support.pattern(row['program']))
                # Literal values are not included in pattern(), so compare the
                # full canonical expanded targets as well.
                self.assertEqual(typed_codec.encode(decoded,'fixture')['expanded_sha256'],
                                 typed_codec.encode(row['program'],'fixture')['expanded_sha256'])

    def test_fit_rejects_audit_or_protected_targets(self):
        for label in ('development_audit','protected','training'):
            with self.assertRaises(ValueError): PredictionCodec.fit([{**self.pairs[0],'learning_split':label}])

    def test_cyclic_shared_unreachable_and_nontrailing_nodes_rejected(self):
        original=self.codec.encode(self.rows[0]['program'])
        def rejects(codes):
            with self.assertRaises(ValueError): self.codec.decode(codes,self.rows[0]['program']['parameters'])
        codes=copy.deepcopy(original); codes['first'][0]=1; rejects(codes)
        codes=copy.deepcopy(original); codes['first'][0]=0; rejects(codes)
        codes=copy.deepcopy(original); codes['next'][1]=2; rejects(codes)
        codes=copy.deepcopy(original); codes['op'][1]=0; rejects(codes)

    def test_literal_sign_magnitude_and_future_binding_checked(self):
        original=self.codec.encode(self.rows[0]['program'])
        slot=next(i for i,v in enumerate(original['op']) if OPS[v]=='ref')
        codes=copy.deepcopy(original); codes['binding'][slot]=INPUTS+self.codec.slots-1
        with self.assertRaises(ValueError): self.codec.decode(codes,['nums'])
        slot=next(i for i,v in enumerate(original['op']) if OPS[v]=='int')
        codes=copy.deepcopy(original); codes['bits'][slot][0]=2
        with self.assertRaises(ValueError): self.codec.decode(codes,['nums'])


if __name__=='__main__': unittest.main()
