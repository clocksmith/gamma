"""Bounded editor execution through the existing Linux sandbox and host scorer."""
import json
import re
from pathlib import Path
from . import validate
from .judge import judge, sandbox
from .records import Problem

IDENTIFIER = re.compile(r'^[A-Za-z_][A-Za-z_0-9]*$')


def query_problem(raw):
    if not isinstance(raw, dict):
        raise ValueError('Problem must be an object')
    tests = raw.get('public_tests', [])
    if not isinstance(tests, list) or len(tests) > 20:
        raise ValueError('At most 20 public examples')
    for test in tests:
        if not isinstance(test, dict) or 'expected' not in test or not isinstance(test.get('args'), list):
            raise ValueError('Each example needs args and expected')
        if test.get('kwargs'):
            raise ValueError('Use positional arguments in editor examples')
        if test.get('compare', 'return') != 'return' and not re.fullmatch(r'arg:\d+', test.get('compare', '')):
            raise ValueError('Unsupported comparison')
    entry = raw.get('entry', {})
    if not isinstance(entry, dict) or not IDENTIFIER.fullmatch(entry.get('method', '')):
        raise ValueError('A named function/method is required')
    if entry.get('class') and not IDENTIFIER.fullmatch(entry['class']):
        raise ValueError('Invalid class')
    params = raw.get('params', [])
    if not isinstance(params, list) or any(not isinstance(p, list) or len(p) != 2 or not all(isinstance(x, str) for x in p) or not IDENTIFIER.fullmatch(p[0]) for p in params):
        raise ValueError('Invalid function parameters')
    return Problem(uid='user:editor', source='user', source_id='editor',
                   title=str(raw.get('title', 'Editor problem'))[:500], slug=str(raw.get('slug', ''))[:200],
                   statement=str(raw.get('statement', ''))[:60000], io_mode='functional',
                   entry={k: v for k,v in entry.items() if k in ('class', 'method')}, params=params,
                   starter_code=str(raw.get('starter_code', ''))[:10000], public_tests=tests)


def execute(language, source, problem=None):
    if language not in ('python', 'javascript') or not isinstance(source, str) or len(source.encode()) > 65536:
        raise ValueError('Expected Python/JavaScript source, at most 64 KiB')
    if problem is not None:
        query = query_problem(problem)
        if language == 'python':
            verdict = validate.judge_problem(query, source, query.public_tests, wall_seconds=8)
        else:
            tests = validate.functional_tests(query.public_tests)
            if query.slug == 'course-schedule-ii' and query.entry['method'] == 'findOrder':
                for test in tests:
                    test.validator = 'topological_order'
            if not tests:
                return {'example_passed': False, 'reason': 'no_tests', 'independent_tests_passed': None}
            calls = {'method': query.entry['method'], 'params': query.params,
                     'calls': [{'args': t.args} for t in tests]}
            result = sandbox.run(['/usr/bin/node', '--jitless', '--max-old-space-size=64', 'harness.cjs'],
                files={'harness.cjs': Path(__file__).with_name('editor_harness.cjs').read_text(),
                       'candidate.cjs': source, 'calls.json': json.dumps(calls)},
                limits=sandbox.Limits(wall_seconds=8, cpu_seconds=3, memory_bytes=1024*1024*1024, max_output_bytes=65536))
            verdict = judge._score_functional(result, tests)
        return {'example_passed': verdict.passed, 'independent_tests_passed': None, 'verdict': verdict.to_dict()}
    argv = [sandbox.PYTHON, '-I', '-S', 'candidate.py'] if language == 'python' else ['/usr/bin/node', '--jitless', '--max-old-space-size=64', 'candidate.cjs']
    filename = 'candidate.py' if language == 'python' else 'candidate.cjs'
    result = sandbox.run(argv, files={filename: source}, limits=sandbox.Limits(
        wall_seconds=3, cpu_seconds=2, memory_bytes=1024*1024*1024, max_output_bytes=65536))
    return {'execution_ok': result.ok, 'stdout': result.stdout.decode('utf-8', 'replace'),
            'stderr': result.stderr.decode('utf-8', 'replace'), 'timed_out': result.timed_out,
            'output_limit_exceeded': result.output_limit_exceeded, 'exit_code': result.exit_code,
            'example_passed': None, 'independent_tests_passed': None}
