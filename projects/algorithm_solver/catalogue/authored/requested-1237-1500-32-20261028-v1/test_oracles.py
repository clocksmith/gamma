import importlib.util
from pathlib import Path
import unittest

_spec = importlib.util.spec_from_file_location('gamma_1237_test_oracles', Path(__file__).with_name('oracles.py'))
_o = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_o)
reference, validate_domain, IDS = _o.reference, _o.validate_domain, _o.IDS

_cspec = importlib.util.spec_from_file_location('gamma_1237_test_cases', Path(__file__).with_name('cases.py'))
_c = importlib.util.module_from_spec(_cspec)
_cspec.loader.exec_module(_c)
build_cases = _c.build_cases


class References(unittest.TestCase):
    def test_all_cases_and_bounds(self):
        self.assertEqual(len(IDS), 32)
        for pid in IDS:
            rows = build_cases(pid, include_maximum=True)
            self.assertGreaterEqual(len(rows), 2)
            self.assertTrue(any(r['category'] == 'analytic-maximum' for r in rows))

    def test_spot_checks(self):
        self.assertEqual(reference(1237, [1, 5]), [[1, 4], [2, 3], [3, 2], [4, 1]])
        self.assertEqual(reference(1245, [[[0, 1], [0, 2]]]), 2)
        self.assertEqual(reference(1246, [[1, 3, 4, 1, 5]]), 3)
        self.assertEqual(reference(1265, [[1, 2, 3, 4]]), [4, 3, 2, 1])
        self.assertEqual(reference(1273, [7, [-1, 0, 0, 1, 2, 2, 2], [1, -2, 4, 0, -2, -1, -1]]), 2)
        self.assertEqual(reference(1278, ['abc', 2]), 1)
        self.assertEqual(reference(1302, [[1, 2, 3, 4, 5, None, 6, 7, None, None, None, None, 8]]), 15)
        self.assertEqual(reference(1428, [[[0, 0], [1, 1]]]), 0)
        self.assertEqual(reference(1448, [[3, 1, 4, 3, None, 1, 5]]), 4)
        self.assertEqual(reference(1457, [[2, 3, 1, 3, 1, None, 1]]), 2)
        self.assertEqual(reference(1469, [[1, 2, 3, None, 4]]), [4])
        self.assertEqual(reference(1474, [[1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13], 2, 3]), [1, 2, 6, 7, 11, 12])

    def test_domain_rejections(self):
        with self.assertRaises(ValueError):
            validate_domain(1237, [1, 0])
        with self.assertRaises(ValueError):
            validate_domain(1278, ['abc', 4])


if __name__ == '__main__':
    unittest.main()
