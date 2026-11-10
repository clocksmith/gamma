"""Finite authored controls only; no protected tasks, source corpus or model."""
import copy
import unittest

from algsolve.synth import typed_prediction_codec as prediction
from algsolve.synth import typed_recipes as fixture
from algsolve.synth import typed_stream_contract as contract
from algsolve.synth import typed_word_codec as word
from algsolve.synth import typed_vector_program as vector


def predictor(program, slots=512):
    _, types = prediction.flatten(program)
    return prediction.PredictionCodec(slots, sorted(set(types)))


class TypedStreamContractTests(unittest.TestCase):
    def assert_partition(self, packet):
        report = contract.ledger(packet)
        categories = report['categories']
        self.assertEqual(sum(v['selections'] for v in categories.values()), report['costs']['selections'])
        self.assertEqual(sum(v['bits'] for v in categories.values()), report['costs']['payload_bits'])
        self.assertEqual(report['costs']['packet_bits'], report['costs']['payload_bits'] +
                         report['costs']['framing_bits'] + report['costs']['padding_bits'])
        profile, _, indices = word._unpack(packet)
        self.assertEqual([e['code'] for e in report['trace']], indices)
        self.assertEqual([e['word'] for e in report['trace']], [word.vocabulary(profile)[i] for i in indices])
        return report

    def test_concrete_mapping_distinguishes_frozen_profiles(self):
        descriptor = contract.descriptor()
        self.assertEqual(descriptor['prediction_labels'], 43)
        self.assertEqual(descriptor['profiles']['base-v2']['entries'], 53)
        self.assertEqual(descriptor['profiles']['vector-v1']['entries'], 57)
        self.assertEqual(set(descriptor['vector_only_words']),
                         {'E:vector.new', 'E:vector.append', 'E:vector.snapshot', 'T:vector_int'})
        rows = descriptor['prediction_mapping']
        self.assertEqual([r['prediction_label'] for r in rows], prediction.OPS)
        for row in rows:
            for profile, codes in row['word_codes'].items():
                self.assertEqual([word.vocabulary(profile)[c] for c in codes], row['word_tokens'])
        for row in rows:
            if row['prediction_label'].startswith('recipe:') or row['prediction_label'] == 'EMPTY':
                self.assertEqual(row['word_tokens'], [])

    def test_constant_ledger_has_no_free_literal_bits(self):
        program = fixture.program({}, [], fixture.lit(-257), 'int')
        for width in (6, 7, 8):
            packet, _ = word.encode(program, width)
            report = self.assert_partition(packet)
            self.assertEqual(report['categories'], {
                'operations': {'selections': 0, 'bits': 0},
                'bindings': {'selections': 0, 'bits': 0},
                'structure': {'selections': 6, 'bits': 6 * width},
                'constants': {'selections': 12, 'bits': 12 * width},
                'types': {'selections': 1, 'bits': width}})

    def test_binding_numerals_and_structure_numerals_are_separate(self):
        program = fixture.program({'x': 'int'}, [
            fixture.assign('answer', fixture.pure('add', fixture.ref('x'), fixture.lit(2)))],
            fixture.ref('answer'), 'int')
        packet, _ = word.encode(program, 6)
        report = self.assert_partition(packet)
        self.assertEqual(report['categories']['bindings']['selections'], 10)
        self.assertEqual(report['categories']['operations']['selections'], 2)
        self.assertEqual(report['categories']['constants']['selections'], 5)
        roles = {entry['role'] for entry in report['trace'] if entry['word'] == 'END'}
        self.assertEqual(roles, {'bindings', 'structure', 'constants'})

    def test_prediction_bridge_preserves_order_constants_and_mutable_scope(self):
        program = fixture.program({'right': 'int', 'left': 'int'}, [
            fixture.assign('total', fixture.ref('left'), 'var'),
            fixture.branch(fixture.pure('lt', fixture.ref('right'), fixture.lit(0)),
                           [fixture.assign('local', fixture.lit(7)),
                            fixture.assign('total', fixture.pure('sub', fixture.ref('total'), fixture.ref('local')), 'set')],
                           [fixture.assign('local', fixture.lit(9)),
                            fixture.assign('total', fixture.pure('add', fixture.ref('total'), fixture.ref('local')), 'set')])],
            fixture.ref('total'), 'int')
        program['parameters'] = ['left', 'right']
        codec = predictor(program)
        codes = codec.encode(program)
        original = copy.deepcopy(codes)
        for width in (6, 7, 8):
            packet, report = contract.from_prediction(codec, codes, program['parameters'], width)
            self.assertEqual(word.execute(packet, [20, -2]), 13)
            self.assertEqual(word.execute(packet, [20, 2]), 29)
            self.assertEqual(word.decode(packet), word.canonicalize(program))
            self.assertEqual(report['raw_prediction_sha256'], contract.digest(codes))
            self.assertEqual(report['prediction_tensor']['literal_bit_fields'], prediction.BITS * codec.slots)
            self.assertIsNone(report['prediction_tensor']['wire_bits'])
            self.assert_partition(packet)
        self.assertEqual(codes, original)

    def test_all_recipe_fixtures_expand_and_reverse_without_refolding(self):
        for name, program in fixture.fixtures().items():
            with self.subTest(name=name):
                codec = predictor(program)
                packet, report = contract.from_prediction(codec, codec.encode(program), program['parameters'])
                self.assertEqual(word.decode(packet), word.canonicalize(program, recipes=fixture.catalog()))
                self.assertGreater(report['costs']['selections'], report['prediction_tensor']['active_nodes'])
                reverse, params = contract.to_prediction(packet, codec)
                labels = [prediction.OPS[code] for code in reverse['op']]
                self.assertFalse(any(label.startswith('recipe:') for label in labels))
                self.assertEqual(contract.from_prediction(codec, reverse, params)[0], packet)
                self.assert_partition(packet)

    def test_recipe_execution_and_repeated_expansion_cost(self):
        recipe = fixture.program({'values': ['list', 'int']}, [
            fixture.invoke('stable_unique', 'first', fixture.ref('values')),
            fixture.invoke('stable_unique', 'second', fixture.ref('first'))], fixture.ref('second'), ['list', 'int'])
        codec = predictor(recipe)
        packet, report = contract.from_prediction(codec, codec.encode(recipe), recipe['parameters'])
        self.assertEqual(word.execute(packet, [[3, 1, 3, -5, 1]]), [3, 1, -5])
        self.assertEqual(report['costs']['word_counts']['E:map.new'], 2)
        self.assertEqual(report['costs']['word_counts']['E:queue.new'], 2)

    def test_integer_boundaries_and_boolean_are_not_coerced(self):
        for value in (0, 1, -1, (1 << 128) - 1, -((1 << 128) - 1), True, False):
            with self.subTest(value=value):
                program = fixture.program({}, [], fixture.lit(value), 'bool' if type(value) is bool else 'int')
                codec = predictor(program)
                packet, report = contract.from_prediction(codec, codec.encode(program), [])
                result = word.execute(packet, [])
                self.assertEqual(result, value)
                self.assertIs(type(result), type(value))
                if type(value) is bool:
                    self.assertEqual(report['categories']['constants']['selections'], 1)
                self.assert_partition(packet)

    def test_vector_ledger_preserves_owned_snapshot_and_refuses_prediction(self):
        program = fixture.program({}, [
            fixture.call('vector.new', 'builder'), fixture.call('vector.append', 'put', fixture.ref('builder'), fixture.lit(4)),
            fixture.call('vector.snapshot', 'old', fixture.ref('builder')),
            fixture.call('vector.append', 'put2', fixture.ref('builder'), fixture.lit(9)),
            fixture.call('vector.snapshot', 'new', fixture.ref('builder'))],
            fixture.pure('tuple', fixture.ref('old'), fixture.ref('new')), ['tuple', ['list', 'int'], ['list', 'int']])
        program['schema'] = vector.SCHEMA
        for width in (6, 7, 8):
            packet, _ = word.encode(program, width, 'vector-v1')
            self.assertEqual(word.execute(packet, []), ([4], [4, 9]))
            self.assert_partition(packet)
            with self.assertRaisesRegex(ValueError, 'Vector profile'):
                contract.to_prediction(packet, prediction.PredictionCodec(512, []))
        # Even a vector-schema constant is not silently relabeled as base-v2.
        program = fixture.program({}, [], fixture.lit(1), 'int')
        program['schema'] = vector.SCHEMA
        packet, _ = word.encode(program, 6, 'vector-v1')
        with self.assertRaisesRegex(ValueError, 'Vector profile'):
            contract.to_prediction(packet, prediction.PredictionCodec(512, ['"int"']))

    def test_reverse_rejects_unfitted_type_and_inadequate_slots(self):
        program = fixture.program({'x': 'int'}, [], fixture.ref('x'), 'int')
        packet, _ = word.encode(program, 6)
        with self.assertRaises(ValueError):
            contract.to_prediction(packet, prediction.PredictionCodec(512, ['"bool"']))
        with self.assertRaisesRegex(ValueError, 'slot budget'):
            contract.to_prediction(packet, prediction.PredictionCodec(1, ['"int"']))

    def test_word_stream_can_have_more_inputs_than_predictor(self):
        inputs = {'input' + str(i): 'int' for i in range(9)}
        program = fixture.program(inputs, [], fixture.ref('input8'), 'int')
        packet, _ = word.encode(program, 6)
        self.assertEqual(word.execute(packet, list(range(9))), 8)
        self.assert_partition(packet)
        with self.assertRaisesRegex(ValueError, 'Too many prediction inputs'):
            contract.to_prediction(packet, prediction.PredictionCodec(512, ['\"int\"']))

    def test_malformed_prediction_and_stream_fail_without_repair(self):
        program = fixture.program({'x': 'int'}, [], fixture.ref('x'), 'int')
        codec = predictor(program)
        codes = codec.encode(program)
        codes['first'][0] = 1
        with self.assertRaises(ValueError):
            contract.from_prediction(codec, codes, ['x'])
        packet, _ = word.encode(program, 6)
        for invalid in (packet[:-1], packet + b'\x00'):
            with self.assertRaises(ValueError):
                contract.ledger(invalid)


if __name__ == '__main__':
    unittest.main()
