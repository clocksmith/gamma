"""Owned-vector successor: synthetic development fixtures, no corpus/case access."""
import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from algsolve.synth import typed_program as legacy, typed_recipes as legacy_recipes
from algsolve.synth import typed_vector_program as ir, typed_vector_recipes as r
from algsolve.synth import typed_vector_codec as codec
from algsolve.synth.typed_experiment import cases


def measured(runtime, recipe_module, name, values):
    meters = []
    class Meter(runtime.Budget):
        def __init__(self, remaining):
            super().__init__(remaining)
            self.initial = remaining
            meters.append(self)
    with patch.object(runtime, 'Budget', Meter):
        value = runtime.execute(recipe_module.fixtures()[name], {'values': values},
                                recipes=recipe_module.catalog(), budget=1000000000)
    return value, meters[0].initial - meters[0].remaining


class VectorTests(unittest.TestCase):
    def test_all_authored_synthetic_fixtures_and_inlining(self):
        catalog = r.catalog()
        fixtures = r.fixtures()
        expanded = {k: ir.expanded(p, catalog) for k, p in fixtures.items()}
        for row in cases():
            args = copy.deepcopy(row['input'])
            self.assertEqual(ir.execute(fixtures[row['fixture']], args, recipes=catalog), row['expected'])
            graph, names = expanded[row['fixture']]
            self.assertEqual(ir.execute(graph, {names[k]: v for k, v in args.items()}), row['expected'])
            self.assertEqual(args, row['input'])

    def test_snapshot_has_value_semantics_and_fresh_calls(self):
        p = r.program({}, [r.call('vector.new', 'v'),
            r.call('vector.append', 'first', r.ref('v'), r.lit(7)),
            r.call('vector.snapshot', 'before', r.ref('v')),
            r.call('vector.append', 'second', r.ref('v'), r.lit(-3)),
            r.call('vector.snapshot', 'after', r.ref('v'))],
            r.pure('tuple', r.ref('before'), r.ref('after')), ('tuple', ir.INTS, ir.INTS))
        first = ir.execute(p, {})
        self.assertEqual(first, ([7], [7, -3]))
        first[0].append(999)
        self.assertEqual(ir.execute(p, {}), ([7], [7, -3]))

    def test_resource_alias_escape_port_and_type_misuse(self):
        allocate = r.call('vector.new', 'v')
        invalid = [
            r.program({}, [allocate, r.assign('alias', r.ref('v'))], r.lit(0), 'int'),
            r.program({}, [allocate], r.ref('v'), 'vector_int'),
            r.program({}, [allocate], r.pure('tuple', r.ref('v')), ('tuple', 'vector_int')),
            r.program({'v': 'vector_int'}, [], r.lit(0), 'int'),
            r.program({'vs': ('list', 'vector_int')}, [], r.lit(0), 'int'),
            r.program({}, [allocate, r.call('vector.append', 'x', r.ref('v'), r.lit(True))], r.lit(0), 'int'),
            r.program({}, [allocate, r.call('heap.push', 'x', r.ref('v'), r.lit(1))], r.lit(0), 'int'),
            r.program({}, [r.call('queue.new', 'v'), r.call('vector.snapshot', 'x', r.ref('v'))], r.ref('x'), ir.INTS),
            r.program({}, [allocate, r.call('vector.new', 'v')], r.lit(0), 'int'),
            r.program({}, [allocate], r.pure('vector.snapshot', r.ref('v')), ir.INTS),
            r.program({}, [r.branch(r.lit(True), [allocate]), r.call('vector.snapshot', 'x', r.ref('v'))], r.ref('x'), ir.INTS),
        ]
        for p in invalid:
            with self.assertRaises(ir.Invalid):
                ir.validate(p)
        callee = r.program({'v': 'vector_int'}, [], r.lit(0), 'int')
        caller = r.program({}, [allocate, r.invoke('bad', 'x', r.ref('v'))], r.ref('x'), 'int')
        with self.assertRaises(ir.Invalid):
            ir.validate(caller, {'bad': callee})

    def test_capacity_and_budget_fail_before_mutation(self):
        values = [0] * ir.MAX_COLLECTION
        p = r.fixtures()['heap_sort']
        self.assertEqual(ir.execute(p, {'values': values}, recipes=r.catalog(), budget=2000000), values)
        with self.assertRaisesRegex(ir.Invalid, 'bounded collection'):
            ir.execute(p, {'values': values + [0]}, recipes=r.catalog())
        owned = [1] * ir.MAX_COLLECTION
        with self.assertRaisesRegex(ir.Invalid, 'capacity'):
            ir._effect('vector.append', [owned, 2], ir.Budget(10))
        self.assertEqual(len(owned), ir.MAX_COLLECTION)
        owned = [1]
        with self.assertRaises(ir.BudgetExceeded):
            ir._effect('vector.append', [owned, 2], ir.Budget(0))
        self.assertEqual(owned, [1])
        with self.assertRaises(ir.BudgetExceeded):
            ir._effect('vector.snapshot', [owned], ir.Budget(0))
        self.assertEqual(owned, [1])
        meter = ir.Budget(10)
        ir._effect('vector.append', [owned, 2], meter)
        self.assertEqual(meter.remaining, 9)
        snapshot = ir._effect('vector.snapshot', [owned], meter)
        self.assertEqual(meter.remaining, 7)
        self.assertIsNot(snapshot, owned)
        with self.assertRaises(ir.BudgetExceeded):
            ir.execute(p, {'values': [3, 1, 2]}, recipes=r.catalog(), budget=1)
        self.assertEqual(ir.execute(p, {'values': [3, 1, 2]}, recipes=r.catalog()), [1, 2, 3])

    def test_integer_bounds_and_effect_order(self):
        largest = (1 << ir.MAX_INTEGER_BITS) - 1
        p = r.fixtures()['heap_sort']
        for values in ([largest, -largest], [], [2, -1, 2, 0]):
            self.assertEqual(ir.execute(p, {'values': values}, recipes=r.catalog()), sorted(values))
        for values in ([True], [largest + 1], [1.5]):
            with self.assertRaises(ir.Invalid):
                ir.execute(p, {'values': values}, recipes=r.catalog())
        bad = r.program({}, [r.call('vector.append', 'a', r.ref('v'), r.lit(1)),
                            r.call('vector.new', 'v')], r.lit(0), 'int')
        with self.assertRaises(ir.Invalid):
            ir.validate(bad)

    def test_hygiene_and_recipe_composition(self):
        p = r.program({'v1': ir.INTS}, [r.invoke('heap_sort', 'v2', r.ref('v1'))], r.ref('v2'), ir.INTS)
        expanded, names = ir.expanded(p, r.catalog())
        self.assertEqual(ir.execute(expanded, {names['v1']: [3, 1, 2]}), [1, 2, 3])
        for fixture in ('sorted_unique', 'unique_sorted'):
            self.assertEqual(ir.execute(r.fixtures()[fixture], {'values': [3, -1, 3, 2]}, recipes=r.catalog()), [-1, 2, 3])
        for recipe in ('heap_sort', 'stable_unique'):
            counts = ir.operation_counts(r.catalog()[recipe])
            self.assertNotIn('append', counts)
            self.assertEqual(counts['vector.append'], 1)
            self.assertEqual(counts['vector.snapshot'], 1)

    def test_counted_growth_removes_quadratic_accumulation(self):
        for recipe in ('heap_sort', 'stable_unique'):
            old, new = [], []
            for n in (128, 256, 512):
                values = list(range(n, 0, -1))
                expected = sorted(values) if recipe == 'heap_sort' else values
                for runtime, recipes, results in ((legacy, legacy_recipes, old), (ir, r, new)):
                    result, steps = measured(runtime, recipes, recipe, values)
                    self.assertEqual(result, expected)
                    results.append(steps)
            self.assertGreater(old[-1] / old[-2], 3)
            self.assertLess(new[-1] / new[-2], 2.3)
            self.assertLess(new[-1], old[-1])

    def test_adapter_runtime_names_and_unicode_normalization(self):
        for name in ('execute', 'json', 'Solution', 'Budget', 'recipes'):
            p = r.program({name: ir.INTS}, [], r.ref(name), ir.INTS)
            source = codec.render(codec.encode(p, 'fixture'), 'fixture', method='solve', params=[name])
            namespace = {'__name__': 'synthetic_vector_fixture'}
            exec(source, namespace)
            self.assertEqual(namespace['Solution']().solve([1, 2]), [1, 2])
        for params, method in [(['K', 'K'], 'solve'), (['ｆｏｒ'], 'solve'),
                               (['K'], 'K'), (['self'], 'solve'), (['x'], 'ｄｅｆ')]:
            p = r.program({name: 'int' for name in params}, [], r.ref(params[0]), 'int')
            with self.assertRaises(ir.Invalid):
                codec.render(codec.encode(p, 'fixture'), 'fixture', method=method, params=params)

    def test_codec_schema_drift_framing_and_standalone_storage(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'codec.json'
            path.write_text(ir.canonical(codec.descriptor()))
            identity = codec.frozen(path)
            p = r.fixtures()['heap_sort']
            target = codec.encode(p, identity)
            self.assertEqual(codec.decode(json.loads(ir.canonical(target)), identity), p)
            corrupt = copy.deepcopy(target)
            corrupt['expanded_sha256'] = 'changed'
            with self.assertRaises(ir.Invalid):
                codec.decode(corrupt, identity)
            with self.assertRaises(ir.Invalid):
                codec.decode(target, 'wrong-codec')
            data = json.loads(path.read_text())
            data['vector_contract']['capacity'] += 1
            path.write_text(ir.canonical(data))
            with self.assertRaises(ir.Invalid):
                codec.frozen(path)
            source = codec.render(target, identity, method='solve', params=['values'])
            namespace = {'__name__': 'synthetic_vector_fixture'}
            exec(source, namespace)  # Repository-authored synthetic fixture only.
            values = [3, -1, 3, 2]
            self.assertEqual(namespace['Solution']().solve(values), sorted(values))
            self.assertEqual(values, [3, -1, 3, 2])
            costs = codec.storage_costs(target, identity, method='solve', params=['values'])
            self.assertEqual(costs['standalone_source_bytes'], len(source.encode()))
            self.assertEqual(costs['target_bytes'], len(ir.canonical(target).encode()))
            self.assertIsNone(costs['input_presses'])
            with self.assertRaises(legacy.Invalid):
                legacy.validate(p, legacy_recipes.catalog())
            with self.assertRaises(ir.Invalid):
                ir.validate(legacy_recipes.fixtures()['heap_sort'], r.catalog())


if __name__ == '__main__':
    unittest.main()
