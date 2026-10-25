"""Cost only: externally pinned fresh-process qualification receipt required."""
import argparse
import hashlib
import json
from pathlib import Path
import resource
import signal
import time

import compare


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def pinned(spec):
    path = Path(spec['path'])
    if not path.is_absolute() or path.is_symlink() or path.stat().st_size > 32 * 1024**2:
        raise ValueError('bounded exact metadata path')
    raw = path.read_bytes()
    if sha(raw) != spec['sha256']:
        raise ValueError('metadata identity')
    return json.loads(raw)


def run(freeze, output):
    start = time.monotonic()
    for path, expected in freeze['code_sha256'].items():
        if sha(Path(path).read_bytes()) != expected:
            raise ValueError('cost dependency changed')
    verified = pinned(freeze['verified'])
    report = pinned(freeze['report'])
    qualification = pinned(freeze['qualification_freeze'])
    if (verified['verified'] is not True or verified['report_sha256'] != freeze['report']['sha256'] or
            verified['freeze_sha256'] != freeze['qualification_freeze']['sha256'] or
            verified['qualified_arms'] != 18 or verified['isolated_executions'] != 57 or verified['checks'] != 1554 or
            report['qualified_arms'] != 18 or report['status'] != 'completed'):
        raise ValueError('all matched arms must be independently qualified')
    expected = {(arm, row['id']): row[arm]['sha256'] for arm in ('original', 'format', 'role') for row in qualification['rows']}
    actual = {(row['arm'], row['id']): row['source_sha256'] for row in verified['outcomes'] if row['passed'] is True}
    if actual != expected or len(actual) != 18:
        raise ValueError('complete source-specific qualification')
    module, state = compare.recover(freeze['recovery']['path'], output / 'recovery.json')
    transfer = module.f.load('six_role_cost_transfer', module.f.LIT / 'readable-joint-blocks-v1/transfer.py')
    additions = {'format': {}, 'role': {}}
    duplicate_hashes = []
    existing_hashes = {sha(text.encode()) for text in state['texts'].values()}
    for row in qualification['rows']:
        pid = str(row['id'])
        for arm in additions:
            module.boundary_policy.authorize_before_open('leetcode:' + pid, state['gate']['artifact_paths'],
                state['gate']['trusted_hashes'], language='javascript', payload_kind='source')
            spec = row[arm]
            path = Path(spec['path'])
            raw = transfer.read_relative(path.parent, path.name, maximum=65536)
            if sha(raw) != spec['sha256'] or len(raw) != spec['bytes']:
                raise ValueError('qualified transformed source identity')
            if spec['sha256'] in existing_hashes:
                duplicate_hashes.append({'problem_id': pid, 'arm': arm, 'sha256': spec['sha256']})
            additions[arm][pid] = dict(key=pid + ':six-' + arm + '-' + spec['sha256'],
                source=raw.decode('utf8'), sha256=spec['sha256'])
    comparisons = compare.compare(state, additions)
    summaries = {}
    for arm, result in comparisons.items():
        result['source_choices_sha256'] = module.digest(result.pop('choices'))
        summaries[arm] = result
    return dict(schema='gamma.six-role-fixed-dictionary-cost.v1', status='completed',
        qualification_report_sha256=freeze['report']['sha256'], qualification_verifier_sha256=freeze['verified']['sha256'],
        dictionary_sha256=compare.DICTIONARY_SHA, original_source_choices_sha256=compare.CHOICES_SHA,
        fit_denominator=300, m1_denominator=500, catalogue_denominator=4081,
        original_variants_retained=875, introduced_arm_entries=12,
        exact_existing_source_duplicates=duplicate_hashes, dictionary_search=False,
        candidate_execution=False, protected_access=False, m1_qualified=False,
        comparisons=summaries, wall_seconds=time.monotonic()-start,
        cpu_seconds=time.process_time(), peak_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        evidence_scope='Fixed dictionary, separately finite-qualified sources, exact decoding and complete costs; no normative/canonical promotion')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--freeze', required=True)
    parser.add_argument('--freeze-sha256', required=True)
    parser.add_argument('--output', required=True)
    args = parser.parse_args()
    resource.setrlimit(resource.RLIMIT_AS, (512 * 1024**2,) * 2)
    resource.setrlimit(resource.RLIMIT_CPU, (60, 60))
    signal.alarm(60)
    freeze = pinned({'path': str(Path(args.freeze).resolve()), 'sha256': args.freeze_sha256})
    output = Path(args.output)
    output.mkdir(mode=0o700, parents=True, exist_ok=False)
    try:
        result = run(freeze, output)
        result['freeze_sha256'] = args.freeze_sha256
        (output / 'report.json').write_text(json.dumps(result, indent=2, sort_keys=True,
            default=lambda value: {'numerator': value.numerator, 'denominator': value.denominator}) + '\n')
    except BaseException as error:
        (output / 'failure.json').write_text(json.dumps({'error_type': type(error).__name__,
            'freeze_sha256': args.freeze_sha256, 'qualified': False}) + '\n')
        raise
