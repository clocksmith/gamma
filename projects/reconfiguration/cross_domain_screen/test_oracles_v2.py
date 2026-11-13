"""CPU regression checks for versioned bounded sorted/lambda interpretation."""
import ast
import gzip
import json
from pathlib import Path
import unittest

import oracles
import oracles_v2
from test_oracles import RUNS, INTERVALS


class OracleV2Tests(unittest.TestCase):
    def test_non_interpreter_semantics_ast_identical(self):
        def outside(path):
            tree = ast.parse(path.read_text())
            tree.body = [n for n in tree.body if not (isinstance(n, ast.ClassDef) and n.name == "BoundedPython")]
            return ast.dump(tree, include_attributes=False)
        root = Path(__file__).parent
        self.assertEqual(outside(root / "oracles.py"), outside(root / "oracles_v2.py"))

    def test_sealed_valid_source_and_actual_behavior_errors(self):
        root = Path(__file__).parent
        sealed = json.loads(gzip.decompress((root / "screen-run-01/sealed-outputs.json.gz").read_bytes()))
        source = next(row["source"] for row in sealed["records"] if row["id"] == "python-intervals/permuted_gain")
        self.assertFalse(oracles.score("python-intervals", source)["passed"])
        self.assertTrue(oracles_v2.score("python-intervals", source)["passed"])
        self.assertFalse(oracles_v2.score("python-intervals", source.replace("s <= e", "s < e"))["passed"])
        self.assertFalse(oracles_v2.score("python-intervals", source.replace("key=lambda x: (x[0], x[1])", "key=lambda x: (x[0], x[1]), reverse=True"))["passed"])
        self.assertTrue(oracles_v2.score("python-runs", RUNS)["passed"])
        self.assertTrue(oracles_v2.score("python-intervals", INTERVALS)["passed"])

    def test_sorted_key_reverse_and_closure_semantics(self):
        for source, args, expected in [
            ("def f(items):\n return sorted(items,key=lambda x: (-x[0],x[1]),reverse=True)", [[[2,3],[1,2],[2,1]]], [[1,2],[2,3],[2,1]]),
            ("def f(items):\n return sorted(items,key=abs,reverse=True)", [[-2,1,-3]], [-3,-2,1]),
            ("def f(items):\n return sorted(items,key=None,reverse=False)", [[3,1,2]], [1,2,3]),
            ("def f(items):\n k=1\n fn=lambda x:k*x\n k=-1\n return sorted(items,key=fn)", [[1,3,2]], [3,2,1])]:
            self.assertEqual(oracles_v2.BoundedPython(source,"f",1).call(args),expected)

    def test_unsafe_unbounded_and_mutating_callbacks_rejected(self):
        for source in [
            "def f(items):\n return sorted(items,key=lambda x: open('/tmp/no','w'))",
            "def f(items):\n return sorted(items,key=lambda x: x.__class__)",
            "def f(items):\n return sorted(items,key=lambda x: items.append(x))",
            "def f(items):\n return sorted(items,key=lambda x: [0]*100000000000)",
            "def f(items):\n fn=lambda x:fn(x)\n return sorted(items,key=fn)",
            "def f(items):\n return sorted(items,key=lambda x=0:x)",
            "def f(items):\n return sorted(items,other=True)",
        ]:
            with self.subTest(source=source), self.assertRaises(Exception):
                oracles_v2.BoundedPython(source,"f",1).call([[1,2]])


if __name__ == "__main__":
    unittest.main()
