"""Source-free ABI signatures and host packet projections; never execute candidates."""
import ast
import importlib.util
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).parent
SPEC = importlib.util.spec_from_file_location('native_continuation_cases', ROOT / 'cases.py')
cases = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(cases)


class CaseContractTests(unittest.TestCase):
    def test_official_example_and_seeded_case_counts(self):
        for pid, count in ((3709, 52), (3815, 53), (3829, 53)):
            values = cases.build_cases(pid)
            self.assertEqual(len(values), count)
            for case in values:
                self.assertTrue(cases.oracle.exact(cases.oracle.reference(pid, case['args']), case['expected']))

    def test_maximum_analytic_shapes_and_exact_numeric_bound(self):
        for pid, method_count in ((3709, 100000), (3815, 50000), (3829, 1000)):
            case = cases.maximum_case(pid)
            self.assertEqual(len(case['args'][0]), method_count + 1)
            self.assertEqual(len(case['expected']), method_count + 1)
            cases.oracle.validate(pid, case['args'])
        self.assertEqual(cases.maximum_case(3709)['expected'][-1], 99999000000000)
        self.assertLess(cases.maximum_case(3709)['expected'][-1], 2**53)

    def test_python_declared_native_signatures_match_official_metadata(self):
        contracts = json.loads((ROOT / 'contracts.json').read_text())
        for item in contracts['problems']:
            interface = item['native_interface']
            tree = ast.parse((ROOT / 'python' / f'{item["id"]}.py').read_text())
            native = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == interface['classname'])
            methods = {n.name: n for n in native.body if isinstance(n, ast.FunctionDef)}
            self.assertEqual(len(methods['__init__'].args.args), 1)
            for method in interface['methods']:
                self.assertEqual(len(methods[method['name']].args.args) - 1, len(method['params']))
            solve = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'solve')
            self.assertEqual([a.arg for a in solve.args.args], ['operation_names', 'argument_lists'])

    def test_maximum_expected_values_never_appear_in_argument_only_packet(self):
        # For the only nontrivial scalar aggregate, expected sum is host-only.
        case = cases.maximum_case(3709)
        raw = json.dumps({'args': case['args']}, separators=(',', ':')).encode()
        self.assertNotIn(str(case['expected'][-1]).encode(), raw)
        self.assertNotIn(b'expected', raw)

    def test_mutable_expected_outputs_are_not_input_argument_lists(self):
        case = cases.maximum_case(3829)
        identities = {id(case['args']), *(id(x) for x in case['args']), *(id(x) for x in case['args'][1])}
        for result in case['expected']:
            if isinstance(result, list): self.assertNotIn(id(result), identities)
        returns = [result for result in case['expected'] if isinstance(result, list)]
        self.assertEqual(len({id(x) for x in returns}), len(returns))


if __name__ == '__main__': unittest.main()
