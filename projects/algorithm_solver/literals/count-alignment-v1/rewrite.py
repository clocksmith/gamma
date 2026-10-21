"""Source-bound count alignment; transforms supplied text, never executes it."""
from __future__ import annotations

import argparse
import ast
import hashlib
import importlib.util
import json
from pathlib import Path

COMPONENTS_SHA256 = "0d2e8b07fe91acab29485d5ee516693baa58346cf7dbc435369870a03e6180d0"
COMPONENT_NAME = "integer_count_read_increment_pilot_v1"
MAX_WITNESS_BYTES = 65536

CONTRACT = '''Private built-in integer count map. read(map, key) returns the stored
nonnegative integer or zero without insertion. increment(map, key) changes only
that key by one and returns no value. Keys exclude bool/NaN/objects/strings;
JavaScript keys and values remain safe integers. No observable iteration-order
promise, aliases to input, callbacks or global state. Expected O(1) per operation;
O(u) map storage, implementation-dependent hash-table overhead. Increment depends
on read. Full helper source is included in every emitted program.'''

PY_HELPERS = '''def count_read(counts: dict[int, int], key: int) -> int:
    return counts.get(key, 0)

def count_increment(counts: dict[int, int], key: int) -> None:
    counts[key] = count_read(counts, key) + 1

'''

JS_HELPERS = '''function countRead(counts, key) {
  return counts.get(key) ?? 0;
}
function countIncrement(counts, key) {
  counts.set(key, countRead(counts, key) + 1);
}
'''

REWRITES = {
    '0781-javascript': [
        ('function countBoundedValues(values, minimumValue, maximumValue)', 'function countIntegerValues(values)'),
        ('const countsByOffset = new Array(maximumValue - minimumValue + 1).fill(0);', 'const counts = new Map();'),
        ('countsByOffset[value - minimumValue] += 1;', 'countIncrement(counts, value);'),
        ('return countsByOffset;', 'return counts;'),
        ('const countsByOffset = countBoundedValues(values, 0, 999);', 'const counts = countIntegerValues(values);'),
        ('for (let valueOffset = 0; valueOffset < countsByOffset.length; valueOffset += 1) {\n    const frequencyCount = countsByOffset[valueOffset];\n    const groupSize = valueOffset + 1;', 'for (const [key, frequencyCount] of counts) {\n    const groupSize = key + 1;'),
    ],
    '0781-python': [
        ('def count_bounded_values(values: list[int], minimum_value: int, maximum_value: int) -> list[int]:', 'def count_integer_values(values: list[int]) -> dict[int, int]:'),
        ('counts_by_offset = [0] * (maximum_value - minimum_value + 1)', 'counts = {}'),
        ('counts_by_offset[value - minimum_value] += 1', 'count_increment(counts, value)'),
        ('return counts_by_offset', 'return counts'),
        ('counts_by_offset = count_bounded_values(values, 0, 999)', 'counts = count_integer_values(values)'),
        ('for value_offset in range(len(counts_by_offset)):\n        frequency_count = counts_by_offset[value_offset]\n        group_size = value_offset + 1', 'for key, frequency_count in counts.items():\n        group_size = key + 1'),
    ],
    '0560-javascript': [
        ('const countsBySum = {\n    0: 1\n  };', 'const counts = new Map();\n  countIncrement(counts, 0);'),
        ('countsBySum[prefixSum - targetValue] || 0', 'countRead(counts, prefixSum - targetValue)'),
        ('countsBySum[prefixSum] = (countsBySum[prefixSum] || 0) + 1;', 'countIncrement(counts, prefixSum);'),
    ],
    '0560-python': [
        ('counts_by_sum = {0: 1}', 'counts = {}\n    count_increment(counts, 0)'),
        ('counts_by_sum.get(prefix_sum - target_value, 0)', 'count_read(counts, prefix_sum - target_value)'),
        ('counts_by_sum[prefix_sum] = counts_by_sum.get(prefix_sum, 0) + 1', 'count_increment(counts, prefix_sum)'),
    ],
}

WITNESS_PINS = {'0560-javascript': {'language': 'javascript', 'before_sha256': '73c8230b270cf06a5596762861f1b9e0fc73105d5ce8d14f591a880bed27e39b', 'after_sha256': '0f2476595bed9e74db42d1c8978b7940986ad95de62a94724ab7a2d1eab868fb'}, '0560-python': {'language': 'python', 'before_sha256': 'b6db6ca1befb97c5274079dc88ec546b60da96f5bb2476637cecc5e7b5615507', 'after_sha256': '2cc6e069a2083b30b12f698d79fb9e18ec065ee340c3971ed38f3d5b16756286'}, '0781-javascript': {'language': 'javascript', 'before_sha256': 'f639c7802a303a940c0539449d95988fad8087a1cab49eeab66f987c7a04147e', 'after_sha256': '17d457dcd35945e5d2b5928528d9419a85a20b7f3f92aa5fbccddfa30e67de8e'}, '0781-python': {'language': 'python', 'before_sha256': 'b29aa27070131e91e60c26f49aba21a6302b1e6bcf0cc1228dfd790cbdbbadc1', 'after_sha256': '524b6895a207e0f2ce10317c054594584144d99bca70345161e3f0b540a5186b'}}


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def register_component(registry):
    """Use the existing synth/components.py contract API, in memory only."""
    expected = {'name': COMPONENT_NAME, 'contract': CONTRACT.strip(), 'source': PY_HELPERS.strip() + '\n'}
    existing = registry.COMPONENTS.get(COMPONENT_NAME)
    if existing is not None and existing != expected:
        raise ValueError('existing component has a different contract or source')
    if existing is None:
        registry.component(COMPONENT_NAME, CONTRACT, PY_HELPERS)
    if registry.COMPONENTS[COMPONENT_NAME] != expected:
        raise ValueError('component registry contract normalization differs')
    return expected


