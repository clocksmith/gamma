"""Explicit bridge from prediction trees to charged primitive word streams.

Neither existing codec nor runtime is changed. Predictions target base-v2, not
vector-v1. Recipe inlining, alpha-renaming and grammar serialization are explicit
conversion steps; node labels alone are never reported as complete input cost.
"""
from __future__ import annotations

from collections import Counter
import hashlib
import json
from pathlib import Path

from . import typed_prediction_codec as prediction
from . import typed_recipes
from . import typed_word_codec as word

SCHEMA = 'algsolve.typed-stream-contract.v1'
ROLES = ('operations', 'bindings', 'structure', 'constants', 'types')


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'),
                                     allow_nan=False).encode()).hexdigest()


def descriptor():
    """Concrete label/code mapping, including labels with no single word image."""
    vocabularies = {p: word.vocabulary(p) for p in word.PROFILES}
    rows = []
    fixed = {'EMPTY': (), 'root': ('PROGRAM',), 'sequence': ('BLOCK',),
             'let': ('LET',), 'var': ('VAR',), 'set': ('SET',), 'for': ('FOR',),
             'if': ('IF',), 'ref': ('REF',), 'int': ('INT',),
             'bool': ('TRUE', 'FALSE')}
    for code, label in enumerate(prediction.OPS):
        if label.startswith('pure:'):
            tokens, conversion = ('P:' + label[5:],), 'operation with charged arity and operands'
        elif label.startswith('call:'):
            tokens, conversion = ('E:' + label[5:],), 'effect with charged output binding, arity and operands'
        elif label.startswith('recipe:'):
            tokens, conversion = (), 'hygienically inline full base recipe; no recipe opcode'
        else:
            tokens = fixed[label]
            conversion = {'EMPTY': 'prediction padding only; not a stream word',
                          'root': 'serialize ordered parameter signature, output type, body and return',
                          'sequence': 'serialize statement count and ordered body',
                          'ref': 'remap input/declaration slot to sequential lexical binding index',
                          'int': '129 prediction bits to sign and canonical MSB magnitude words plus END',
                          'bool': '129 prediction bits to exactly one TRUE or FALSE word'}.get(
                              label, 'serialize statement shape and all bindings/operands')
        rows.append({'prediction_code': code, 'prediction_label': label,
                     'conversion': conversion, 'word_tokens': list(tokens),
                     'word_codes': {p: [v.index(t) for t in tokens] for p, v in vocabularies.items()}})
    return {'schema': SCHEMA, 'prediction_schema': 'algsolve.typed-prediction.v1',
            'prediction_labels': len(prediction.OPS), 'prediction_program_schema': prediction.ir.SCHEMA,
            'prediction_mapping': rows,
            'profiles': {p: word.descriptor(p) for p in vocabularies},
            'vector_only_words': [t for t in vocabularies['vector-v1'] if t not in vocabularies['base-v2']],
            'compatibility': 'Prediction conversion accepts base-v2 only. Vector operations, resource '
                             'ownership and runtime schema are not lowered or relabeled.',
            'structure': 'first-child/next-sibling links become charged prefix grammar, block counts '
                         'and argument counts; no edge table is required by the resulting packet',
            'bindings': 'Inputs retain positional order. Prediction references use input index or '
                        '8 + declaration slot; word references/declarations use sequential bN indices. '
                        'Recipe expansion introduces additional charged lexical bindings.',
            'types': 'Prediction type IDs are fitted side information. Stream types and compound '
                     'arity are explicit words; no fitted type table is required to decode the packet.',
            'constants': 'Integers preserve signed 128-bit magnitude bounds. Prediction magnitude '
                         'bits are LSB-first; stream magnitude words are canonical MSB-first. '
                         'Booleans remain distinct from integers.',
            'not_measured': ['prediction transport bytes', 'model/optimizer storage and inference cost',
                             'human navigation, corrections and completion time', 'native qualification',
                             'unseen solving'],
            'sources': conversion_support()}


def conversion_support():
    """Source storage for the bridge/tooling, separate from packet decode support."""
    root = Path(__file__).parent
    names = ('typed_stream_contract.py', 'typed_prediction_codec.py', 'typed_codec.py',
             'typed_recipes.py', 'typed_program.py', 'typed_word_codec.py')
    return {name: {'sha256': hashlib.sha256((root / name).read_bytes()).hexdigest(),
                   'storage_bits': (root / name).stat().st_size * 8} for name in names}


