import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('dispatch', ROOT/'tools/fx2_weight_adaptive_dispatch_v1.py')
dispatch = importlib.util.module_from_spec(spec)
spec.loader.exec_module(dispatch)


class DispatchPatchTest(unittest.TestCase):
    def test_rejects_changed_or_unidentified_source(self):
        for source in (b'', b'GFX2MAR1', b'GFX2ADM1'):
            with self.assertRaises(ValueError):
                dispatch.patch(source)

    def test_exact_parent_and_one_production_condition(self):
        source = (ROOT/'results/fx2_weight_adaptive_loader_gate_v1/attempt01/D/cpp_infer/src/opt/arena_build.cpp').read_bytes()
        output = dispatch.patch(source)
        self.assertEqual(output.count(b'GFX2ADM1'), 1)
        self.assertEqual(output.replace(b' ||\n                    std::memcmp(magic, "GFX2ADM1", 8) == 0', b''), source)
        with self.assertRaises(ValueError):
            dispatch.patch(output)


if __name__ == '__main__':
    unittest.main()
