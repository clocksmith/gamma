"""Portable, source-hash-bound independent development checks.

Run from any directory. Default source root is the parent of this review folder.
No acquisition, admission, serving, or qualification decisions are made here.
"""
import argparse
import collections
import hashlib
import json
import pathlib
import subprocess
import sys
import time

import highrisk_oracles as oracle

HERE = pathlib.Path(__file__).resolve().parent
IDS = (3235, 3518, 3525, 3539, 3579, 3590, 3600)


def python_limits():
    try:
        import resource
    except ImportError:
        return
    resource.setrlimit(resource.RLIMIT_AS, (512 * 1024**2, 512 * 1024**2))
    resource.setrlimit(resource.RLIMIT_CPU, (60, 60))


def run_language(root, pid, language, cases):
    if language == 'python':
        command = [sys.executable, str(HERE / 'highrisk_runner.py'), str(root)]
    else:
        command = ['node', '--max-old-space-size=256',
                   str(HERE / 'highrisk_runner.js'), str(root)]
    requests = [{'pid': pid, 'args': case['args']} for case in cases]
    start = time.monotonic()
    # POSIX-only resource limits supplement a portable wall-clock timeout.
    limit_fn = python_limits if language == 'python' and sys.platform != 'win32' else None
    process = subprocess.run(command, input=json.dumps(requests), capture_output=True,
                             text=True, timeout=65, check=True, preexec_fn=limit_fn)
    answers = json.loads(process.stdout)
    assert len(answers) == len(cases), (pid, language, 'output count')
    for index, (answer, case) in enumerate(zip(answers, cases)):
        assert answer['value'] == case['expected'], (pid, language, index, answer['value'], case['expected'])
        assert answer['mutated'] is False, (pid, language, index, 'unexpected input mutation')
    return round(time.monotonic() - start, 4)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=pathlib.Path, default=HERE.parent)
    parser.add_argument('--receipt', type=pathlib.Path, default=HERE / 'highrisk_review.json')
    parser.add_argument('--skip-maximum', action='store_true')
    parser.add_argument('--out', type=pathlib.Path)
    args = parser.parse_args()
    root = args.root.resolve()
    frozen = json.loads(args.receipt.read_text())
    expected_rows = {row['problem_id']: row for row in frozen['results']}
    hashes = {}
    for pid in IDS:
        hashes[pid] = {}
        for language, suffix in [('python', 'py'), ('javascript', 'js')]:
            path = root / language / f'{pid}.{suffix}'
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            assert digest == expected_rows[pid]['source_sha256'][language], (pid, language, 'source differs from reviewed bytes')
            hashes[pid][language] = digest
    # Generate in this fixed order so seeded random cases remain reproducible.
    all_cases = {pid: oracle.cases_for(pid) for pid in IDS}
    all_cases[3235] = oracle.add_geometry_cases(all_cases[3235])
    results = []
    for pid, cases in all_cases.items():
        assert len(cases) == expected_rows[pid]['cases_per_language']
        digest = hashlib.sha256((json.dumps(cases, separators=(',', ':')) + '\n').encode()).hexdigest()
        assert digest == expected_rows[pid]['case_sha256'], (pid, 'regenerated cases differ')
        elapsed = {language: run_language(root, pid, language, cases)
                   for language in ('python', 'javascript')}
        results.append({'problem_id': pid, 'source_sha256': hashes[pid],
                        'cases_per_language': len(cases), 'language_checks': 2 * len(cases),
                        'categories': dict(collections.Counter(case['kind'] for case in cases)),
                        'case_sha256': digest, 'seconds': elapsed, 'passed': True})
        print(f'{pid}: {len(cases)} cases x 2 languages passed', file=sys.stderr)
    maximum_results = []
    if not args.skip_maximum:
        for pid, values, expected, description in oracle.maximum_cases():
            cases = [{'args': values, 'expected': expected}]
            for language in ('python', 'javascript'):
                seconds = run_language(root, pid, language, cases)
                maximum_results.append({'problem_id': pid, 'language': language,
                                        'source_sha256': hashes[pid][language],
                                        'description': description, 'seconds': seconds, 'passed': True})
                print(f'{pid}: {language} maximum-shape probe passed', file=sys.stderr)
    report = {'schema': 'gamma.request-252-independent-review-replay.v1',
              'results': results, 'oracle_language_checks': sum(row['language_checks'] for row in results),
              'maximum_shape_results': maximum_results, 'maximum_shape_language_checks': len(maximum_results),
              'source_policy_changed': False, 'qualification_created': False}
    encoded = json.dumps(report, indent=2) + '\n'
    if args.out:
        args.out.write_text(encoded)
    else:
        print(encoded, end='')


if __name__ == '__main__':
    main()
