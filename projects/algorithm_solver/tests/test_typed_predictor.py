import unittest

import torch

from algsolve.synth import typed_codec, typed_development
from algsolve.synth.typed_prediction_codec import PredictionCodec, OPS, INPUTS, BITS
from algsolve.synth.typed_predictor import TypedPredictor, decisions, per_example_loss
from algsolve.synth.train_typed import signature


class TypedPredictorTests(unittest.TestCase):
    def test_parallel_heads_loss_and_exact_decision_roundtrip(self):
        torch.set_num_threads(1)
        graph=typed_development.proposed()[0]['program']
        encoding=PredictionCodec.fit([{'learning_split':'development_fit','target':typed_codec.encode(graph,'fixture')}])
        labels={k:torch.tensor([v]) for k,v in encoding.encode(graph).items()}
        model=TypedPredictor(16,encoding.slots,len(encoding.types),width=16)
        logits=model(torch.randn(1,16),torch.randn(1,4,16))
        loss=per_example_loss(logits,labels)
        self.assertEqual(tuple(loss.shape),(1,)); self.assertTrue(torch.isfinite(loss).all())
        loss.sum().backward()
        self.assertTrue(all(p.grad is not None for p in model.parameters()))
        exact={}
        for k,v in logits.items():
            if k=='bits': exact[k]=labels[k].clamp_min(0).float()*20-10
            else:
                exact[k]=torch.full_like(v,-10.)
                exact[k].scatter_(-1,labels[k].clamp_min(0).unsqueeze(-1),10.)
        decoded=encoding.decode(decisions(exact),graph['parameters'])
        self.assertEqual(typed_codec.encode(decoded,'fixture')['expanded_sha256'],typed_codec.encode(graph,'fixture')['expanded_sha256'])

    def test_signature_body_is_not_embedded(self):
        pair={'input':{'starter_code':'class Solution:\n    def solve(self, nums: list[int]) -> int:\n        return 123456789\n'}}
        method,source=signature(pair)
        self.assertEqual(method,'solve'); self.assertNotIn('123456789',source); self.assertIn('pass',source)

    def test_bodyless_imported_starter_is_accepted_without_changing_signature(self):
        pair={'input':{'starter_code':'class Solution:\n    def solve(self, nums: List[int]) -> int:\n        '}}
        method,source=signature(pair)
        self.assertEqual(method,'solve'); self.assertIn('nums: List[int]',source); self.assertIn('pass',source)


if __name__=='__main__': unittest.main()
