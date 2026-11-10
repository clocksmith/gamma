"""Bounded synthetic vector-recipe evidence. No datasets, models or case loaders."""
import hashlib
import json
from pathlib import Path
import platform
import sys
import time
from unittest.mock import patch

LANE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(LANE))
from algsolve.synth import typed_program as old, typed_recipes as old_recipes
from algsolve.synth import typed_vector_program as new, typed_vector_recipes as new_recipes
from algsolve.synth import typed_vector_codec as codec


def measure(runtime, recipes, key, values):
    meters = []
    class Meter(runtime.Budget):
        def __init__(self, remaining):
            super().__init__(remaining)
            self.initial = remaining
            meters.append(self)
    started = time.perf_counter()
    with patch.object(runtime, 'Budget', Meter):
        result = runtime.execute(recipes.fixtures()[key], {'values': values},
                                 recipes=recipes.catalog(), budget=1000000000)
    seconds = time.perf_counter() - started
    expected = sorted(values) if key == 'heap_sort' else list(dict.fromkeys(values))
    if result != expected:
        raise AssertionError('Independent synthetic oracle mismatch')
    return {'operations': meters[0].initial - meters[0].remaining,
            'wall_seconds': seconds, 'correct': True,
            'result_sha256': hashlib.sha256(new.canonical(result).encode()).hexdigest()}


def main():
    rows = []
    for recipe in ('heap_sort', 'stable_unique'):
        for size in (128, 256, 512, 1024, 2048):
            values = list(range(size, 0, -1))
            rows.append({'recipe': recipe, 'size': size,
                         'legacy': measure(old, old_recipes, recipe, values),
                         'vector': measure(new, new_recipes, recipe, values)})
    descriptor = codec.descriptor()
    identity = codec.digest(descriptor)
    costs = {}
    for name in ('heap_sort', 'stable_unique'):
        target = codec.encode(new_recipes.fixtures()[name], identity)
        costs[name] = codec.storage_costs(target, identity, method='solve', params=['values'])
    source_files = [Path(m.__file__) for m in (old, old_recipes, new, new_recipes, codec)] + [Path(__file__)]
    report = {
        'schema': 'algsolve.typed-vector-synthetic-evidence.v1',
        'source_sha256': {str(p.relative_to(LANE)): hashlib.sha256(p.read_bytes()).hexdigest() for p in source_files},
        'runtime': {'python': sys.version, 'platform': platform.platform()},
        'population': 'Authored descending integer lists; synthetic development only',
        'measurement': 'One observation per arm/size, including validation and interpreter setup. Deterministic charged operations are not hardware instruction counts.',
        'execution_budget': 1000000000,
        'descriptor_sha256': identity,
        'rows': rows,
        'representation_costs': costs,
        'qualified_problems': 0,
        'limits': ['No native judge qualification or protected cases.',
                   'No broad catalogue coverage, autonomous composition or human BITS claim.',
                   'Wall times are observational, not a full performance qualification.',
                   'JSON storage is charged; no 6/7/8-bit selection claim.',
                   'Legacy frozen runtime, recipes, descriptor and receipts remain unchanged.'],
    }
    path = Path(__file__).with_name('results.json')
    path.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({'output': str(path), 'rows': len(rows), 'all_correct': True}))


if __name__ == '__main__':
    main()
