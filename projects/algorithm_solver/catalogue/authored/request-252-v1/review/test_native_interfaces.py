"""Independent native API validation; development evidence, not qualification."""
import copy
import datetime
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
HERE = Path(__file__).resolve().parent
NAMES = {3242: 'NeighborSum', 3408: 'TaskManager', 3484: 'Spreadsheet', 3508: 'Router'}


def load(pid):
    spec = importlib.util.spec_from_file_location(f'native_candidate_{pid}', ROOT / 'python' / f'{pid}.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main():
    with tempfile.TemporaryDirectory(prefix='gamma-native-review-') as temporary:
        case_path = Path(temporary) / 'cases.json'
        subprocess.run([sys.executable, str(HERE / 'generate_native_cases.py'), str(case_path)], check=True, capture_output=True, timeout=15)
        cases = json.loads(case_path.read_text())
        modules = {pid: load(pid) for pid in NAMES}
        instances = []
        for test in cases:
            args = copy.deepcopy(test['constructor'])
            instance = getattr(modules[test['problem_id']], NAMES[test['problem_id']])(*args)
            assert args == test['constructor'], ('constructor mutated input', test['problem_id'])
            instances.append(instance)
        calls = 0
        for step in range(max(len(test['steps']) for test in cases)):
            for i, test in enumerate(cases):
                if step >= len(test['steps']):
                    continue
                method, original_args, expected = test['steps'][step]
                args = copy.deepcopy(original_args)
                actual = getattr(instances[i], method)(*args)
                assert actual == expected, (test['problem_id'], i, step, method, actual, expected)
                assert args == original_args, ('method mutated input', method)
                calls += 1
        linked = load(3217)
        native_lists = 0
        for size in [*range(1, 65), 100000]:
            nodes = [linked.ListNode(i % 7 + 1) for i in range(size)]
            for i in range(1, size):
                nodes[i - 1].next = nodes[i]
            removed = [2, 4, 6]
            expected = [node for node in nodes if node.val not in removed]
            result = linked.modifiedList(removed, nodes[0])
            for node in expected:
                assert result is node, ('survivor identity changed', size)
                result = result.next
            assert result is None
            assert removed == [2, 4, 6]
            native_lists += 1
        python = dict(instances=len(cases), native_calls=calls, linked_identity_cases=native_lists)
        result = subprocess.run(['node', '--max-old-space-size=256', str(HERE / 'native_runner.js'), str(case_path)], check=True, capture_output=True, text=True, timeout=60)
        javascript = json.loads(result.stdout)
        assert javascript == python
    checked = {}
    for pid in [3217, *NAMES]:
        for language, suffix in [('javascript', 'js'), ('python', 'py')]:
            path = ROOT / language / f'{pid}.{suffix}'
            checked[str(path.relative_to(ROOT))] = hashlib.sha256(path.read_bytes()).hexdigest()
    receipt = dict(schema='gamma.native-api-independent-review.v1', checked_at=datetime.datetime.now(datetime.timezone.utc).isoformat(), status='passed', source_hashes=checked, python=python, javascript=javascript, independent_oracles=True, state_isolation='146 independent instances interleaved', linked_list_semantics='Survivor object identity preserved, including a 100000-node chain.', qualification='not_established', protected_cases_used=False, reference_urls={3217:'https://leetcode.com/problems/delete-nodes-from-linked-list-present-in-array/',3242:'https://leetcode.com/problems/design-neighbor-sum-service/',3408:'https://leetcode.com/problems/design-task-manager/',3484:'https://leetcode.com/problems/design-spreadsheet/',3508:'https://leetcode.com/problems/implement-router/'})
    (HERE / 'native-test-results.json').write_text(json.dumps(receipt, indent=2) + '\n')
    print(json.dumps({k:v for k,v in receipt.items() if k in ('status','python','javascript')}))


if __name__ == '__main__':
    main()
