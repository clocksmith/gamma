"""Rebuild finite authored bridge evidence; no model, corpus or protected inputs."""
import hashlib
import json
from pathlib import Path
import sys

PROJECT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT))
from algsolve.synth import typed_prediction_codec as prediction
from algsolve.synth import typed_recipes as fixture
from algsolve.synth import typed_stream_contract as contract
from algsolve.synth import typed_word_codec as word


def fixtures():
    yield 'signed_constant', fixture.program({}, [], fixture.lit(-257), 'int'), [], -257
    yield 'mutable_sum', fixture.program({'values': ['list', 'int']}, [
        fixture.assign('total', fixture.lit(0), 'var'),
        fixture.each('item', fixture.ref('values'), [
            fixture.assign('total', fixture.pure('add', fixture.ref('total'), fixture.ref('item')), 'set')])],
        fixture.ref('total'), 'int'), [[4, -2, 9]], 11
    yield 'map_zero_default', fixture.program({}, [
        fixture.call('map.new', 'mapping'),
        fixture.call('map.set', 'written', fixture.ref('mapping'), fixture.lit(3), fixture.lit(0)),
        fixture.call('map.get', 'found', fixture.ref('mapping'), fixture.lit(3), fixture.lit(99))],
        fixture.ref('found'), 'int'), [], 0
    yield 'repeated_recipe', fixture.program({'values': ['list', 'int']}, [
        fixture.invoke('stable_unique', 'first', fixture.ref('values')),
        fixture.invoke('stable_unique', 'second', fixture.ref('first'))],
        fixture.ref('second'), ['list', 'int']), [[3, 1, 3, -5, 1]], [3, 1, -5]


def measure():
    rows = []
    for name, program, inputs, expected in fixtures():
        _, types = prediction.flatten(program)
        codec = prediction.PredictionCodec(512, sorted(set(types)))
        codes = codec.encode(program)
        direct = prediction.ir.execute(program, dict(zip(program['parameters'], inputs)), recipes=fixture.catalog())
        if direct != expected:
            raise ValueError('Authored direct execution differs: ' + name)
        for width in (6, 7, 8):
            packet, report = contract.from_prediction(codec, codes, program['parameters'], width)
            reverse, params = contract.to_prediction(packet, codec)
            if contract.from_prediction(codec, reverse, params, width)[0] != packet:
                raise ValueError('Primitive packet roundtrip differs: ' + name)
            if word.execute(packet, inputs) != expected:
                raise ValueError('Authored packet execution differs: ' + name)
            rows.append({'fixture': name, 'profile': 'base-v2', 'width': width,
                         'packet_hex': packet.hex(), 'packet_sha256': report['packet_sha256'],
                         'canonical_program_sha256': report['canonical_program_sha256'],
                         'categories': report['categories'], 'costs': report['costs'],
                         'prediction_tensor': report['prediction_tensor'],
                         'prediction_descriptor': codec.descriptor(),
                         'prediction_codes_sha256': contract.digest(codes),
                         'input_parameters': program['parameters'], 'positional_inputs': inputs,
                         'authored_expected': expected, 'execution_matches': True,
                         'primitive_packet_roundtrip_exact': True})
    # The vector profile remains independently measured, not converted to base.
    program = fixture.program({}, [
        fixture.call('vector.new', 'builder'),
        fixture.call('vector.append', 'first', fixture.ref('builder'), fixture.lit(4)),
        fixture.call('vector.snapshot', 'old', fixture.ref('builder')),
        fixture.call('vector.append', 'second', fixture.ref('builder'), fixture.lit(9)),
        fixture.call('vector.snapshot', 'new', fixture.ref('builder'))],
        fixture.pure('tuple', fixture.ref('old'), fixture.ref('new')), ['tuple', ['list', 'int'], ['list', 'int']])
    program['schema'] = word.runtime('vector-v1').SCHEMA
    for width in (6, 7, 8):
        packet, _ = word.encode(program, width, 'vector-v1')
        report = contract.ledger(packet)
        if word.execute(packet, []) != ([4], [4, 9]):
            raise ValueError('Owned snapshots differ')
        try:
            contract.to_prediction(packet, prediction.PredictionCodec(512, []))
        except ValueError:
            pass
        else:
            raise ValueError('Unsupported vector prediction was accepted')
        rows.append({'fixture': 'owned_vector_snapshot', 'profile': 'vector-v1', 'width': width,
                     'packet_hex': packet.hex(), 'packet_sha256': hashlib.sha256(packet).hexdigest(),
                     'categories': report['categories'], 'costs': report['costs'],
                     'positional_inputs': [], 'authored_expected': [[4], [4, 9]],
                     'execution_matches': True, 'prediction_conversion': 'rejected: incompatible runtime profile'})
    return {'schema': 'algsolve.typed-stream-authored-evidence.v1',
            'evidence_scope': 'Five authored fixtures at three widths. Predictor codes are supplied '
                              'perfect graph encodings, not model predictions. No protected/source '
                              'evaluation, native qualification, human measurement or solver result.',
            'contract': contract.descriptor(), 'rows': rows,
            'measurement_source_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}


if __name__ == '__main__':
    print(json.dumps(measure(), sort_keys=True, indent=2))
