"""Versioned target contract and deterministic sandbox assembly, no model calls."""
from __future__ import annotations

import argparse
import hashlib
import json
import keyword
from pathlib import Path

from . import typed_program as ir, typed_recipes

SCHEMA = 'algsolve.typed-codec.v1'
TARGET_SCHEMA = 'algsolve.typed-target.v1'
EXECUTION_BUDGET = 2000000


def digest(value):
    return hashlib.sha256(ir.canonical(value).encode()).hexdigest()


def descriptor():
    root = Path(__file__).parent
    return {'schema': SCHEMA, 'program_schema': ir.SCHEMA,
            'pure_operators': sorted(ir.PURE),
            'effects': {k: {'inputs': list(ins), 'output': out, 'effect': effect}
                        for k, (ins, out, effect) in sorted(ir.EFFECTS.items())},
            'map_get_contract': 'Read-only: stored value, including zero, wins over default; absent key returns the integer default without insertion. map.has distinguishes presence when stored value equals default. Boolean defaults are not integers.',
            'statements': ['let', 'var', 'set', 'call', 'recipe', 'for', 'if'],
            'types': {'atoms': ['int', 'bool', 'unit', *sorted(ir.RESOURCES)],
                      'constructors': ['list[element]', 'tuple[fields...]'],
                      'resource_containment': 'no resource aliases, values, inputs or outputs'},
            'bindings': {'inputs': 'explicit ordered parameters array defines positional recipe ports; inputs map defines types only',
                         'let': 'immutable lexical binding, no shadowing',
                         'var_set': 'typed cell; writes survive child scope',
                         'branches_loops': 'child locals do not escape',
                         'references': 'lexically bound names, no forward references'},
            'limits': {'graph_tree_nodes': ir.MAX_GRAPH_NODES, 'graph_depth': ir.MAX_DEPTH,
                       'collection_length': ir.MAX_COLLECTION, 'integer_bits': ir.MAX_INTEGER_BITS,
                       'execution_operations': EXECUTION_BUDGET, 'recipe_depth': 8},
            'recipes': typed_recipes.catalog(),
            'expansion': 'hygienic inlining; result binding; owned resources; same primitive IR',
            'serialization': 'UTF-8 compact JSON; sorted object keys; arrays including parameters retain order; no NaN',
            'sources_sha256': {n: hashlib.sha256((root/n).read_bytes()).hexdigest()
                               for n in ['typed_codec.py', 'typed_program.py', 'typed_recipes.py']}}


def frozen(path):
    value = json.loads(Path(path).read_text())
    if value != descriptor():
        raise ir.Invalid('Frozen codec differs from runtime/catalog; create a new version before evaluation')
    return digest(value)


def encode(program, identity):
    catalog = typed_recipes.catalog()
    expanded, names = ir.expanded(program, catalog)
    return {'schema': TARGET_SCHEMA, 'codec_sha256': identity, 'program': program,
            'expanded_sha256': digest(expanded), 'input_mapping': names}


def decode(target, identity):
    ir.fields(target, 'schema', 'codec_sha256', 'program', 'expanded_sha256', 'input_mapping')
    ir.require(target['schema'] == TARGET_SCHEMA and target['codec_sha256'] == identity, 'Target codec mismatch')
    expected = encode(target['program'], identity)
    ir.require(target == expected, 'Target expansion/binding receipt differs')
    return target['program']


def render(target, identity, *, method, params):
    program = decode(target, identity)
    ir.require(program['parameters'] == params, 'Problem parameter order differs from target')
    for value in [method, *params]:
        ir.name(value)
        ir.require(not keyword.iskeyword(value), 'Reserved Python adapter name')
    ir.require(method not in params and 'self' not in params, 'Adapter name collision')
    source = Path(ir.__file__).read_text()
    payload = ir.canonical({'program': program, 'recipes': typed_recipes.catalog()})
    # Only the fixed runtime and validated JSON are assembled. Graph expressions
    # never become Python source. Expected outputs never enter this adapter.
    return (source + '\n\n_TYPED = json.loads(' + repr(payload) + ')\n'
            + 'class Solution:\n    def ' + method + '(self' + ''.join(', ' + p for p in params) + '):\n'
            + '        return execute(_TYPED["program"], {'
            + ', '.join(repr(p) + ': ' + p for p in params)
            + '}, recipes=_TYPED["recipes"], budget=' + str(EXECUTION_BUDGET) + ')\n')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--freeze', type=Path, required=True)
    args = parser.parse_args()
    with args.freeze.open('x') as stream:
        stream.write(ir.canonical(descriptor()) + '\n')
    print(json.dumps({'path': str(args.freeze), 'sha256': frozen(args.freeze)}))


if __name__ == '__main__': main()
