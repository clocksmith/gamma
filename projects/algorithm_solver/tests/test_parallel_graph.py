import unittest
import torch

from algsolve.synth import call_graph
from algsolve.synth.parallel_graph import Codec, ParallelGraphPredictor, supervised_loss


def pair():
    return {'learning_split': 'training', 'input': {'params': [['n','int'], ['edges','list']]},
            'target': {'schema': call_graph.SCHEMA, 'vocabulary_sha256': call_graph.vocabulary_hash(),
                       'nodes': [{'operator': 'adjacency', 'arguments': ['n','edges','True','False'], 'output': 'adj'},
                                 {'operator': 'bfs', 'arguments': ['n','adj','[0]'], 'output': 'dist'}],
                       'answer': 'max(dist)'}}


class ParallelGraphTests(unittest.TestCase):
    def test_codec_round_trip_preserves_bindings_with_renamed_inputs(self):
        original = pair()
        codec = Codec.fit([original])
        decoded = codec.decode(*codec.encode(original), params=['size','links'])
        self.assertEqual(decoded['nodes'][0]['arguments'][:2], ['size','links'])
        self.assertEqual(decoded['nodes'][1]['arguments'], ['size','value_0','[0]'])
        source = call_graph.compile_graph(decoded, method='solve', params=['size','links']).source
        namespace = {}; exec(source, namespace)
        self.assertEqual(namespace['Solution']().solve(3, [[0,1],[1,2]]), 2)

    def test_confirmation_targets_do_not_extend_template_bank(self):
        original = pair(); codec = Codec.fit([original]); old = list(codec.templates)
        original['learning_split'] = 'pattern_confirmation'
        with self.assertRaises(ValueError):
            Codec.fit([original])
        original['target']['answer'] = 'min(dist) + 723'
        with self.assertRaisesRegex(ValueError, 'absent from training'):
            codec.encode(original)
        self.assertEqual(codec.templates, old)

    def test_forward_is_parallel_differentiable_and_decoding_rejects_future_edges(self):
        torch.manual_seed(3)
        original = pair(); codec = Codec.fit([original])
        targets = tuple(t[None] for t in codec.encode(original))
        model = ParallelGraphPredictor(8, len(codec.templates), width=16)
        predicted = model(torch.ones(1,8), torch.ones(1,4,8))
        self.assertEqual(predicted[0].shape[:2], (1,3))
        loss = supervised_loss(predicted, targets)
        loss.backward()
        self.assertTrue(torch.isfinite(loss))
        self.assertIsNotNone(model.binding.weight.grad)
        components, templates, bindings = codec.encode(original)
        bindings[0,0,0] = 10
        with self.assertRaisesRegex(ValueError, 'future binding'):
            codec.decode(components, templates, bindings, ['n','edges'])


if __name__ == '__main__':
    unittest.main()
