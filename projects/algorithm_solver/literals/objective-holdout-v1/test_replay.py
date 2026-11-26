#!/usr/bin/env python3
"""The checks must fail on a real failure. Each case breaks one receipt in a temporary copy and
expects replay.py or make_results.py to refuse; the unbroken copy must pass.

    python3 test_replay.py        # under a second; also run by `replay.py check`
"""
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import replay  # noqa: E402

H = 'token-K4096'
DECODE_CASES = [
    ('the decoder says not everything is ok', lambda d: d.update(all_ok=False)),
    ('the decoder lists a failure', lambda d: d['failures'].append('token-K4096: file 3 differs')),
    ('one archive did not decode to its files', lambda d: d['headers'][H].update(all_files_equal=False)),
    ('one file differs from its source', lambda d: d['headers'][H].update(files_differing_from_source=1)),
    ('a junk byte follows the last file', lambda d: d['headers'][H].update(padding_bits=d['headers'][H]['padding_bits'] + 8)),
    ('a one bit sits in the padding', lambda d: d['headers'][H].update(padding_all_zero=False)),
    ('the archive does not begin with the frozen header', lambda d: d['headers'][H].update(begins_with_frozen_header=False)),
    ('the decoder is missing an archive', lambda d: d['headers'].pop(H)),
    ('the decoder compared itself with another results file', lambda d: d.update(compared_with_sha256='0' * 64)),
    ('a results row has no archive', lambda d: d['results_rows_without_an_archive'].append(H)),
    ('the token count differs from the scorer', lambda d: d['headers'][H].update(tokens=d['headers'][H]['tokens'] + 1)),
    ('the archive hash differs from the scorer', lambda d: d['headers'][H].update(archive_sha256='0' * 64)),
    ('source files did not match the manifest', lambda d: d.update(source_files_match_manifest_sha256_and_size=False)),
]


def decode_verdict(td, mutate):
    dec = json.loads((HERE / 'out' / 'decode-fresh.json').read_text())
    mutate(dec)
    path = td / 'decode-fresh.json'
    path.write_text(json.dumps(dec))
    try:
        replay.decode_sound('fresh', HERE / 'out' / 'results-fresh.json', path, replay.SETS['fresh'][0])
    except AssertionError as exc:
        return str(exc)
    return None


def make_results_refuses(td, mutate):
    """make_results.py in a copy of the folder whose decoder receipt is broken must write nothing."""
    work = td / 'folder'
    for sub in ('out', 'sets', 'metadata', 'frozen/sets'):
        (work / sub).mkdir(parents=True)
    shutil.copy(HERE / 'make_results.py', work)
    for s in replay.SETS:
        shutil.copy(HERE / 'out' / f'results-{s}.json', work / 'out')
        shutil.copy(HERE / 'out' / f'decode-{s}.json', work / 'out')
    for name in ('fresh', 'project'):
        shutil.copy(HERE / 'sets' / f'{name}.json', work / 'sets')
    for name in ('train', 'dev'):
        shutil.copy(HERE / 'frozen' / 'sets' / f'{name}.json', work / 'frozen' / 'sets')
    shutil.copy(HERE / 'metadata' / 'ibm-identical-problem-clusters.txt', work / 'metadata')
    path = work / 'out' / 'decode-fresh.json'
    dec = json.loads(path.read_text())
    mutate(dec)
    path.write_text(json.dumps(dec))
    done = subprocess.run([sys.executable, 'make_results.py'], cwd=work, capture_output=True, text=True)
    return done.returncode != 0 and not (work / 'RESULTS.md').exists()


def main():
    failed = []
    with tempfile.TemporaryDirectory(prefix='objective-holdout-test-') as td:
        td = Path(td)
        if decode_verdict(td, lambda d: None) is not None:
            failed.append('the unbroken receipt was rejected')
        for label, mutate in DECODE_CASES:
            if decode_verdict(td, mutate) is None:
                failed.append(f'accepted although {label}')
        if not make_results_refuses(td, lambda d: d.update(all_ok=False)):
            failed.append('make_results.py wrote RESULTS.md although the decoder reported a failure')
    for strict, want in ((False, True), (True, False)):
        report = replay.Report(strict=strict)
        if report.step('probe', lambda: replay.Part('half checked')) is not want or report.steps[0]['status'] != 'PART':
            failed.append(f'a partly checked step is not reported as PART (strict={strict})')
    report = replay.Report()
    if report.step('probe', lambda: replay.need(False, 'broken')) is not False or report.ok:
        failed.append('a failed step did not fail the report')
    if failed:
        print('\n'.join('FAILED: ' + f for f in failed))
        return 1
    print(f'{len(DECODE_CASES)} broken receipts rejected, the unbroken one accepted, make_results.py refuses, PART is not PASS')
    return 0


if __name__ == '__main__':
    sys.exit(main())
