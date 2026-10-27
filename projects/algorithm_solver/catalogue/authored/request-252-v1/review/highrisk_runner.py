"""Candidate subprocess: receives inputs, never expected values."""
import importlib.util
import json
import pathlib
import sys

root = pathlib.Path(sys.argv[1])
requests = json.load(sys.stdin)
modules = {}
outputs = []
for request in requests:
    pid = request['pid']
    if pid not in modules:
        spec = importlib.util.spec_from_file_location(
            f'candidate_{pid}', root / 'python' / f'{pid}.py')
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        modules[pid] = module
    args = request['args']
    original = json.dumps(args)
    value = modules[pid].solve(*args)
    outputs.append({'value': value, 'mutated': original != json.dumps(args)})
json.dump(outputs, sys.stdout)
