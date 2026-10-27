"""Verify pinned BITS replay observations for the existing admission queue.

This accepts only the bounded return/mutation observation scope of that runner.
It never upgrades qualification, browser guide admission, aliases, licenses or
source access. Operator-supplied artifact pins are trust inputs, not self-proof.
"""
import hashlib
import json

from .catalogue import BINDINGS, digest


ADAPTERS = {'named-function-v1', 'commonjs-solve-v1', 'commonjs-object-solve-v1'}


def verify(bundle_raw, report_raw, queue, *, bundle_sha256, report_sha256,
           runner_hashes, runtime_sha256):
    """Return source_evidence records after checking every recorded case batch."""
    def require(ok, message):
        if not ok:
            raise ValueError(message)

    sha = lambda raw: hashlib.sha256(raw).hexdigest()
    require(sha(bundle_raw) == bundle_sha256 and sha(report_raw) == report_sha256,
            'externally pinned browser artifacts required')
    bundle, report = json.loads(bundle_raw), json.loads(report_raw)
    require(report.get('bundle_sha256') == bundle_sha256 and
            report.get('runner') == runner_hashes and
            report.get('runtime_sha256') == runtime_sha256,
            'browser source/runtime binding mismatch')
    require(report.get('externalRequests') == [] and
            report.get('browser_guides_admitted') == 0,
            'unexpected external requests or admission claim')
    require(bundle.get('service_sha256') == queue['inputs']['service_sha256'],
            'queue/service identity mismatch')
    expected, observed = bundle['rows'], report['rows']
    require(0 < len(expected) <= 4096 and len(observed) == len(expected) == report['problems'],
            'incomplete browser population')
    by_id = {row['problem_id']: row for row in expected}
    require(len(by_id) == len(expected) and len({r['problem_id'] for r in observed}) == len(observed),
            'duplicate browser identity')
    slots = {row['problem_id']: row for row in queue['problems']}
    evidence, failures, case_count = [], [], 0
    for result in observed:
        pid = result['problem_id']
        require(pid in by_id and pid in slots, 'browser identity outside declared population')
        source, problem = by_id[pid], slots[pid]
        slot = problem['implementations']['javascript']
        require(problem['permission'] == 'source_access_authorized' and
                slot['qualification']['receipt_binding_checked'], 'source not authorized and qualified')
        bindings = slot['bindings']
        require(set(bindings) == set(BINDINGS) and
                sha(source['source'].encode()) == source['source_sha256'] == bindings['source_sha256'] and
                source['tests_sha256'] == bindings['tests_sha256'] and
                source['interface_sha256'] == bindings['interface_sha256'] and
                source['receipt_sha256'] == slot['qualification']['receipt_sha256'],
                'exact canonical source/contract/receipt join required')
        require(source['entrypointAdapter'] in ADAPTERS and
                all(result[k] == source[k] for k in ('source_sha256', 'tests_sha256', 'receipt_sha256')),
                'browser observation source/adapter mismatch')
        require(result.get('entrypointAdapter', source['entrypointAdapter']) == source['entrypointAdapter'] and
                result.get('bindings', bindings) == bindings, 'observation binding drift')
        tests, batches = source['tests'], result['batches']
        require(type(result['cases']) is int and result['cases'] == len(tests) > 0 and batches,
                'missing browser cases')
        cursor, passed = 0, True
        for batch in batches:
            require(type(batch['start']) is int and batch['start'] == cursor and
                    type(batch['count']) is int and 1 <= batch['count'] <= 4 and
                    type(batch['passed']) is bool, 'missing, overlapping or invalid browser batch')
            cursor += batch['count']
            require(cursor <= len(tests), 'browser batch exceeds cases')
            require((batch['result'] is None) if batch['passed'] else isinstance(batch['result'], str),
                    'browser outcome/detail mismatch')
            passed = passed and batch['passed']
        require(cursor == len(tests) and result['passed'] is passed, 'incomplete or inconsistent browser outcome')
        case_count += cursor
        if not passed:
            failures.append(pid)
            continue
        evidence.append({'problem_id': pid, 'language': 'javascript', 'kind': 'browser_adapter',
            'bindings': dict(bindings), 'evidence': {
                'schema': 'gamma.browser-return-mutation-replay.v1',
                'bundle_sha256': bundle_sha256, 'report_sha256': report_sha256,
                'browser_fixture_sha256': digest(tests), 'case_count': len(tests),
                'entrypoint_adapter': source['entrypointAdapter'], 'runner_sha256': dict(runner_hashes),
                'runtime_sha256': runtime_sha256, 'receipt_sha256': source['receipt_sha256'],
                'return_mutation_batches_verified': True, 'source_bytes_unchanged': True,
                'identity_alias_acceptance': False, 'host_api_acceptance': False,
                'license_acceptance': False, 'independent_correctness_qualification': False,
                'browser_guide_admission': False}})
    return {'schema': 'gamma.browser-replay-evidence-verification.v1', 'records': evidence,
            'problems': len(expected), 'cases': case_count, 'passed': len(evidence),
            'failed_problem_ids': failures, 'admission_performed': False}
