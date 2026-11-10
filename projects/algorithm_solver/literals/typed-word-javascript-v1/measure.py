"""Reproduce authored JavaScript backend evidence, without accessing a corpus.

This only runs source emitted from the finite graphs declared below. It neither
invokes nor replaces Gamma's native judge and never creates solution receipts.
"""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile

PROJECT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT))
from algsolve.synth import typed_word_codec as codec
from algsolve.synth import typed_word_javascript as javascript
from algsolve.synth import typed_vector_recipes as recipes


def ref(name): return {'ref': name}
def lit(value): return {'literal': value}
def pure(name, *args): return {'op': name, 'args': list(args)}
def bind(name, value, kind='let'): return {'op': kind, 'name': name, 'value': value}
def call(name, out, *args): return {'op': 'call', 'operator': name, 'out': out, 'args': list(args)}
def graph(profile, inputs, body, answer, output='int'):
    return {'schema': codec.runtime(profile).SCHEMA, 'parameters': list(inputs),
            'inputs': inputs, 'body': body, 'return': answer, 'output_type': output}


def js_value(value):
    if type(value) is int: return str(value) + 'n'
    if type(value) in (list, tuple): return '[' + ','.join(js_value(v) for v in value) + ']'
    return json.dumps(value, allow_nan=False)


def tagged(value):
    if type(value) is int: return {'integer': str(value)}
    if type(value) in (list, tuple): return [tagged(v) for v in value]
    return value


def fixtures():
    yield 'signed_128_bit', 'base-v2', graph('base-v2', {}, [], lit(-((1 << 128) - 1))), [], -((1 << 128) - 1), None
    yield 'mutable_sum', 'base-v2', graph('base-v2', {'values': ['list', 'int']}, [
        bind('sum', lit(0), 'var'), {'op': 'for', 'item': 'item', 'in': ref('values'),
        'body': [bind('sum', pure('add', ref('sum'), ref('item')), 'set')]}], ref('sum')), [[4, -2, 9]], 11, None
    yield 'map_zero_default', 'base-v2', graph('base-v2', {}, [
        call('map.new', 'map'), call('map.set', 'set', ref('map'), lit(3), lit(0)),
        call('map.get', 'found', ref('map'), lit(3), lit(99))], ref('found')), [], 0, None
    yield 'vector_snapshot', 'vector-v1', graph('vector-v1', {}, [
        call('vector.new', 'builder'), call('vector.append', 'first', ref('builder'), lit(4)),
        call('vector.snapshot', 'old', ref('builder')), call('vector.append', 'second', ref('builder'), lit(9)),
        call('vector.snapshot', 'new', ref('builder'))], pure('tuple', ref('old'), ref('new')),
        ['tuple', ['list', 'int'], ['list', 'int']]), [], ([4], [4, 9]), None
    examples = recipes.fixtures()
    inputs = [4, [[0, 1, 3], [1, 2, -2], [0, 2, 4], [2, 2, 99]]]
    for key, expected in (('minimum_forest', 1), ('maximum_forest', 7), ('component_count', 2), ('rejected_edge_weight', 103)):
        yield key, 'vector-v1', examples[key], inputs, expected, recipes.catalog()
    values = [4, -1, 4, 0, -1, 1 << 100]
    for key, expected in (('heap_sort', [-1, -1, 0, 4, 4, 1 << 100]),
                          ('stable_unique', [4, -1, 0, 1 << 100]),
                          ('sorted_unique', [-1, 0, 4, 1 << 100]),
                          ('unique_sorted', [-1, 0, 4, 1 << 100])):
        yield key, 'vector-v1', examples[key], [values], expected, recipes.catalog()


def measure():
    rows = []
    imports = []
    invocations = []
    expected_results = []
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        for label, profile, program, inputs, expected, recipe_map in fixtures():
            for width in (6, 7, 8):
                packet, _ = codec.encode(program, width, profile, recipe_map)
                source, receipt = javascript.emit(packet)
                if codec.execute(packet, inputs) != expected:
                    raise RuntimeError('Python authored expected-result mismatch: ' + label)
                index = len(rows)
                (root / f'program{index}.mjs').write_text(source, encoding='utf-8')
                imports.append(f'import {{solve as solve{index}}} from "./program{index}.mjs";')
                invocations.append(f'dump(solve{index}({js_value(inputs)}));')
                expected_results.append(tagged(expected))
                ir = codec.runtime(profile)
                canonical = codec.decode(packet)
                rows.append({'fixture': label, **receipt,
                    'canonical_graph_sha256': hashlib.sha256(ir.canonical(canonical).encode()).hexdigest(),
                    'python_authored_expected_result_passed': True,
                    'javascript_authored_expected_result_passed': True})
        runner = '\n'.join(imports + [
            'const dump=x=>console.log(JSON.stringify(x,(_k,v)=>typeof v==="bigint"?{integer:String(v)}:v));'
        ] + invocations)
        (root / 'run.mjs').write_text(runner, encoding='utf-8')
        result = subprocess.run(['node', str(root / 'run.mjs')], capture_output=True, text=True, timeout=20, check=True)
        observed = [json.loads(line) for line in result.stdout.splitlines()]
        if observed != expected_results:
            raise RuntimeError('JavaScript authored expected-result mismatch')
    packages = []
    descriptors = {p: codec.descriptor(p) for p in codec.PROFILES}
    support = rows[0]['emission_support_bytes']
    for width in (6, 7, 8):
        selected = [r for r in rows if r['width'] == width]
        packet_bytes = sum(r['packet_cost']['packet_bits'] // 8 for r in selected)
        shared_bytes = (support['python_decoder'] + support['javascript_emitter'] + support['javascript_runtime'] +
                        support['python_package_initializers'] +
                        sum(d['dictionary_bytes'] + d['runtime_source_bytes'] for d in descriptors.values()))
        packages.append({'width': width, 'authored_graphs': len(selected), 'packet_bytes': packet_bytes,
                         'shared_emission_toolchain_bytes': shared_bytes,
                         'packet_package_bytes': packet_bytes + shared_bytes,
                         'standalone_modules_bytes': sum(r['standalone_javascript_source_bytes'] for r in selected),
                         'accounting': 'Shared compiler/runtime support counted once per packet package. Standalone modules each embed their runtime and are an alternative representation, not an additional charge.'})
    return {'schema': 'algsolve.typed-word-javascript-authored-measurement.v1', 'fixture_count': 12,
            'rows': rows, 'packages': packages,
            'node_version': subprocess.run(['node', '--version'], capture_output=True, text=True, check=True).stdout.strip(),
            'python_version': sys.version.split()[0],
            'measurement_source_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            'evidence_scope': '12 authored graphs at three widths, Python/JavaScript expected-result checks. No catalogue coverage, native qualification, unseen scoring, or autonomous solving.',
            'integer_interface': 'JavaScript BigInt, Python int, magnitude at most 128 bits. Number conversion and ordinary LeetCode adapters are not included.',
            'width_comparison': 'Same 53/57 entries at every width; no richer 7/8-bit vocabulary or width advantage claimed.'}


if __name__ == '__main__':
    print(json.dumps(measure(), indent=2, sort_keys=True))
