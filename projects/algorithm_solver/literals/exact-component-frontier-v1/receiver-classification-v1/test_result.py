import json
from pathlib import Path
import unittest
from closure import container_shape_upper_bound

class Tests(unittest.TestCase):
    def test_pure_math_not_container_extension(self):
        self.assertFalse(container_shape_upper_bound({'counts':{'member/global_Math/max':1}}))
    def test_map_shape_only(self):
        self.assertTrue(container_shape_upper_bound({'counts':{'member/new_Map/get':1,'constructor/new_Map':1,'global_reference/Map':1}}))
    def test_risk_excludes(self):
        self.assertFalse(container_shape_upper_bound({'counts':{'member/new_Map/get':1,'risk/reflection_property':1}}))
    def test_unknown_call_excludes(self):
        self.assertFalse(container_shape_upper_bound({'counts':{'member/new_Map/get':1,'direct/unresolved':1}}))
    def test_all209_and_actual_core_mass(self):
        r=json.loads(Path(__file__).with_name('RESULT-v1.json').read_text())
        self.assertEqual(r['scope'],dict(variants=209,owners=116,source_bytes=50555))
        self.assertEqual(len(r['controls']),18);self.assertTrue(all(x['expected']==x['observed']for x in r['controls']))
        core=r['closed_container_core_shape_upper_bound']
        self.assertEqual((core['variants'],core['owners'],core['source_bytes']),(44,22,9111))
        self.assertEqual(core['admitted'],0);self.assertFalse(core['initializer_dominance_measured'])
        self.assertFalse(r['candidate_execution']);self.assertEqual(r['additional_sources_admitted'],0)

if __name__=='__main__':unittest.main()