def ledger(packet):
    """Partition every validated payload selection by its grammatical role.

    The same BIT0/BIT1/END tokens are classified by context, never guessed from
    their spelling. This is an accounting view, not a new decoder or wire format.
    """
    program = word.decode(packet)
    profile, width, indices = word._unpack(packet)
    vocabulary = word.vocabulary(profile)
    actual = [vocabulary[i] for i in indices]
    entries = []

    def emit(token, role):
        position = len(entries)
        word.require(position < len(actual) and actual[position] == token,
                     'Cost ledger differs from validated word stream')
        entries.append({'selection': position, 'word': token, 'code': indices[position], 'role': role})

    def natural(value, role):
        for bit in bin(value)[2:]:
            emit('BIT' + bit, role)
        emit('END', role)

    def binding(name):
        natural(int(name[1:]), 'bindings')

    def dtype(value):
        if type(value) is str:
            emit('T:' + value, 'types')
        else:
            emit('T:' + value[0], 'types')
            if value[0] == 'tuple':
                natural(len(value) - 1, 'types')
            for item in value[1:]:
                dtype(item)

    def arguments(values):
        natural(len(values), 'structure')
        for value in values:
            expression(value)

    def expression(value):
        if 'ref' in value:
            emit('REF', 'bindings')
            binding(value['ref'])
        elif 'literal' in value:
            literal = value['literal']
            if type(literal) is bool:
                emit('TRUE' if literal else 'FALSE', 'constants')
            else:
                emit('INT', 'constants')
                emit('NEG' if literal < 0 else 'POS', 'constants')
                natural(abs(literal), 'constants')
        else:
            emit('P:' + value['op'], 'operations')
            arguments(value['args'])

    def block(body):
        emit('BLOCK', 'structure')
        natural(len(body), 'structure')
        for statement in body:
            kind = statement['op']
            if kind in ('let', 'var', 'set'):
                emit(kind.upper(), 'operations')
                binding(statement['name'])
                expression(statement['value'])
            elif kind == 'call':
                emit('E:' + statement['operator'], 'operations')
                binding(statement['out'])
                arguments(statement['args'])
            elif kind == 'for':
                emit('FOR', 'structure')
                binding(statement['item'])
                expression(statement['in'])
                block(statement['body'])
            elif kind == 'if':
                emit('IF', 'structure')
                expression(statement['condition'])
                block(statement['then'])
                block(statement['else'])

    emit('PROGRAM', 'structure')
    natural(len(program['parameters']), 'structure')
    for name in program['parameters']:
        binding(name)
        dtype(program['inputs'][name])
    dtype(program['output_type'])
    block(program['body'])
    expression(program['return'])
    word.require(len(entries) == len(actual), 'Unaccounted stream selections')
    counts = Counter(entry['role'] for entry in entries)
    costs = word.costs(packet)
    return {'schema': SCHEMA, 'profile': profile, 'width': width,
            'categories': {role: {'selections': counts[role], 'bits': counts[role] * width} for role in ROLES},
            'costs': costs, 'trace': entries,
            'interaction_scope': 'Complete serialized program, framing and padding; not measured human interaction.'}


def from_prediction(codec, codes, params, width=6):
    """Decode base prediction, expand its fixed recipes, and charge all words.

    The existing prediction validator remains authoritative. Raw prediction and
    descriptor hashes are retained because ignored prediction fields and cosmetic
    names need not survive conversion; this is not a lossless tensor transport.
    """
    params = list(params)
    program = codec.decode(codes, params)
    packet, _ = word.encode(program, width, 'base-v2', typed_recipes.catalog())
    report = ledger(packet)
    nodes, _ = prediction.flatten(program)
    report.update({'prediction_descriptor': codec.descriptor(),
                   'prediction_descriptor_sha256': digest(codec.descriptor()),
                   'raw_prediction_sha256': digest(codes),
                   'ordered_parameters_sha256': digest(params),
                   'canonical_program_sha256': digest(word.decode(packet)),
                   'packet_sha256': hashlib.sha256(packet).hexdigest(),
                   'recipe_catalog_sha256': digest(typed_recipes.catalog()),
                   'prediction_tensor': {'slots': codec.slots, 'active_nodes': len(nodes),
                                         'op_fields': codec.slots, 'edge_fields': 2 * codec.slots,
                                         'binding_fields': codec.slots, 'literal_bit_fields': prediction.BITS * codec.slots,
                                         'type_fields': prediction.INPUTS + 1,
                                         'wire_bits': None},
                   'conversion_support': conversion_support(),
                   'evidence_scope': 'Representation conversion only; no prediction quality or source qualification.'})
    return packet, report


def to_prediction(packet, codec):
    """Encode a base primitive packet into an existing fitted predictor vocabulary.

    Recipes are not refolded. Slot limits and fitted type coverage may reject a
    perfectly valid word packet. Vector packets always fail rather than changing
    runtime identity or replacing mutation with immutable append.
    """
    profile, _, _ = word._unpack(packet)
    word.require(profile == 'base-v2', 'Vector profile has no compatible frozen prediction schema')
    program = word.decode(packet)
    codes = codec.encode(program)
    # Check the resulting prediction itself, including lexical scope and limits.
    decoded = codec.decode(codes, program['parameters'])
    word.require(word.canonicalize(decoded) == program, 'Prediction conversion changed primitive semantics')
    return codes, program['parameters']