def load_component_registry(path: Path):
    """Only import the known trusted registry implementation, not witness code."""
    if digest(path.read_bytes()) != COMPONENTS_SHA256:
        raise ValueError('component registry identity differs; review it before use')
    spec = importlib.util.spec_from_file_location('count_alignment_component_contracts', path)
    if spec is None or spec.loader is None:
        raise ValueError('component registry cannot be loaded')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    register_component(module)
    return module


def replace_exact(source: str, replacements) -> str:
    """Replace unique witnessed spans, preserving every surrounding character."""
    for before, after in replacements:
        if not before or source.count(before) != 1:
            raise ValueError('witness span absent or ambiguous')
        source = source.replace(before, after, 1)
    return source


def rewrite_guarded(raw: bytes, *, before_sha256: str, after_sha256: str,
                    language: str, replacements) -> bytes:
    """Hash guards identify an already reviewed witness; they do not prove semantics."""
    if len(raw) > MAX_WITNESS_BYTES or digest(raw) != before_sha256:
        raise ValueError('unsupported source identity or size')
    if language not in ('javascript', 'python'):
        raise ValueError('unsupported language')
    source = raw.decode('ascii')
    rewritten = replace_exact(source, replacements)
    helpers = JS_HELPERS if language == 'javascript' else PY_HELPERS
    result = (helpers + rewritten).encode('ascii')
    if digest(result) != after_sha256:
        raise ValueError('successor identity differs')
    if language == 'python':
        ast.parse(result.decode('ascii'))  # Syntax only; no witness execution.
    return result


def transform(key: str, raw: bytes) -> bytes:
    if key not in WITNESS_PINS:
        raise ValueError('unsupported witness key')
    return rewrite_guarded(raw, **WITNESS_PINS[key], replacements=REWRITES[key])


def write_rewrites(witnesses, output: Path):
    """Validate every supplied input before creating a fresh output directory."""
    if not witnesses or len({key for key, _ in witnesses}) != len(witnesses):
        raise ValueError('provide at least one distinct witness key')
    prepared = []
    for key, path in witnesses:
        with Path(path).open('rb') as stream:
            raw = stream.read(MAX_WITNESS_BYTES + 1)
        successor = transform(key, raw)
        language = WITNESS_PINS[key]['language']
        suffix = '.js' if language == 'javascript' else '.py'
        prepared.append((key, raw, successor, key + suffix))
    # No overwrite, reset, source mutation or automatic publication path.
    output.mkdir(exist_ok=False)
    rows = []
    for key, original, successor, filename in prepared:
        with (output / filename).open('xb') as stream:
            stream.write(successor)
        rows.append({'key': key, 'output_file': filename,
            'predecessor_sha256': digest(original), 'successor_sha256': digest(successor),
            'predecessor_bytes': len(original), 'successor_bytes': len(successor),
            'helper_bytes': len((JS_HELPERS if key.endswith('javascript') else PY_HELPERS).encode('ascii'))})
    manifest = {'schema': 'gamma.count-alignment.portable-rewrite.v1',
        'component_registry_sha256': COMPONENTS_SHA256, 'witnesses': rows,
        'candidate_executions': 0, 'new_qualification': False, 'admissions': 0,
        'scope': 'Exact identities reproduce previously tested witnesses. This invocation performs text rewriting only.'}
    with (output / 'manifest.json').open('x', encoding='utf-8') as stream:
        json.dump(manifest, stream, indent=2)
        stream.write('\n')
    return manifest


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--components', required=True, type=Path,
                        help='Explicit path to the pinned algsolve/synth/components.py')
    parser.add_argument('--witness', nargs=2, action='append', metavar=('KEY', 'PATH'),
                        help='Explicit external authorized witness file; repeat for additional keys')
    parser.add_argument('--output', type=Path, help='New local output directory; existing paths are refused')
    parser.add_argument('--describe', action='store_true', help='Print only the general helper contract and witness hashes')
    args = parser.parse_args(argv)
    if args.describe and (args.witness or args.output):
        parser.error('--describe does not accept witness/output arguments')
    if not args.describe and (not args.witness or args.output is None):
        parser.error('rewriting requires --witness KEY PATH and --output')
    try:
        registry = load_component_registry(args.components)
        if args.describe:
            value = {'component': register_component(registry), 'javascript_source': JS_HELPERS,
                     'python_separator_bytes': 1, 'witness_pins': WITNESS_PINS}
        else:
            value = write_rewrites(args.witness, args.output)
    except (OSError, ValueError, SyntaxError) as error:
        parser.error(str(error))
    print(json.dumps(value, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
