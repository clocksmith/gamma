"""Variant manifest integrity; reads sources as bytes and never executes them."""
from __future__ import annotations
import difflib
import hashlib
import json
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
AUTHORED = HERE.parent/'authored'


class ManifestTests(unittest.TestCase):
    def test_each_variant_is_its_frozen_original_with_one_local_edit(self):
        manifest = json.loads((HERE/'variants.json').read_text())
        self.assertEqual(manifest['schema'], 'gamma.continuation-jk-semantic-variants.v1')
        seen = set()
        for v in manifest['variants']:
            key = (v['problem_id'], v['language'], v['name']); self.assertNotIn(key, seen); seen.add(key)
            cohort = 'k' if v['problem_id'] == 3850 else 'j'; ext = 'py' if v['language'] == 'python' else 'js'
            original = (AUTHORED/f'continuation-{cohort}-20261028-v1'/v['language']/f"{v['problem_id']}.{ext}").read_bytes()
            variant = (HERE/v['path']).read_bytes()
            self.assertEqual(hashlib.sha256(original).hexdigest(), v['original_sha256'])
            self.assertEqual(hashlib.sha256(variant).hexdigest(), v['variant_sha256'])
            self.assertNotEqual(original, variant)
            changed = [line for line in difflib.unified_diff(original.decode().splitlines(), variant.decode().splitlines(), n=0)
                       if line[:1] in '+-' and not line.startswith(('+++', '---'))]
            self.assertLessEqual(len(changed), 16, key)
        self.assertEqual({v['problem_id'] for v in manifest['variants']}, {3820, 3821, 3825, 3835, 3850})


if __name__ == '__main__':
    unittest.main()
