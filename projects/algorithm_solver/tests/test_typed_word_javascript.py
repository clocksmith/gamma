"""Authored synthetic backend tests, never a native-judge/corpus substitute."""
import copy
import hashlib
import json
from pathlib import Path
import random
import shutil
import subprocess
import tempfile
import unittest

from algsolve.synth import typed_word_codec as codec
from algsolve.synth import typed_word_javascript as javascript
from algsolve.synth import typed_vector_recipes as recipes


def ref(name): return {'ref': name}
def lit(value): return {'literal': value}
def op(name, *args): return {'op': name, 'args': list(args)}
def bind(name, value, kind='let'): return {'op': kind, 'name': name, 'value': value}
def call(name, out, *args): return {'op': 'call', 'operator': name, 'out': out, 'args': list(args)}
def graph(inputs, body, answer, output='int', profile='base-v2'):
    return {'schema': codec.runtime(profile).SCHEMA, 'parameters': list(inputs),
            'inputs': inputs, 'body': body, 'return': answer, 'output_type': output}


def js_value(value):
    if type(value) is int: return str(value) + 'n'
    if type(value) in (tuple, list): return '[' + ','.join(js_value(v) for v in value) + ']'
    return json.dumps(value, allow_nan=False)


def tagged(value):
    if type(value) is int: return {'integer': str(value)}
    if type(value) in (tuple, list): return [tagged(v) for v in value]
    return value


