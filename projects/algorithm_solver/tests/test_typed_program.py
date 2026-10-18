import copy
import unittest

from algsolve.synth import typed_program as ir
from algsolve.synth import typed_recipes as r
from algsolve.synth.typed_experiment import cases, shared_fragments, alpha_fragment


class TypedProgramTests(unittest.TestCase):
    def test_recipes_and_expansions_match_independent_oracles(self):
        catalog, fixtures = r.catalog(), r.fixtures()
        expanded = {k: ir.expanded(p, catalog) for k, p in fixtures.items()}
        for row in cases():
            with self.subTest(fixture=row['fixture'], arguments=row['input']):
                p = fixtures[row['fixture']]
                before = copy.deepcopy(row['input'])
                self.assertEqual(ir.execute(p, row['input'], recipes=catalog), row['expected'])
                inline, names = expanded[row['fixture']]
                self.assertNotIn('recipe', ir.operation_counts(inline))
                self.assertEqual(ir.execute(inline, {names[k]: v for k, v in row['input'].items()}), row['expected'])
                self.assertEqual(row['input'], before)

    def test_wrong_bindings_and_conditions_have_real_counterexamples(self):
        for _, p, args, expected in r.negative_fixtures():
            ir.validate(p)  # Type-correct does not imply task-correct.
            self.assertNotEqual(ir.execute(p, args), expected)

    def test_types_cannot_be_coerced_through_python_bool_int(self):
        p = r.program({'n': 'int'}, [], r.pure('add', r.ref('n'), r.lit(1)), 'int')
        for value in (True, '2', 1.5, 1 << 130):
            with self.assertRaises(ir.Invalid): ir.execute(p, {'n': value})
        p['return']['args'][1] = r.lit(True)
        with self.assertRaises(ir.Invalid): ir.validate(p)

    def test_unbound_wrong_ports_projection_and_branch_types_fail(self):
        for expression in (r.ref('missing'), r.pure('add', r.lit(1)),
                           r.field(r.pure('tuple', r.lit(1)), 1),
                           r.pure('field', r.pure('tuple', r.lit(1)), r.ref('index')),
                           r.pure('dsu.union', r.lit(1))):
            p = r.program({'index': 'int'}, [], expression, 'int')
            with self.assertRaises(ir.Invalid): ir.validate(p)
        p = r.program({}, [r.branch(r.lit(1), [])], r.lit(0), 'int')
        with self.assertRaises(ir.Invalid): ir.validate(p)

    def test_effect_order_and_resource_identity(self):
        p = r.program({}, [r.call('queue.new', 'q'), r.call('queue.push', 'added', r.ref('q'), r.lit(7)),
                           r.call('queue.pop', 'value', r.ref('q'))], r.ref('value'), 'int')
        self.assertEqual(ir.execute(p, {}), 7)
        p['body'][1], p['body'][2] = p['body'][2], p['body'][1]
        with self.assertRaisesRegex(ir.Invalid, 'empty queue'): ir.execute(p, {})
        p['body'][1] = r.call('heap.pop', 'value', r.ref('q'))
        with self.assertRaises(ir.Invalid): ir.validate(p)

    def test_resource_alias_and_escape_rejected(self):
        for body, answer, ty in [
            ([r.call('queue.new', 'q'), r.assign('alias', r.ref('q'))], r.lit(0), 'int'),
            ([r.call('queue.new', 'q')], r.ref('q'), 'queue_int'),
            ([r.call('queue.new', 'q')], r.pure('tuple', r.ref('q')), ('tuple', 'queue_int')),
        ]:
            with self.assertRaises(ir.Invalid): ir.validate(r.program({}, body, answer, ty))

    def test_explicit_cells_persist_across_nested_scopes_but_locals_do_not(self):
        p = r.program({'values': ir.INTS}, [r.assign('sum', r.lit(0), 'var'),
            r.each('x', r.ref('values'), [r.branch(r.pure('lt', r.lit(0), r.ref('x')),
                [r.assign('sum', r.pure('add', r.ref('sum'), r.ref('x')), 'set')])])], r.ref('sum'), 'int')
        self.assertEqual(ir.execute(p, {'values': [-1, 2, 3]}), 5)
        p['return'] = r.ref('x')
        with self.assertRaises(ir.Invalid): ir.validate(p)
        p['return'] = r.ref('sum')
        p['body'][0]['op'] = 'let'
        with self.assertRaises(ir.Invalid): ir.validate(p)

    def test_shadowing_does_not_silently_change_bindings(self):
        p = r.program({'x': 'int'}, [r.assign('x', r.lit(2))], r.ref('x'), 'int')
        with self.assertRaises(ir.Invalid): ir.validate(p)

    def test_budget_exhaustion_discards_state_and_next_run_is_fresh(self):
        p = r.heap_sort_recipe()
        args = {'values': list(range(20, 0, -1))}
        with self.assertRaises(ir.BudgetExceeded): ir.execute(p, args, budget=30)
        self.assertEqual(ir.execute(p, args), sorted(args['values']))

    def test_invalid_indices_empty_pop_and_growth_fail_closed(self):
        p = r.forest_recipe()
        for n, edges in [(-1, []), (2, [[-1, 1, 0]]), (2, [[0, 2, 0]])]:
            with self.assertRaises(ir.Invalid): ir.execute(p, {'n': n, 'edges': edges, 'descending': False})
        p = r.program({}, [r.call('heap.new', 'h'), r.call('heap.pop', 'x', r.ref('h'))], r.ref('x'), 'int')
        with self.assertRaises(ir.Invalid): ir.execute(p, {})
        p = r.program({}, [], r.pure('range', r.lit(ir.MAX_COLLECTION + 1)), ir.INTS)
        with self.assertRaises(ir.Invalid): ir.execute(p, {})
        p = r.program({}, [], r.pure('mul', r.lit(1 << 100), r.lit(1 << 100)), 'int')
        with self.assertRaises(ir.Invalid): ir.execute(p, {})

    def test_no_source_holes_or_unknown_fields(self):
        for expression in ('__import__("os")', {'python': 'sum(values)'},
                           {'op': 'eval', 'args': [r.lit(1)]}):
            with self.assertRaises(ir.Invalid):
                ir.validate(r.program({}, [], expression, 'int'))
        p = r.program({}, [], r.lit(0), 'int')
        p['source'] = 'return 0'
        with self.assertRaises(ir.Invalid): ir.validate(p)

    def test_recursive_recipes_and_port_mismatches_rejected(self):
        p = r.program({'x': 'int'}, [r.invoke('self', 'y', r.ref('x'))], r.ref('y'), 'int')
        with self.assertRaises(ir.Invalid): ir.validate(p, {'self': p})
        p = r.program({}, [r.invoke('heap_sort', 'y', r.lit(4))], r.ref('y'), ir.INTS)
        with self.assertRaises(ir.Invalid): ir.validate(p, r.catalog())

    def test_expanded_recipe_work_is_bounded_before_execution(self):
        catalog = {'leaf': r.program({'x': 'int'}, [], r.ref('x'), 'int')}
        previous = 'leaf'
        for i in range(5):
            key = f'level{i}'
            catalog[key] = r.program({'x': 'int'}, [r.invoke(previous, f'v{j}', r.ref('x'))
                                                   for j in range(6)], r.ref('v5'), 'int')
            previous = key
        with self.assertRaisesRegex(ir.Invalid, 'size limit'):
            ir.validate(catalog[previous], catalog)

    def test_expansion_is_hygienic_for_colliding_external_names(self):
        p = r.program({'v1': ir.INTS}, [r.invoke('heap_sort', 'v2', r.ref('v1'))], r.ref('v2'), ir.INTS)
        expanded, names = ir.expanded(p, r.catalog())
        self.assertEqual(ir.execute(expanded, {names['v1']: [3, 1, 2]}), [1, 2, 3])

    def test_shared_fragments_preserve_binding_connections(self):
        fragments = shared_fragments(r.catalog())
        self.assertTrue(any(set(v['recipes']) == {'forest', 'cycle_weight'} for v in fragments))
        a = [r.assign('x', r.pure('add', r.ref('a'), r.ref('b'))), r.assign('y', r.ref('x'))]
        b = [r.assign('z', r.pure('add', r.ref('p'), r.ref('q'))), r.assign('w', r.ref('z'))]
        self.assertEqual(alpha_fragment(a), alpha_fragment(b))
        b[-1]['value'] = r.ref('p')
        self.assertNotEqual(alpha_fragment(a), alpha_fragment(b))


if __name__ == '__main__': unittest.main()
