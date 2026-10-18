import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from algsolve.synth import typed_codec as codec, typed_program as ir, typed_recipes as r
from algsolve.synth import typed_development as dev, typed_pairs, typed_support


class TypedCodecTests(unittest.TestCase):
    def test_explicit_signature_survives_sorted_serialization_and_expansion(self):
        recipe = r.program({'z': 'int', 'a': 'int'}, [], r.pure('sub', r.ref('z'), r.ref('a')), 'int')
        p = r.program({}, [r.invoke('difference', 'out', r.lit(9), r.lit(2))], r.ref('out'), 'int')
        payload = json.loads(ir.canonical({'program': p, 'recipes': {'difference': recipe}}))
        self.assertEqual(list(payload['recipes']['difference']['inputs']), ['a', 'z'])
        self.assertEqual(payload['recipes']['difference']['parameters'], ['z', 'a'])
        self.assertEqual(ir.execute(payload['program'], {}, recipes=payload['recipes']), 7)
        expanded, _ = ir.expanded(payload['program'], payload['recipes'])
        self.assertEqual(ir.execute(json.loads(ir.canonical(expanded)), {}), 7)
        swapped = copy.deepcopy(recipe)
        swapped['parameters'].reverse()
        self.assertNotEqual(codec.digest(recipe), codec.digest(swapped))
        self.assertEqual(ir.execute(p, {}, recipes={'difference': swapped}), -7)

    def test_signature_must_be_complete_and_unique(self):
        for signature in (['x','x'], [], ['missing']):
            p = r.program({'x':'int'}, [], r.ref('x'), 'int')
            p['parameters'] = signature
            with self.assertRaises(ir.Invalid): ir.validate(p)

    def test_map_get_zero_absence_default_and_read_only_effect(self):
        p = r.program({}, [r.call('map.new','m'), r.call('map.set','set',r.ref('m'),r.lit(1),r.lit(0)),
            r.call('map.get','present',r.ref('m'),r.lit(1),r.lit(99)),
            r.call('map.get','absent',r.ref('m'),r.lit(2),r.lit(99)),
            r.call('map.has','still_missing',r.ref('m'),r.lit(2)),
            r.call('map.has','still_present',r.ref('m'),r.lit(1))],
            r.pure('tuple',r.ref('present'),r.ref('absent'),r.ref('still_missing'),r.ref('still_present')),
            ('tuple','int','int','bool','bool'))
        self.assertEqual(ir.execute(p,{}), (0,99,False,True))
        self.assertEqual(ir.EFFECTS['map.get'][2], 'read')
        p['body'][2]['args'][-1] = r.lit(True)
        with self.assertRaises(ir.Invalid): ir.validate(p)

    def test_codec_identity_and_expansion_receipt_fail_on_drift(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp)/'codec.json'
            path.write_text(ir.canonical(codec.descriptor()))
            identity = codec.frozen(path)
            target = codec.encode(r.fixtures()['minimum_forest'],identity)
            self.assertEqual(codec.decode(json.loads(ir.canonical(target)),identity), target['program'])
            broken = copy.deepcopy(target); broken['expanded_sha256'] = 'changed'
            with self.assertRaises(ir.Invalid): codec.decode(broken,identity)
            with self.assertRaises(ir.Invalid): codec.decode(target,'other-codec')
            data = json.loads(path.read_text()); data['limits']['integer_bits'] = 64
            path.write_text(ir.canonical(data))
            with self.assertRaises(ir.Invalid): codec.frozen(path)

    def test_standalone_adapter_preserves_ports_and_has_no_oracle(self):
        p = r.program({'z':'int','a':'int'}, [], r.pure('sub',r.ref('z'),r.ref('a')), 'int')
        target = codec.encode(p,'fixture')
        source = codec.render(target,'fixture',method='solve',params=['z','a'])
        ns = {'__name__':'candidate'}
        exec(source,ns)  # fixed repository fixture, never an untrusted program
        self.assertEqual(ns['Solution']().solve(9,2),7)
        self.assertNotIn('independent_tests',source)
        with self.assertRaises(ir.Invalid): codec.render(target,'fixture',method='solve',params=['a','z'])

    def test_all_real_proposals_validate_and_pass_declared_bound_probes(self):
        for row in dev.proposed():
            with self.subTest(uid=row['uid'],variant=row['variant']):
                p=row['program']; target=codec.encode(p,'fixture')
                source=codec.render(target,'fixture',method='solve',params=p['parameters'])
                ns={'__name__':'candidate'}; exec(source,ns)
                self.assertEqual(ns['Solution']().solve(*row['bound_probe']['args']),row['bound_probe']['expected'])

    def test_forbidden_problem_rejected_before_test_access(self):
        with patch.object(typed_pairs,'load_hidden_tests',side_effect=AssertionError('leak')):
            pair, verdict=typed_pairs.qualify({'uid':'protected'}, {}, {}, 'fixture')
        self.assertIsNone(pair)
        self.assertEqual(verdict['reason'],'not_permitted_development')

    def test_support_audit_detects_missing_modes_and_family_overlap(self):
        def pair(uid,p):
            return {'uid':uid,'problem_family':uid,'pattern_sha256':typed_support.pattern(p),
                    'target':codec.encode(p,'fixture')}
        a=pair('a',r.program({'n':'int'},[],r.pure('add',r.ref('n'),r.lit(1)),'int'))
        b=pair('b',r.program({'n':'int'},[],r.pure('mul',r.ref('n'),r.lit(-2)),'int'))
        report=typed_support.audit([a],[b])
        self.assertFalse(report['all_supported'])
        self.assertIn('pure:mul',report['candidates'][0]['missing_features'])
        self.assertIn('literal:int:negative',report['candidates'][0]['missing_features'])
        report=typed_support.audit([a],[a])
        self.assertTrue(report['all_supported'])
        self.assertFalse(report['partition_eligible'])
        self.assertIn('same_problem',report['candidates'][0]['overlap'])

    def test_corpus_covers_admitted_operations_effects_resources_and_recipes(self):
        observed=set().union(*(set(typed_support.features(row['program'])) for row in dev.proposed()))
        required=({'pure:'+op for op in ir.PURE}|{'effect_operator:'+op for op in ir.EFFECTS}
                  |{'resource:'+t for t in ir.RESOURCES}|{'recipe:'+key for key in r.catalog()})
        self.assertEqual(required-observed,set())


if __name__=='__main__': unittest.main()
