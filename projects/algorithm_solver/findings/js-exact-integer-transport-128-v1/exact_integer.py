"""Isolated exact-integer transport v2. Does not modify the live wave helper."""
from dataclasses import replace
import json
import math
from pathlib import Path
import re

from algsolve.judge import judge, sandbox

TAG = '__gamma_bigint_v1__'
MAX_SAFE = 2**53 - 1
MAX_DIGITS = 4096
DECIMAL = re.compile(r'(?:0|-[1-9][0-9]*|[1-9][0-9]*)\Z')
HARNESS = Path(__file__).with_name('harness.cjs')


def pack_input(value):
    """Only actual Python ints outside the safe range become tagged BigInts."""
    if type(value) is int:
        if abs(value) <= MAX_SAFE:
            return value
        text = str(value)
        if len(text.lstrip('-')) > MAX_DIGITS:
            raise ValueError('Exact integer digit limit')
        return {TAG: text}
    if type(value) is float:
        if not math.isfinite(value) or (value.is_integer() and abs(value) > MAX_SAFE):
            raise ValueError('Unsafe/nonfinite floating input')
        return value
    if isinstance(value, list):
        return [pack_input(x) for x in value]
    if isinstance(value, dict):
        if TAG in value:
            raise ValueError('Reserved exact-integer key in user object')
        return {k: pack_input(v) for k, v in value.items()}
    if value is None or isinstance(value, (str, bool)):
        return value
    raise ValueError('Unsupported input type')


def unpack_output(value):
    if isinstance(value, dict):
        if TAG in value:
            text = value[TAG]
            if (set(value) != {TAG} or not isinstance(text, str)
                    or len(text.lstrip('-')) > MAX_DIGITS or not DECIMAL.fullmatch(text)):
                raise ValueError('Malformed exact-integer tag')
            return int(text)
        return {k: unpack_output(v) for k, v in value.items()}
    if isinstance(value, list):
        return [unpack_output(x) for x in value]
    if type(value) is int and abs(value) > MAX_SAFE:
        raise ValueError('Unsafe untagged integer output')
    if type(value) is float and (not math.isfinite(value)
                               or (value.is_integer() and abs(value) > MAX_SAFE)):
        raise ValueError('Unsafe/nonfinite numeric output')
    return value


def no_duplicates(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError('Duplicate JSON key')
        result[key] = value
    return result


def reject_constant(value):
    raise ValueError('Nonfinite JSON constant: ' + value)


def decode_stdout(data):
    records = []
    for line in data.decode('utf-8').splitlines():
        if not line.strip():
            continue
        row = json.loads(line, object_pairs_hook=no_duplicates, parse_constant=reject_constant)
        if not isinstance(row, dict):
            raise ValueError('Protocol record must be object')
        for field in ('result', 'args_after'):
            if field in row:
                row[field] = unpack_output(row[field])
        records.append(row)
    # Python emits exact integer decimal tokens, and the unchanged host judge
    # reads them back as arbitrary-precision ints. Expectations are untouched.
    return ('\n'.join(json.dumps(r, allow_nan=False) for r in records) + '\n').encode()


def score_result(result, tests):
    if result.timed_out or result.output_limit_exceeded:
        return judge._score_functional(result, tests)
    try:
        translated = decode_stdout(result.stdout)
    except (ValueError, UnicodeError) as exc:
        return judge.Verdict(False, judge.MALFORMED_OUTPUT, len(tests), 0,
                             result.wall_seconds, {'transport_error': str(exc)},
                             result.stderr.decode('utf-8', 'replace')[-600:])
    return judge._score_functional(replace(result, stdout=translated), tests)


def execute(source, method, params, tests):
    calls = {'method': method, 'params': params,
             'calls': [{'args': pack_input(t.args),
                        'capture_args': str(t.compare).startswith('arg:')} for t in tests]}
    payload = json.dumps(calls, allow_nan=False)
    result = sandbox.run(['/usr/bin/node', '--jitless', '--max-old-space-size=64', 'harness.cjs'],
        files={'harness.cjs': HARNESS.read_text(), 'candidate.cjs': source,
               'calls.json': payload},
        limits=sandbox.Limits(wall_seconds=8, cpu_seconds=3, memory_bytes=1024**3,
                             max_output_bytes=65536))
    return score_result(result, tests), result, payload