@unittest.skipUnless(shutil.which('node'), 'Node is required for authored JavaScript backend tests')
class TypedWordJavaScriptTests(unittest.TestCase):
    def run_source(self, source, invocation):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'program.mjs').write_text(source)
            (root / 'run.mjs').write_text(
                'import {solve,descriptor} from "./program.mjs";\n'
                'const dump=x=>console.log(JSON.stringify(x,(_k,v)=>typeof v==="bigint"?{integer:String(v)}:v));\n'
                'const capture=f=>{try{return {value:f()};}catch(e){return {error:e.name,message:e.message};}};\n'
                + invocation)
            result = subprocess.run(['node', str(root / 'run.mjs')], capture_output=True, text=True, timeout=20)
            self.assertEqual(result.returncode, 0, result.stderr)
            return [json.loads(line) for line in result.stdout.splitlines()]

    def compare(self, program, inputs, expected, profile='base-v2', recipe_map=None):
        for width in (6, 7, 8):
            with self.subTest(width=width, profile=profile):
                packet, _ = codec.encode(program, width, profile, recipe_map)
                source, receipt = javascript.emit(packet)
                self.assertEqual(codec.execute(packet, inputs, budget=2000000), expected)
                decoded = codec.decode(packet)
                ir = codec.runtime(profile)
                budget = ir.Budget(2000000)
                self.assertEqual(ir._run(decoded, copy.deepcopy(inputs), {}, budget), expected)
                spent = 2000000 - budget.remaining
                script = f'dump(capture(()=>solve({js_value(inputs)},{spent})));\n'
                if spent > 1:
                    script += f'dump(capture(()=>solve({js_value(inputs)},{spent - 1})));\n'
                results = self.run_source(source, script)
                self.assertEqual(results[0], {'value': tagged(expected)})
                if spent > 1: self.assertEqual(results[1]['error'], 'BudgetExceeded')
                self.assertEqual(receipt['standalone_javascript_source_bytes'], len(source.encode()))
                self.assertEqual(receipt['generated_source_sha256'], hashlib.sha256(source.encode()).hexdigest())
                self.assertEqual(receipt['packet_plus_emission_toolchain_bytes'],
                                 len(packet) + sum(receipt['emission_support_bytes'].values()))

    def test_scalar_bounds_boolean_and_positional_signature(self):
        for value in (0, -1, 1 << 53, (1 << 128) - 1, -((1 << 128) - 1)):
            self.compare(graph({}, [], lit(value)), [], value)
        program = graph({'right': 'int', 'left': 'int'}, [], op('sub', ref('left'), ref('right')))
        program['parameters'] = ['left', 'right']
        self.compare(program, [9, 4], 5)
        self.compare(graph({'x': 'bool'}, [], op('not', ref('x')), 'bool'), [False], True)
        self.compare(graph({'x': 'bool'}, [], op('lt', ref('x'), lit(True)), 'bool'), [False], True)

    def test_mutable_nested_scopes_and_all_arithmetic(self):
        program = graph({'values': ['list', 'int']}, [
            bind('total', lit(-7), 'var'),
            {'op': 'for', 'item': 'item', 'in': ref('values'), 'body': [
                {'op': 'if', 'condition': op('lt', lit(0), ref('item')),
                 'then': [bind('temp', op('mul', ref('item'), lit(2))), bind('total', op('add', ref('total'), ref('temp')), 'set')],
                 'else': [bind('temp', op('neg', ref('item'))), bind('total', op('add', ref('total'), ref('temp')), 'set')]}]}], ref('total'))
        self.compare(program, [[-3, 0, 4]], 4)

    def test_immutable_lists_range_tuple_and_stable_sort(self):
        program = graph({'count': 'int'}, [bind('values', op('empty_ints'), 'var'),
            {'op': 'for', 'item': 'i', 'in': op('range', ref('count')), 'body': [
                bind('values', op('append', ref('values'), op('neg', ref('i'))), 'set')]}],
            op('tuple', ref('values'), op('len', ref('values'))), ['tuple', ['list', 'int'], 'int'])
        self.compare(program, [4], ([0, -1, -2, -3], 4))
        pairs = [[10, 1], [20, 0], [30, 1], [40, 0]]
        for descending, expected in ((False, [pairs[1], pairs[3], pairs[0], pairs[2]]),
                                     (True, [pairs[0], pairs[2], pairs[1], pairs[3]])):
            sorting = graph({'pairs': ['list', ['tuple', 'int', 'int']]}, [],
                            op('sort_by', ref('pairs'), lit(1), lit(descending)), ['list', ['tuple', 'int', 'int']])
            self.compare(sorting, [pairs], expected)

    def test_map_default_presence_overwrite_and_unit(self):
        program = graph({}, [call('map.new', 'map'), call('map.set', 'set', ref('map'), lit(-9), lit(0)),
            call('map.has', 'present', ref('map'), lit(-9)), call('map.has', 'absent', ref('map'), lit(0)),
            call('map.get', 'found', ref('map'), lit(-9), lit(99)),
            call('map.get', 'missing', ref('map'), lit(0), lit(-20)),
            call('map.set', 'overwrite', ref('map'), lit(-9), lit(7)),
            call('map.get', 'changed', ref('map'), lit(-9), lit(99))],
            op('tuple', ref('present'), ref('absent'), ref('found'), ref('missing'), ref('changed'), ref('overwrite')),
            ['tuple', 'bool', 'bool', 'int', 'int', 'int', 'unit'])
        self.compare(program, [], (True, False, 0, -20, 7, None))

    def test_vector_snapshot_and_repeated_calls_own_their_values(self):
        program = graph({'x': 'int'}, [call('vector.new', 'vector'), call('vector.append', 'one', ref('vector'), ref('x')),
            call('vector.snapshot', 'old', ref('vector')), call('vector.append', 'two', ref('vector'), lit(9)),
            call('vector.snapshot', 'new', ref('vector'))], op('tuple', ref('old'), ref('new')),
            ['tuple', ['list', 'int'], ['list', 'int']], 'vector-v1')
        self.compare(program, [4], ([4], [4, 9]), 'vector-v1')
        source, _ = javascript.emit(codec.encode(program, 6, 'vector-v1')[0])
        self.assertEqual(self.run_source(source,
            'const a=solve([4n]); a[0].push(90n); a[1].push(91n); dump(solve([4n]));\n'
            'dump(capture(()=>solve([4n],2))); dump(solve([5n]));'),
            [tagged(([4], [4, 9])), {'error': 'BudgetExceeded', 'message': 'Execution operation budget exhausted'}, tagged(([5], [5, 9]))])
        identity = graph({'values': ['list', 'int']}, [], ref('values'), ['list', 'int'])
        source, _ = javascript.emit(codec.encode(identity, 6)[0])
        self.assertEqual(self.run_source(source, 'const input=[[1n,2n]]; const output=solve(input); output.push(3n); dump(input);'), [tagged([[1, 2]])])

    def test_authored_composed_recipes(self):
        examples = recipes.fixtures()
        graph_inputs = [4, [[0, 1, 3], [1, 2, -2], [0, 2, 4], [2, 2, 99]]]
        expected = {'minimum_forest': 1, 'maximum_forest': 7, 'component_count': 2, 'rejected_edge_weight': 103}
        for key, result in expected.items():
            self.compare(examples[key], graph_inputs, result, 'vector-v1', recipes.catalog())
        values = [4, -1, 4, 0, -1, (1 << 100)]
        for key in ('heap_sort', 'stable_unique', 'sorted_unique', 'unique_sorted'):
            result = sorted(values) if key == 'heap_sort' else list(dict.fromkeys(values)) if key == 'stable_unique' else sorted(set(values))
            self.compare(examples[key], [values], result, 'vector-v1', recipes.catalog())

    def test_deterministic_randomized_heap_queue_and_graph_compositions(self):
        rng = random.Random(20261110)
        for key in ('heap_sort', 'stable_unique', 'minimum_forest', 'maximum_forest'):
            program = recipes.fixtures()[key]
            invocations = []
            expected = []
            for _ in range(40):
                values = [rng.randrange(-40, 41) for _ in range(rng.randrange(50))]
                inputs = [values] if key in ('heap_sort', 'stable_unique') else [8,
                    [[rng.randrange(8), rng.randrange(8), rng.randrange(-50, 51)] for _ in range(30)]]
                packet, _ = codec.encode(program, 6, 'vector-v1', recipes.catalog())
                expected.append(tagged(codec.execute(packet, inputs)))
                invocations.append(f'dump(solve({js_value(inputs)}));')
            source, _ = javascript.emit(packet)
            self.assertEqual(self.run_source(source, '\n'.join(invocations)), expected)

    def test_input_type_arity_capacity_and_budget_fail_closed(self):
        program = graph({'x': 'int'}, [], ref('x'))
        source, _ = javascript.emit(codec.encode(program, 6)[0])
        invocations = ['solve([])', 'solve([1n,2n])', 'solve({x:1n})', 'solve([1])', 'solve([true])',
                       'solve([1n<<128n])', 'solve([-(1n<<128n)])', 'solve([null])',
                       'solve([1n],0)', 'solve([1n],true)', 'solve([1n],1n)', 'solve([1n],2000001)',
                       'solve([1n],NaN)', 'solve([1n],1.5)']
        for result in self.run_source(source, '\n'.join(f'dump(capture(()=>{x}));' for x in invocations)):
            self.assertEqual(result['error'], 'Invalid')
        nested = graph({'x': ['list', ['tuple', 'int', 'bool']]}, [], ref('x'), ['list', ['tuple', 'int', 'bool']])
        source, _ = javascript.emit(codec.encode(nested, 6)[0])
        self.assertEqual(self.run_source(source, 'dump(solve([[[1n,true]]]));'), [tagged([[1, True]])])
        for result in self.run_source(source,
            'dump(capture(()=>solve([[[1n]]]))); dump(capture(()=>solve([[[1n,0n]]])));\n'
            'dump(capture(()=>solve([Array(20001).fill([1n,true])])));'):
            self.assertEqual(result['error'], 'Invalid')

    def test_integer_overflow_empty_resources_and_invalid_bounds(self):
        programs = [graph({'x': 'int'}, [], op('add', ref('x'), lit(1))),
                    graph({'x': 'int'}, [], op('mul', ref('x'), lit(2))),
                    graph({'x': 'int'}, [], op('range', ref('x')), ['list', 'int']),
                    graph({}, [call('heap.new', 'heap'), call('heap.pop', 'empty', ref('heap'))], ref('empty')),
                    graph({}, [call('queue.new', 'queue'), call('queue.pop', 'empty', ref('queue'))], ref('empty')),
                    graph({'x': 'int'}, [call('dsu.new', 'sets', lit(3)), call('dsu.find', 'root', ref('sets'), ref('x'))], ref('root'))]
        for program, inputs in zip(programs, [[(1 << 128) - 1], [(1 << 128) - 1], [20001], [], [], [3]]):
            for width in (6, 7, 8):
                packet, _ = codec.encode(program, width)
                with self.assertRaises(ValueError): codec.execute(packet, inputs)
                source, _ = javascript.emit(packet)
                self.assertEqual(self.run_source(source, f'dump(capture(()=>solve({js_value(inputs)})));')[0]['error'], 'Invalid')

    def test_maximum_collection_and_resource_capacities(self):
        for kind in ('heap', 'queue', 'vector', 'map'):
            profile = 'vector-v1' if kind == 'vector' else 'base-v2'
            effect = 'append' if kind == 'vector' else 'set' if kind == 'map' else 'push'
            args = (ref('resource'), ref('item'), ref('item')) if kind == 'map' else (ref('resource'), ref('item'))
            fill = [call(kind + '.new', 'resource'),
                    {'op': 'for', 'item': 'item', 'in': op('range', lit(20000)),
                     'body': [call(kind + '.' + effect, 'written', *args)]}]
            program = graph({}, fill, lit(1), profile=profile)
            packet, _ = codec.encode(program, 6, profile)
            source, _ = javascript.emit(packet)
            self.assertEqual(codec.execute(packet, [], budget=2000000), 1)
            self.assertEqual(self.run_source(source, 'dump(solve([],2000000));'), [tagged(1)])
            overflow = copy.deepcopy(program)
            extra_args = (ref('resource'), lit(20000), lit(7)) if kind == 'map' else (ref('resource'), lit(20000))
            overflow['body'].append(call(kind + '.' + effect, 'overflow', *extra_args))
            packet, _ = codec.encode(overflow, 6, profile)
            with self.assertRaises(ValueError): codec.execute(packet, [], budget=2000000)
            source, _ = javascript.emit(packet)
            result = self.run_source(source, 'dump(capture(()=>solve([],2000000)));')[0]
            self.assertEqual(result['error'], 'Invalid')
            self.assertIn('capacity', result['message'])
            if kind == 'map':
                overwrite = copy.deepcopy(program)
                overwrite['body'].append(call('map.set', 'overwrite', ref('resource'), lit(0), lit(-7)))
                overwrite['body'].append(call('map.get', 'answer', ref('resource'), lit(0), lit(9)))
                overwrite['return'] = ref('answer')
                self.compare(overwrite, [], -7)

    def test_queue_drain_refill_and_boolean_sort_keys(self):
        program = graph({'values': ['list', 'int']}, [call('queue.new', 'queue'), bind('answer', lit(0), 'var'),
            {'op': 'for', 'item': 'item', 'in': ref('values'), 'body': [
                call('queue.push', 'pushed', ref('queue'), ref('item')),
                call('queue.pop', 'popped', ref('queue')),
                bind('answer', op('add', ref('answer'), ref('popped')), 'set')]},
            call('queue.size', 'size', ref('queue'))],
            op('tuple', ref('answer'), ref('size')), ['tuple', 'int', 'int'])
        self.compare(program, [list(range(200))], (19900, 0))
        pairs = [[True, 1], [False, 2], [True, 3], [False, 4]]
        program = graph({'pairs': ['list', ['tuple', 'bool', 'int']]}, [],
                        op('sort_by', ref('pairs'), lit(0), lit(True)), ['list', ['tuple', 'bool', 'int']])
        self.compare(program, [pairs], [pairs[0], pairs[2], pairs[1], pairs[3]])

    def test_packet_tampering_is_rejected_before_emission(self):
        packet, _ = codec.encode(graph({}, [], lit(3)), 6)
        for bad in (b'', packet[:-1], packet + b'\0', b'BAD!' + packet[4:]):
            with self.assertRaises(codec.Invalid): javascript.emit(bad)
        canonical = codec.canonicalize(graph({'x': 'int'}, [], ref('x')))
        canonical['return'] = ref('b900')
        bad = codec._packet(codec._encode_words(canonical, 'base-v2'), 6, 'base-v2')
        with self.assertRaises(codec.Invalid): javascript.emit(bad)

    def test_emission_is_deterministic_and_cosmetic_names_cannot_inject(self):
        first = graph({'solve': 'int'}, [bind('eval', op('add', ref('solve'), lit(3)))], ref('eval'))
        second = graph({'constructor': 'int'}, [bind('prototype', op('add', ref('constructor'), lit(3)))], ref('prototype'))
        for width in (6, 7, 8):
            left = codec.encode(first, width)[0]
            right = codec.encode(second, width)[0]
            self.assertEqual(javascript.emit(left), javascript.emit(right))
        self.compare(first, [8], 11)


if __name__ == '__main__': unittest.main()
