"""Cost only: externally pinned fresh-process qualification receipt required."""
import argparse
import hashlib
import json
from pathlib import Path
import resource
import signal
import time

import sys
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'six-role-cost-v1'))
import compare
from addition_policy import make_additions,storage
sys.path.insert(0,str(HERE.parents[2]))
from catalogue.public_batch_adapter import bounded_regular_read


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def pinned(spec):
    raw=bounded_regular_read(str(Path(spec['path']).absolute()),maximum_bytes=4*1024**2)
    if sha(raw)!=spec['sha256']:raise ValueError('metadata identity')
    return json.loads(raw)


def run(freeze, output):
    start = time.monotonic()
    for path, expected in freeze['code_sha256'].items():
        if sha(Path(path).read_bytes()) != expected:
            raise ValueError('cost dependency changed')
    verified = pinned(freeze['verified'])
    report = pinned(freeze['report'])
    qualification = pinned(freeze['qualification_freeze'])
    if (verified.get('schema')!='gamma.extrema8-role-alignment.matched-independent-verification.v1'or report.get('schema')!='gamma.extrema8-role-alignment.matched-run.v1'or verified.get('automatic_promotion')is not False or verified.get('protected_access')is not False or verified.get('fit_owners')!=300 or verified.get('original_variants_retained')!=875 or len(verified.get('outcomes',[]))!=24 or verified['verified'] is not True or verified['report_sha256'] != freeze['report']['sha256'] or
            verified['freeze_sha256'] != freeze['qualification_freeze']['sha256'] or
            verified['qualified_arms'] != 24 or verified['isolated_executions'] != 87 or verified['checks'] != 2406 or
            report['qualified_arms'] != 24 or report['status'] != 'completed'):
        raise ValueError('all matched arms must be independently qualified')
    if [r['id']for r in qualification['rows']] != [123,55,1014,1121,1375,1725,1732,2873] or qualification['cases_per_arm']!=802 or qualification['calls_per_arm']!=29 or report['candidate_executions']!=87 or report['checks_passed']!=2406:raise ValueError('exact reviewed eight matched scope')
    for cleanup in freeze['cleanup']:
        value=pinned(cleanup)
        if value['exit_code']!=0 or not value['no_executing_owned_processes_observed']or value['remaining_live_owned']or value['inspection_unreadable_pids']or value['wall_timeout']:raise ValueError('qualification/verifier cleanup incomplete')
    expected = {(arm, row['id']): row[arm]['sha256'] for arm in ('original', 'format', 'role') for row in qualification['rows']}
    actual = {(row['arm'], row['id']): row['source_sha256'] for row in verified['outcomes'] if row['passed'] is True}
    if actual != expected or len(actual) != 24:
        raise ValueError('complete source-specific qualification')
    module, state = compare.recover(freeze['recovery']['path'], output / 'recovery.json')
    transfer = module.f.load('six_role_cost_transfer', module.f.LIT / 'readable-joint-blocks-v1/transfer.py')
    qualified = []
    for row in qualification['rows']:
        pid = str(row['id'])
        for arm in ('format','role'):
            module.boundary_policy.authorize_before_open('leetcode:' + pid, state['gate']['artifact_paths'],
                state['gate']['trusted_hashes'], language='javascript', payload_kind='source')
            spec = row[arm]
            path = Path(spec['path'])
            raw = transfer.read_relative(path.parent, path.name, maximum=65536)
            if sha(raw) != spec['sha256'] or len(raw) != spec['bytes']:
                raise ValueError('qualified transformed source identity')
            text=raw.decode('utf8')
            compare.whole_source_exclusion(text,state['best']['vocabulary'])
            qualified.append((arm,pid,text,spec['sha256']))
    additions,duplicate_hashes=make_additions(state['texts'],state['groups'],qualified)
    source_storage=storage(state['texts'],state['groups'],additions)
    comparisons = compare.compare(state, additions)
    summaries = {}
    for arm, result in comparisons.items():
        result['source_choices_sha256'] = module.digest(result.pop('choices'))
        summaries[arm] = result
    return dict(schema='gamma.extrema8-fixed-dictionary-cost.v1', status='completed',
        qualification_report_sha256=freeze['report']['sha256'], qualification_verifier_sha256=freeze['verified']['sha256'],
        dictionary_sha256=compare.DICTIONARY_SHA, original_source_choices_sha256=compare.CHOICES_SHA,
        fit_denominator=300, m1_denominator=500, catalogue_denominator=4081,
        original_variants_retained=875, qualified_arm_entries=16,introduced_arm_entries=sum(len(v)for v in additions.values()),source_storage=source_storage,
        exact_existing_source_duplicates=duplicate_hashes, dictionary_search=False,
        candidate_execution=False, protected_access=False, m1_qualified=False,
        comparisons=summaries, tie_policy='Unchanged minN/minC/reference/key policy; new keys sort after existing owner keys so equal-cost old choices are preserved.', wall_seconds=time.monotonic()-start,
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
