"""Exercise original batch sources; expected outputs stay in the parent test process."""
import copy
import importlib.util
import json
from pathlib import Path
import sys


def containers(value):
    if not isinstance(value, (list, dict)):
        return set()
    children = value.values() if isinstance(value, dict) else value
    result = {id(value)}
    for child in children:
        result.update(containers(child))
    return result


def main():
    request = json.load(sys.stdin)
    pid = request['id']
    if pid not in {802, 871, 875, 1438, 1547, 2246, 2406, 2416}:
        raise ValueError('problem outside this batch')
    path = Path(__file__).parent / 'python' / f'{pid}.py'
    spec = importlib.util.spec_from_file_location(f'problem_{pid}', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    methods = (module.solve, getattr(module.Solution(), request['method']))
    results = []
    for original in request['cases']:
        values = []
        for method in methods:
            args = copy.deepcopy(original)
            before = copy.deepcopy(args)
            result = method(*args)
            if args != before:
                raise AssertionError('input mutated')
            if containers(args) & containers(result):
                raise AssertionError('output aliases input')
            values.append(result)
        if values[0] != values[1]:
            raise AssertionError('canonical and Solution entrypoints disagree')
        results.append(values[0])
    json.dump(results, sys.stdout, allow_nan=False)


if __name__ == '__main__':
    main()
