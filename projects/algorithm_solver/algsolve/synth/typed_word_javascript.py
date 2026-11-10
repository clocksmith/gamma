"""Deterministically compile validated typed-word packets to standalone JavaScript.

This is an additive backend, not a new packet version or qualification path.
The compiler accepts only the frozen decoder's canonical primitive graphs. Every
IR operation remains explicit; there is no source hole, eval or answer lookup.
JavaScript integers are BigInt, including at the positional call boundary.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from . import typed_word_codec as codec

SCHEMA = 'algsolve.typed-word-javascript.v1'
RUNTIME = Path(__file__).with_name('typed_word_javascript_runtime.mjs')


def _json(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False)


def emit(packet):
    """Return (standalone ES module source, fully charged storage receipt).

    The module exports solve(positionalInputs, budget=100000) and descriptor.
    Integers must be BigInt; booleans, arrays and null retain their normal JS
    types. Arrays represent both IR lists and tuples under static type checking.
    Input/output type and operation budgets are enforced on every invocation.
    """
    program = codec.decode(packet)
    packet_cost = codec.costs(packet)
    profile = packet_cost['profile']
    descriptor = codec.descriptor(profile)
    support = RUNTIME.read_text(encoding='utf-8')
    emitter_bytes = Path(__file__).read_bytes()
    support_bytes = support.encode('utf-8')
    initializers = {label: path.read_bytes() for label, path in (
        ('algsolve', Path(__file__).parents[1] / '__init__.py'),
        ('algsolve.synth', Path(__file__).parent / '__init__.py'),
    )}
    identity = {
        'schema': SCHEMA,
        'profile': profile,
        'width': packet_cost['width'],
        'packet_sha256': hashlib.sha256(packet).hexdigest(),
        'dictionary_sha256': descriptor['dictionary_sha256'],
        'python_runtime_sha256': descriptor['runtime_sha256'],
        'decoder_sha256': descriptor['decoder_sha256'],
        'javascript_runtime_sha256': hashlib.sha256(support_bytes).hexdigest(),
        'emitter_sha256': hashlib.sha256(emitter_bytes).hexdigest(),
        'package_initializer_sha256': {label: hashlib.sha256(data).hexdigest()
                                       for label, data in initializers.items()},
        'integer_boundary': 'BigInt with magnitude at most 128 bits; no Number coercion',
        'scope': 'authored development backend; no inherited native or catalogue qualification',
    }

    def expr(value):
        if 'ref' in value:
            body = value['ref']
        elif 'literal' in value:
            literal = value['literal']
            body = _json(literal) if type(literal) is bool else str(literal) + 'n'
        else:
            args = ','.join(expr(arg) for arg in value['args'])
            body = f'_twPure({_json(value["op"])},[{args}],_twWork)'
        return f'(_twWork.spend(),{body})'

    lines = [support.rstrip(), '', f'export const descriptor=Object.freeze({_json(identity)});',
             'export function solve(inputs,budget=100000) {',
             f'  _twRequire(Array.isArray(inputs) && inputs.length==={len(program["parameters"])},"Positional input arity mismatch");',
             '  _twRequire(Number.isInteger(budget) && budget>=1 && budget<=2000000,"Invalid execution budget");']
    for index, parameter in enumerate(program['parameters']):
        lines.append(f'  _twCheck(inputs[{index}],{_json(program["inputs"][parameter])});')
    lines.append('  const _twWork=new _twBudget(budget);')
    for index, parameter in enumerate(program['parameters']):
        lines.append(f'  const {parameter}=_twCopy(inputs[{index}]);')

    def block(statements, indent):
        prefix = '  ' * indent
        for statement in statements:
            lines.append(prefix + '_twWork.spend();')
            operation = statement['op']
            if operation in ('let', 'var', 'set'):
                declaration = {'let': 'const ', 'var': 'let ', 'set': ''}[operation]
                lines.append(f'{prefix}{declaration}{statement["name"]}={expr(statement["value"])};')
            elif operation == 'call':
                args = ','.join(expr(arg) for arg in statement['args'])
                lines.append(f'{prefix}const {statement["out"]}=_twEffect({_json(statement["operator"])},[{args}],_twWork);')
            elif operation == 'for':
                lines.append(f'{prefix}for (const {statement["item"]} of {expr(statement["in"])}) {{')
                lines.append(prefix + '  _twWork.spend();')
                block(statement['body'], indent + 1)
                lines.append(prefix + '}')
            elif operation == 'if':
                lines.append(f'{prefix}if ({expr(statement["condition"])}) {{')
                block(statement['then'], indent + 1)
                lines.append(prefix + '} else {')
                block(statement['else'], indent + 1)
                lines.append(prefix + '}')
            else:
                raise codec.Invalid('Decoder produced a nonprimitive statement')

    block(program['body'], 1)
    lines.extend([f'  const _twResult={expr(program["return"])};',
                  f'  _twCheck(_twResult,{_json(program["output_type"])});',
                  '  return _twResult;', '}', ''])
    source = '\n'.join(lines)
    source_bytes = source.encode('utf-8')
    support_storage = {
        'dictionary': descriptor['dictionary_bytes'],
        'python_decoder': descriptor['decoder_source_bytes'],
        'python_runtime': descriptor['runtime_source_bytes'],
        'javascript_emitter': len(emitter_bytes),
        'javascript_runtime': len(support_bytes),
        'python_package_initializers': sum(map(len, initializers.values())),
    }
    return source, {
        **identity,
        'generated_source_sha256': hashlib.sha256(source_bytes).hexdigest(),
        'packet_cost': packet_cost,
        'emission_support_bytes': support_storage,
        'packet_plus_emission_toolchain_bytes': len(packet) + sum(support_storage.values()),
        'standalone_javascript_source_bytes': len(source_bytes),
        'accounting': 'Packet plus emission toolchain and standalone emitted source are alternative packages, not summed. The standalone source already includes its JavaScript runtime.',
        'environment_dependencies': 'Python/Node engines and standard libraries are external environment dependencies; deployment size and human interaction costs are not measured.',
    }
