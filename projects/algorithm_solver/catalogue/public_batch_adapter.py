"""Prospective source-specific adoption of independently reviewed public batches.

Operator-pinned plans/authority reviews are external trust inputs, never request
fields. No candidates execute here. Exact sibling verifiers replay observations;
source acquisition, publication, runtime execution and recognition stay separate.
"""
import copy
import hashlib
import importlib.util
import json
import os
import stat
from pathlib import Path
import re
import sys
import threading

from . import boundary_policy
from .catalogue import BINDINGS, digest, hash_value, validate

HERE = Path(__file__).resolve().parent
LANES = {
    'eight-v3': 'public-domain-qualification-v3',
    'easy16-v1': 'public-domain-qualification-easy16-v1',
    'hard10-v1': 'public-domain-qualification-hard10-v1',
    'easy32-wave1-v1': 'public-domain-qualification-easy32-v1',
    'easy32-wave2-v1': 'public-domain-qualification-easy32-wave2-v1',
    'easy32-wave3-v1': 'public-domain-qualification-easy32-wave3-v1',
    'easy32-wave4-v1': 'public-domain-qualification-easy32-wave4-v1',
    'hard32-wave1-v1': 'public-domain-qualification-hard32-v1',
    'medium32-wave1-v1': 'public-domain-qualification-medium32-v1',
    'medium32-wave2-v1': 'public-domain-qualification-medium32-wave2-v1',
    'medium32-wave2-memory-v1': 'public-domain-qualification-medium32-wave2-memory-v1',
    'medium32-wave2-observer-v1': 'public-domain-qualification-medium32-wave2-observer-v1',
    'medium32-wave3-v1': 'public-domain-qualification-medium32-wave3-v1',
    'medium32-wave4-v1': 'public-domain-qualification-medium32-wave4-v1',
    'hard32-wave2-numeric-v2': 'public-domain-qualification-hard32-wave2-numeric-v2',
    'hard32-wave3-transport-v2': 'public-domain-qualification-hard32-wave3-transport-v2',
    'hard32-wave4-v1': 'public-domain-qualification-hard32-wave4-v1',
}
_IMPORT_LOCK = threading.RLock()
LANGUAGES = ('javascript', 'python')


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def fields(value, required):
    if not isinstance(value, dict) or set(value) != set(required):
        raise ValueError('unexpected or missing adoption fields')


def bounded_regular_read(path, *, maximum_bytes=64 * 1024**2):
    """Read an absolute regular file through no-follow anchored directory handles.

    This is an OS-level reader, not an authorization/qualification policy. The
    live per-ID gate still runs before source/statement calls. Frozen historical
    materializer/judge modules remain untouched.
    """
    raw_path = os.fspath(path)
    if (not isinstance(raw_path, str) or not raw_path.startswith('/') or
            any(part in ('', '.', '..') for part in raw_path[1:].split('/')) or
            type(maximum_bytes) is not int or not 0 < maximum_bytes <= 64 * 1024**2):
        raise ValueError('absolute canonical file path and bounded size required')
    parts = raw_path[1:].split('/')
    directory = os.open('/', os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        for part in parts[:-1]:
            child = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=directory)
            os.close(directory)
            directory = child
        fd = os.open(parts[-1], os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=directory)
        try:
            before = os.fstat(fd)
            if not stat.S_ISREG(before.st_mode) or before.st_size > maximum_bytes:
                raise ValueError('artifact must be a bounded regular file')
            with os.fdopen(fd, 'rb', closefd=False) as stream:
                data = stream.read(maximum_bytes + 1)
            after = os.fstat(fd)
            if len(data) > maximum_bytes or (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns, before.st_ctime_ns) != (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns, after.st_ctime_ns):
                raise ValueError('artifact changed during bounded read')
            return data
        finally:
            os.close(fd)
    finally:
        os.close(directory)


def guarded_path_class(source_paths=()):
    """Narrow verifier Path reads without changing frozen oracle/verdict code."""
    source_names = frozenset(os.fspath(p) for p in source_paths)
    class ReplayPath(type(Path())):
        def read_bytes(self):
            maximum = 1_048_576 if str(self) in source_names else (4 * 1024**2 if self.suffix in ('.stdout', '.stderr') else 64 * 1024**2)
            return bounded_regular_read(self.absolute(), maximum_bytes=maximum)
        def read_text(self, encoding=None, errors=None):
            return self.read_bytes().decode(encoding or 'utf-8', errors or 'strict')
    return ReplayPath


def pinned(spec):
    fields(spec, ('path', 'sha256'))
    if not isinstance(spec['path'], str) or not Path(spec['path']).is_absolute() or not hash_value(spec['sha256']):
        raise ValueError('invalid operator-pinned artifact')
    raw = bounded_regular_read(spec['path'])
    if len(raw) > 64 * 1024**2 or sha(raw) != spec['sha256']:
        raise ValueError('pinned adoption artifact mismatch')
    def unique(pairs):
        out = {}
        for key, value in pairs:
            if key in out:
                raise ValueError('duplicate adoption JSON key')
            out[key] = value
        return out
    return json.loads(raw, object_pairs_hook=unique,
        parse_constant=lambda _: (_ for _ in ()).throw(ValueError('nonfinite adoption JSON'))), raw


def lane_path(lane):
    if not isinstance(lane, str) or lane not in LANES:
        raise ValueError('unsupported reviewed verifier lane')
    return HERE / LANES[lane]


def check_observation_policy(lane, freeze):
    # A property comparator is admitted only for the exact reviewed lane/ID set,
    # not as a general relaxation of ordered equality in historical batches.
    lane_path(lane)
    expected = 'exact typed ordered structures'
    if lane == 'easy32-wave1-v1':
        if freeze.get('ids') != [1317, 1351, 1470, 1556, 1598, 1716, 1800, 1854]:
            raise ValueError('property comparator requires exact reviewed population')
        expected += ' except1317 any valid positive no-zero pair'
    medium = {
        'medium32-wave1-v1': ([1248, 1319, 1338, 1400, 1466, 1471, 1482, 1540],
            'typed exact scalars; ID1471 duplicate-sensitive multiset, arbitrary order; local read-only/fresh-return effects'),
        'medium32-wave2-v1': ([1567, 1573, 1630, 1653, 1743, 1817, 1877, 1887],
            'typed exact scalars and ordered lists; ID1743 relational unique-vertex adjacent path, either orientation; local read-only/fresh-return effects'),
    }
    medium['medium32-wave3-v1'] = ([1894,1911,1921,1953,1976,2079,2131,2135], 'exact typed integer scalar; local read-only effects')
    medium['medium32-wave4-v1'] = ([2170,2186,2256,2433,2587,2597,2602,2860], 'exact typed integer scalar/list; local read-only effects')
    medium['medium32-wave2-memory-v1'] = medium['medium32-wave2-v1']
    medium['medium32-wave2-observer-v1'] = medium['medium32-wave2-v1']
    if lane == 'hard32-wave2-numeric-v2':
        if freeze.get('ids') != [1515, 1521, 1542, 1585, 1713, 2111, 2127]:
            raise ValueError('numerical comparator requires exact reviewed seven-ID population')
        expected = '1515 finite numerical absolute tolerance 1e-5 with exact binary-float conversion and analytic oracle uncertainty guard; other results exact typed scalar; local read-only effects'
    if lane == 'hard32-wave3-transport-v2':
        if freeze.get('ids') != [2132,2267,2290,2426,2565,2569,2573,2663]:
            raise ValueError('integer transport comparator requires exact reviewed eight-ID population')
        expected = 'exact typed scalar/list; ID2569 canonical integer transport tags decoded in both languages; local read-only effects'
    if lane == 'hard32-wave4-v1':
        if freeze.get('ids') != [2709,2781,2953,3003,3041,3093,3130]:
            raise ValueError('Hard4 exact comparator requires reviewed seven-ID population')
        expected = 'exact typed integer scalar/list; local read-only effects'
    if lane in medium:
        population, expected = medium[lane]
        if freeze.get('ids') != population:
            raise ValueError('relational comparator requires exact reviewed population')
    if (freeze.get('effect_policy') != 'read-only args; fresh mutable returns; no result-to-input aliases' or
            freeze.get('result_policy') != expected):
        raise ValueError('unsupported local observation policy')



def qualification_caveats(lane, pid):
    caveats = ['Finite independent tests and algorithm review are not universal correctness proof.',
        'Run the frozen input validator before candidate execution; arbitrary-input oracle service is not qualified.',
        'Acquisition/availability does not grant source publication, recognition, or current-serving execution qualification.']
    if lane == 'hard32-wave2-numeric-v2' and pid == 1515:
        caveats.extend([
            '1515 finite numerical evidence uses 20 analytic point/line/symmetric/majority/three-point fixtures and static algorithm review, not a general geometric-median oracle.',
            '1515 accepts finite numerical returns within absolute 1e-5, conservatively reduced by the frozen 1e-35 analytic-oracle uncertainty guard; equality of floating encodings is not required.',
            'The complete official point domain is validated, but arbitrary-input correctness verification is not established by this finite analytic fixture set.'])
    if lane == 'hard32-wave3-transport-v2':
        if pid == 2569:
            caveats.append('2569 exact integer lists use existing canonical large-integer transport tags in both language harnesses; normalization does not permit floating tolerance, malformed tags, bools or a different outer result type.')
        if pid == 2573:
            caveats.append('2573 official matrix size up to1000 is validated, but finite executed fixtures reach100; complete1000-square matrix transport exceeds unchanged packet/output limits. No maximum-domain execution or universal correctness proof is claimed.')
        if pid == 2663:
            caveats.append('2663 full official length up to100000 is validated; finite executed lexical fixtures have length at most8. Static complexity review is separate from maximum-length execution evidence.')
    if lane == 'hard32-wave4-v1' and pid == 2709:
        caveats.append('2709 requires an exact boolean in both language profiles. The historical frozen batch policy label says integer scalar/list as shorthand; the independently pinned per-ID oracle and authority define boolean semantics and reject integer1 for true.')
    if lane == 'request-next4-v1':
        from . import request_next4_oracles as oracle
        if pid not in oracle.IDS:
            raise ValueError('problem outside the fixed next-four lane')
        caveats.extend([f'{pid}: exactly {oracle.CASE_COUNT[pid]} cases per language; no full-domain performance claim.',
                       oracle.OMITTED_MAXIMUM_SHAPES[pid]])
    return caveats


def _module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


def replay(lane, freeze, report_path, *, source_paths=()):
    """Import only fixed code paths after matching every frozen sibling code pin."""
    directory = lane_path(lane)
    for name in ('oracle.py', 'cases.py', 'qualify.py', 'verify.py'):
        key = 'catalogue/' + directory.name + '/' + name
        if sha((directory / name).read_bytes()) != freeze['code_sha256'].get(key):
            raise ValueError('unreviewed verifier code change')
    with _IMPORT_LOCK:
        saved = {name: sys.modules.get(name) for name in ('oracle', 'cases', 'qualify')}
        try:
            for name in saved:
                sys.modules[name] = _module('_public_batch_' + name, directory / (name + '.py'))
            verifier = _module('_public_batch_verifier', directory / 'verify.py')
            safe_path = guarded_path_class(source_paths)
            # Local imported modules only; never patch pathlib or another service.
            for module in [verifier, *(sys.modules[name] for name in saved)]:
                if hasattr(module, 'Path'):
                    module.Path = safe_path
            return verifier.verify(safe_path(report_path))
        finally:
            for name, value in saved.items():
                if value is None:
                    sys.modules.pop(name, None)
                else:
                    sys.modules[name] = value


def check_authority(authority, *, lane, freeze_sha256, review_sha256, ids):
    """A hash-pinned independent review, not an `official=True` source claim."""
    fields(authority, ('schema', 'lane', 'freeze_sha256', 'review_sha256', 'reviewer',
        'review_scope', 'contracts', 'evidence_artifacts', 'source_publication_authorized'))
    if (authority['schema'] != 'gamma.public-batch-authority-review.v1' or
            authority['lane'] != lane or authority['freeze_sha256'] != freeze_sha256 or
            authority['review_sha256'] != review_sha256 or
            not isinstance(authority['reviewer'], str) or not authority['reviewer'].strip() or
            authority['review_scope'] != 'independent-statement-identity-domain-interface-effects-complexity' or
            authority['source_publication_authorized'] is not False):
        raise ValueError('independent statement authority binding required')
    if not isinstance(authority['contracts'], dict) or set(authority['contracts']) != {f'leetcode:{pid}' for pid in ids}:
        raise ValueError('authority review must cover exact frozen IDs')
    if not isinstance(authority['evidence_artifacts'], list) or not authority['evidence_artifacts']:
        raise ValueError('reviewed source authority evidence required')
    for row in authority['evidence_artifacts']:
        fields(row, ('identity', 'sha256', 'role'))
        if not isinstance(row['identity'], str) or not row['identity'] or not hash_value(row['sha256']) or row['role'] not in ('official-statement', 'reviewed-statement-snapshot', 'identity-clause-override'):
            raise ValueError('invalid independently reviewed authority evidence')
    for gid, contract in authority['contracts'].items():
        fields(contract, ('problem_id', 'numeric_problem_id', 'statement_sha256', 'source_identity',
            'domain', 'interface', 'result', 'complexity', 'local_effects', 'authority_evidence_sha256'))
        if (contract['problem_id'] != gid or type(contract['numeric_problem_id']) is not int or
                gid != 'leetcode:' + str(contract['numeric_problem_id']) or not hash_value(contract['statement_sha256']) or
                not isinstance(contract['source_identity'], dict) or not contract['source_identity'] or
                not isinstance(contract['domain'], (dict, str)) or not contract['domain'] or
                not isinstance(contract['result'], (dict, str)) or not contract['result'] or
                not isinstance(contract['complexity'], (dict, str)) or not contract['complexity'] or
                not isinstance(contract['local_effects'], dict) or not contract['local_effects']):
            raise ValueError('incomplete reviewed per-problem contract')
        interface = contract['interface']
        fields(interface, ('entrypoint', 'arguments', 'parameters'))
        if interface['entrypoint'] != 'solve' or interface['arguments'] != 'ordered-positional' or not isinstance(interface['parameters'], (list, str)) or not interface['parameters']:
            raise ValueError('inconsistent reviewed call interface')
        witnesses = contract['authority_evidence_sha256']
        allowed = {r['sha256'] for r in authority['evidence_artifacts']}
        if not isinstance(witnesses, list) or not witnesses or len(set(witnesses)) != len(witnesses) or not set(witnesses) <= allowed:
            raise ValueError('per-problem authority has no bound evidence')
    return authority['contracts']


def replace_canonicals(universe, catalogue, receipts, replacements, additions):
    """Preserve every previous receipt and unselected slot; no fixed coverage count."""
    before = validate(universe, catalogue, receipts)
    result, retained = copy.deepcopy(catalogue), copy.deepcopy(receipts)
    rows = {r['problem_id']: r for r in result['problems']}
    for (pid, language), impl in replacements.items():
        if pid not in rows or pid in universe['protected_problem_ids'] or language not in LANGUAGES:
            raise ValueError('unknown/protected replacement identity')
        old = rows[pid]['implementations'][language]
        prior = impl.get('provenance', {}).get('previous_canonical', {})
        if prior.get('implementation_sha256') != digest(old) or prior.get('receipt_sha256') != old.get('receipt_sha256'):
            raise ValueError('previous canonical archival binding mismatch')
        if impl.get('status') != 'qualified' or impl.get('evidence_class') != 'normative-typed-effects':
            raise ValueError('only independently qualified reviewed-domain artifacts')
        rows[pid]['implementations'][language] = copy.deepcopy(impl)
    for rid, receipt in additions.items():
        if rid != digest(receipt) or (rid in retained and retained[rid] != receipt):
            raise ValueError('immutable receipt collision/identity mismatch')
        retained[rid] = copy.deepcopy(receipt)
    after = validate(universe, result, retained)
    if before['eligible_problems'] != after['eligible_problems']:
        raise ValueError('denominator changed')
    return result, retained, after


# This route does not relabel imported execution artifacts as a public batch.
# It checks their native identities and replays only retained observations.
REQUEST3215_LANE = 'request3215-v1'
REQUEST3215_REVIEW = frozenset(('boundary_policy', 'statement_identity', 'domain',
    'interface', 'local_effects', 'complexity', 'raw_observations', 'native_runtime_identity'))


def relocated_artifact(path, native_root, local_root):
    """Explicit artifact-only relocation; never rewrite a native run contract."""
    for value in (path, native_root, local_root):
        if (not isinstance(value, str) or not value.startswith('/') or
                any(part in ('', '.', '..') for part in value[1:].split('/'))):
            raise ValueError('canonical absolute artifact mapping required')
    try:
        relative = Path(path).relative_to(native_root)
    except ValueError:
        raise ValueError('artifact outside explicit native bundle root') from None
    if not relative.parts:
        raise ValueError('artifact file required, not bundle root')
    return Path(local_root) / relative


def _request_observations(report, jobs, cases_by_id, report_dir):
    """Recompute verdicts with the existing independent comparator, never flags."""
    from . import imported_qualification as q
    from . import verify_imported_qualification as verifier
    if [(r.get('id'), r.get('language')) for r in report['rows']] != [(j['id'], j['language']) for j in jobs]:
        raise ValueError('missing, duplicate or reordered source outcomes')
    outcomes = []
    for job, row in zip(jobs, report['rows']):
        cases = cases_by_id[job['id']]
        groups = list(q.batches(cases))
        if row['source_sha256'] != job['source_sha256'] or row['cases'] != len(cases) or len(row['calls']) != len(groups):
            raise ValueError('source/case/batch population mismatch')
        failures = []
        for call, (offset, batch) in zip(row['calls'], groups):
            stem = f"{job['id']}-{job['language']}-{offset}"
            if call['stem'] != stem or call['offset'] != offset or call['count'] != len(batch):
                raise ValueError('batch binding mismatch')
            stdout = bounded_regular_read(report_dir / (stem + '.stdout'), maximum_bytes=q.LIMITS['max_output_bytes'])
            stderr = bounded_regular_read(report_dir / (stem + '.stderr'), maximum_bytes=q.LIMITS['max_output_bytes'])
            if sha(stdout) != call['stdout_sha256'] or sha(stderr) != call['stderr_sha256']:
                raise ValueError('raw observation hash mismatch')
            if type(call['exit_code']) is not int or call['exit_code'] != 0 or call['timed_out'] is not False or call['output_limit_exceeded'] is not False:
                failures.append({'offset': offset, 'reason': 'isolated_execution_failed'})
            else:
                failures.extend({'offset': offset, **f} for f in
                    verifier.independent_failures(stdout, batch, job['language'], 'exact'))
        if row['failures'] != failures or row['passed'] is not (not failures):
            raise ValueError('independent raw observation replay disagrees')
        outcomes.append({'id': job['id'], 'language': job['language'], 'passed': not failures,
            'source_sha256': job['source_sha256'], 'tests_raw_sha256': job['tests_raw_sha256'],
            'cases': len(cases), 'failure_count': len(failures)})
    return outcomes


def request3215_observations(report, jobs, cases, report_dir):
    """Preserve the original single-problem comparator entry point."""
    return _request_observations(report, jobs, {job['id']: cases for job in jobs}, report_dir)


def replay_request3215(plan, values, raws):
    """Fixed domain owner plus native pins; no host runtime substitution or run."""
    from collections import Counter
    from . import imported_qualification as q
    from . import request_qualification as request
    from . import verify_imported_qualification as verifier
    freeze, report, verification, review = (values[k] for k in ('freeze', 'report', 'verification', 'review'))
    native, local = plan['native_bundle_root'], plan['artifact_root']

    def mapped(path):
        return relocated_artifact(path, native, local)

    native_freeze = native + '/run-3215/freeze'
    if (mapped(native_freeze + '/contract.json') != Path(plan['freeze']['path']) or
            mapped(native + '/run-3215/observations/report.json') != Path(plan['report']['path']) or
            mapped(native + '/run-3215/independent-verification.json') != Path(plan['verification']['path']) or
            report.get('freeze') != native_freeze or report.get('freeze_sha256') != sha(raws['freeze']) or
            report.get('schema') != 'gamma.imported-independent-report.v1' or
            report.get('status') != 'completed' or report.get('new_qualifications') != 0):
        raise ValueError('native report/freeze mapping or completion mismatch')
    jobs = freeze.get('jobs', [])
    if (freeze.get('schema') != 'gamma.imported-independent-execution.v1' or
            freeze.get('selected_problem_ids') != [request.PID] or
            [(j.get('id'), j.get('language')) for j in jobs] != [(request.PID, lang) for lang in LANGUAGES] or
            freeze.get('pending') != [] or freeze.get('automatic_promotion') is not False or
            freeze.get('protected_access') is not False or freeze.get('limits') != q.LIMITS or
            freeze.get('max_packet_bytes') != q.MAX_PACKET):
        raise ValueError('fixed request population, limits or execution scope differs')
    # Reject all interface/locator changes before any source, statement or case read.
    for job in jobs:
        language = job['language']; suffix = 'js' if language == 'javascript' else 'py'
        fields(job, ('id', 'language', 'source', 'source_sha256', 'original_source', 'tests',
            'tests_raw_sha256', 'tests_canonical_sha256', 'case_count', 'statement',
            'domain_validator', 'comparison_policy', 'source_interface'))
        expected_interface = 'commonjs-object-solve-v1' if language == 'javascript' else 'global-solve-v1'
        if (q.source_interface(job) != expected_interface or job['source'] != f'sources/3215.{suffix}' or
                job['tests'] != 'tests/3215.json' or job['source_sha256'] != request.SOURCE_SHA256[language] or
                job['original_source'] != native + f'/inputs/sources/{language}/3215.{suffix}' or
                job['statement'] != {'path': native_freeze + '/statement.md', 'sha256': request.STATEMENT_SHA256} or
                job['domain_validator'] != REQUEST3215_LANE or job['comparison_policy'] != 'exact' or
                job['case_count'] != request.CASE_COUNT or job['tests_raw_sha256'] != request.CASES_SHA256):
            raise ValueError('fixed source/domain/interface binding differs')
    # Compare native code identities by repository-relative name, including every
    # helper. Current trusted comparator bytes must match the retained copy too.
    repo = HERE.parents[2]
    expected_code = {native + '/code/' + str(Path(path).relative_to(repo)): value for path, value in q.code_pins().items()}
    generator = native + '/code/' + str(Path(request.__file__).relative_to(repo))
    verifier_path = native + '/code/' + str(Path(verifier.__file__).relative_to(repo))
    if freeze.get('code') != expected_code or freeze.get('additional_code') != {generator: expected_code[generator]}:
        raise ValueError('frozen code population or bytes differ')
    for path, expected in {**expected_code, verifier_path: q.file_hash(verifier.__file__)}.items():
        if sha(bounded_regular_read(mapped(path))) != expected:
            raise ValueError('retained frozen code differs')
    runtime = freeze.get('runtime')
    if not isinstance(runtime, dict) or not {'/usr/bin/node', '/usr/bin/python3', '/usr/bin/bwrap', '/usr/bin/prlimit'} <= set(runtime):
        raise ValueError('native runtime identity missing')
    for path, identity in runtime.items():
        fields(identity, ('resolved', 'sha256'))
        if not Path(path).is_absolute() or not Path(identity['resolved']).is_absolute() or not hash_value(identity['sha256']):
            raise ValueError('invalid native runtime identity')
    if (review.get('independent_review') is not True or
            not REQUEST3215_REVIEW <= set(review.get('reviewed', [])) or
            any(review.get(k + '_sha256') != sha(raws[k]) for k in ('freeze', 'report', 'verification')) or
            review.get('source_sha256') != request.SOURCE_SHA256 or
            review.get('native_runtime_sha256') != digest(runtime)):
        raise ValueError('independent exact-source/native-runtime review required')
    gate, native_gate, service = (values[k] for k in ('boundary_gate', 'qualification_boundary_gate', 'qualification_service'))
    fields(gate, ('schema', 'artifact_paths', 'trusted_hashes'))
    fields(native_gate, ('schema', 'artifact_paths', 'trusted_hashes'))
    if (gate['schema'] != 'gamma.boundary-gate-config.v1' or native_gate['schema'] != gate['schema'] or
            gate['trusted_hashes'] != native_gate['trusted_hashes'] or
            gate['trusted_hashes']['universe'] != sha(raws['universe']) or
            freeze.get('service_config_sha256') != sha(raws['qualification_service']) or
            service.get('schema') != 'gamma.known-spec-service.v2' or
            service['source_access']['boundary_gate']['sha256'] != sha(raws['qualification_boundary_gate']) or
            any(service[name]['sha256'] != sha(raws[key]) for name, key in
                (('universe', 'universe'), ('catalogue', 'catalogue'), ('verified_receipts', 'receipts')))):
        raise ValueError('current base and native acquisition authority differ')
    for language in LANGUAGES:
        boundary_policy.authorize_before_open(request.IDENTITY, gate['artifact_paths'], gate['trusted_hashes'], language=language)
    boundary_policy.authorize_before_open(request.IDENTITY, gate['artifact_paths'], gate['trusted_hashes'], language='python', payload_kind='statement')
    contracts = check_authority(values['authority_review'], lane=REQUEST3215_LANE,
        freeze_sha256=sha(raws['freeze']), review_sha256=sha(raws['review']), ids=[request.PID])
    if contracts[request.IDENTITY]['statement_sha256'] != request.STATEMENT_SHA256:
        raise ValueError('reviewed statement differs from fixed definition')
    root = mapped(native_freeze + '/contract.json').parent
    pre, _ = pinned({'path': str(root / 'pre-source-freeze.json'), 'sha256': freeze['pre_source_freeze_sha256']})
    provenance, _ = pinned({'path': str(root / 'case-provenance.json'), 'sha256': freeze['case_provenance_sha256']})
    if (pre.get('schema') != 'gamma.request3215-pre-source-freeze.v1' or pre.get('problem_ids') != [request.PID] or
            pre.get('source_payload_reads_at_freeze') != 0 or pre.get('manifest_sha256') != request.MANIFEST_SHA256 or
            pre.get('statement_sha256') != request.STATEMENT_SHA256 or pre.get('cases_per_language') != request.CASE_COUNT or
            pre.get('tests_raw_sha256') != request.CASES_SHA256 or pre.get('expected_source_sha256') != request.SOURCE_SHA256 or
            pre.get('generator_validator_sha256') != expected_code[generator] or pre.get('observer_code') != expected_code or
            pre.get('limits') != q.LIMITS or pre.get('max_packet_bytes') != q.MAX_PACKET):
        raise ValueError('pre-source freeze differs')
    manifest, _ = pinned({'path': str(mapped(native + '/inputs/manifest.json')), 'sha256': request.MANIFEST_SHA256})
    originals = [row for row in manifest if row.get('problem_id') == request.PID]
    if len(originals) != 1:
        raise ValueError('original authoring manifest identity missing')
    original = originals[0]
    for language, suffix in (('javascript', 'js'), ('python', 'py')):
        if original['source_files'][language] != {'path': f'{language}/3215.{suffix}', 'sha256': request.SOURCE_SHA256[language]}:
            raise ValueError('original authoring source identity differs')
    if original['definition_provenance']['definition_prefix_sha256'] != request.STATEMENT_SHA256:
        raise ValueError('original authoring definition differs')
    boundary_policy.authorize_before_open(request.IDENTITY, gate['artifact_paths'], gate['trusted_hashes'], language='python', payload_kind='statement')
    statement = bounded_regular_read(root / 'statement.md', maximum_bytes=131072)
    cases, categories = request.build_cases(statement)
    actual_cases = bounded_regular_read(root / 'tests/3215.json')
    groups = list(q.batches(cases))
    if (sha(actual_cases) != request.CASES_SHA256 or actual_cases != q.encoded(cases) or
            any(job['tests_canonical_sha256'] != q.canonical_tests_hash(cases) for job in jobs) or
            pre.get('batch_count_per_language') != len(groups) or
            pre.get('largest_packet_bytes') != max(len(q.encoded(q.packet(batch))) for _, batch in groups) or
            provenance != {'seed': request.SEED, 'categories': categories, 'counts': dict(Counter(categories)), 'predecessor': request.ORACLE_PREDECESSOR}):
        raise ValueError('fixed generated cases or provenance differs')
    for job in jobs:
        boundary_policy.authorize_before_open(request.IDENTITY, gate['artifact_paths'], gate['trusted_hashes'], language=job['language'])
        if sha(bounded_regular_read(root / job['source'], maximum_bytes=1_048_576)) != job['source_sha256']:
            raise ValueError('exact passed source bytes differ')
    outcomes = request3215_observations(report, jobs, cases, Path(plan['report']['path']).parent)
    replayed = {'schema': 'gamma.imported-independent-verification.v1', 'verified': True,
        'report_sha256': sha(raws['report']), 'freeze_sha256': sha(raws['freeze']),
        'verifier_sha256': q.file_hash(verifier.__file__), 'outcomes': outcomes,
        'passed': sum(o['passed'] for o in outcomes), 'total': len(outcomes),
        'cases': sum(o['cases'] for o in outcomes), 'new_qualifications': 0,
        'scope': freeze['scope'], 'automatic_promotion': False}
    if replayed != verification or not all(row['passed'] for row in outcomes):
        raise ValueError('actual independent verification differs or failed')
    return contracts, original, root


def adopt_request3215_plan(plan, trusted_plan_sha256):
    """Return reversible candidate data only; never persist or activate service."""
    from . import request_qualification as request
    fields(plan, ('schema', 'universe', 'catalogue', 'receipts', 'boundary_gate', 'freeze',
        'report', 'verification', 'review', 'authority_review', 'qualification_service',
        'qualification_boundary_gate', 'native_bundle_root', 'artifact_root'))
    if plan['schema'] != 'gamma.request3215-adoption-plan.v1':
        raise ValueError('unsupported fixed request plan')
    values, raws = {}, {}
    for key in set(plan) - {'schema', 'native_bundle_root', 'artifact_root'}:
        values[key], raws[key] = pinned(plan[key])
    universe, catalogue, receipts = (values[k] for k in ('universe', 'catalogue', 'receipts'))
    before = validate(universe, catalogue, receipts)
    contracts, original, root = replay_request3215(plan, values, raws)
    freeze = values['freeze']; gid = request.IDENTITY
    rows = {row['problem_id']: row for row in catalogue['problems']}
    replacements, additions, locators, descriptors = {}, {}, {}, {}
    prefix = plan['native_bundle_root'] + '/code/projects/algorithm_solver/'
    code = freeze['code']; generator_sha = code[prefix + 'catalogue/request_qualification.py']
    for job in freeze['jobs']:
        language = job['language']; old = rows[gid]['implementations'][language]
        contract = {'schema': 'gamma.reviewed-public-batch-contract.v1', 'reviewed_statement_contract': contracts[gid],
            'authority_review_sha256': sha(raws['authority_review']), 'qualification_freeze_sha256': sha(raws['freeze']),
            'input_validator': {'lane': REQUEST3215_LANE, 'module_sha256': generator_sha,
                'numeric_problem_id': request.PID, 'entrypoint': 'validate', 'required_before_candidate_execution': True}}
        interface = {'schema': 'gamma.call-interface.v1', 'entrypoint': 'solve',
            'arguments': 'ordered-positional', 'typed_contract': digest(contract)}
        runtime = {'language': language, 'runtime': freeze['runtime'], 'limits': freeze['limits'],
            'sandbox_sha256': code[prefix + 'algsolve/judge/sandbox.py'],
            'runner_sha256': code[prefix + 'catalogue/imported_qualification.py'],
            'source_interface': job['source_interface'], 'native_runtime_only': True}
        harness = ('imported-commonjs-observer-v1/harness.cjs' if language == 'javascript' else
                   'public-domain-qualification-medium32-wave2-observer-v1/harness.py')
        effects = {'local_effects': contracts[gid]['local_effects'], 'observed_effect_policy': freeze['effects'],
            'observed_result_policy': freeze['comparison'], 'oracle_sha256': generator_sha,
            'harness_sha256': code[prefix + 'catalogue/' + harness],
            'observer_helper_sha256': code[prefix + 'catalogue/public-domain-qualification-medium32-wave2-observer-v1/harness.cjs'] if language == 'javascript' else None,
            'verifier_sha256': values['verification']['verifier_sha256'], 'review_sha256': sha(raws['review'])}
        provenance = {'public_batch': {'lane': REQUEST3215_LANE, 'problem_contract': contract,
            'source_provenance': {'original_manifest_sha256': request.MANIFEST_SHA256,
                'original_manifest_path': 'projects/algorithm_solver/catalogue/authored/request-252-v1/batch1/manifest.json',
                'original_source': original['source_files'][language], 'frozen_job': job},
            'report_sha256': sha(raws['report']), 'verification_sha256': sha(raws['verification']),
            'review_sha256': sha(raws['review']), 'case_count': request.CASE_COUNT},
            'previous_canonical': {'implementation_sha256': digest(old), 'receipt_sha256': old.get('receipt_sha256'),
                'base_catalogue_sha256': sha(raws['catalogue']), 'implementation': copy.deepcopy(old)},
            'source_publication_authorized': False, 'historical_receipts_unchanged': True}
        scope = 'Reviewed problem 3215 domain; exact source-specific solve interface, numeric and local-effect contract.'
        caveats = qualification_caveats(REQUEST3215_LANE, request.PID) + [
            '815 finite public-definition cases per language, not fresh heldout confirmation or full-domain performance qualification.',
            'Native runtime identity belongs to the recorded execution host; relocated replay does not establish another host or browser runtime.',
            'Candidate catalogue only; active service configuration and serving source subset remain unchanged.']
        impl = {'status': 'qualified', 'canonical_variant_id': language + ':' + job['source_sha256'],
            'source_sha256': job['source_sha256'], 'problem_contract_sha256': digest(contract),
            'interface': interface, 'interface_sha256': digest(interface), 'runtime_sha256': digest(runtime),
            'tests_sha256': request.CASES_SHA256, 'effects_sha256': digest(effects),
            'evidence_class': 'normative-typed-effects', 'contract_scope': scope, 'caveats': caveats, 'provenance': provenance}
        receipt = {key: impl[key] for key in (*BINDINGS, 'canonical_variant_id', 'evidence_class', 'contract_scope', 'caveats')}
        receipt.update(problem_id=gid, language=language, verdict='qualified', independent_verifier=True,
            provenance_sha256=digest(provenance), original_independent_verification_sha256=sha(raws['verification']),
            review_sha256=sha(raws['review']), per_problem_case_count=request.CASE_COUNT,
            verification_mode='fixed request imported-observation replay plus externally anchored independent authority review')
        rid = digest(receipt); impl['receipt_sha256'] = rid
        replacements[(gid, language)] = impl; additions[rid] = receipt
        locators.setdefault(gid, {})[language] = str(root / job['source'])
        descriptors[f'{language}:3215'] = {'problem_contract': contract, 'runtime': runtime, 'effects': effects}
    updated, retained, summary = replace_canonicals(universe, catalogue, receipts, replacements, additions)
    return {'catalogue': updated, 'verified_receipts': retained, 'summary': summary,
        'source_locators': {'schema': 'gamma.dual.source-locators.v1', 'problems': locators},
        'binding_descriptors': descriptors, 'audit': {'schema': 'gamma.public-batch-adoption.v1',
            'plan_sha256': trusted_plan_sha256, 'adopted_source_language_pairs': len(replacements),
            'previous_receipts_preserved': len(receipts), 'new_receipts': len(additions),
            'source_publication_authorized': False, 'candidate_executions': 0, 'candidate_only': True,
            'active_config_modified': False, 'base_summary': before, 'historical_m1_qualified': False}}


REQUEST_NEXT4_LANE = 'request-next4-v1'
NEXT4_ORIGINAL_EVIDENCE = {
    'original_freeze': ('pre-source-oracle-freeze.json', '41b30609149eaca3305241d2b1a1265c226997e33d6fca994cd5961c159577e2'),
    'original_review': ('independent-pre-source-review-v1.json', '95d85c4f314f4ad68db00476da680d2bbe91f89a2f3e8e0e3471a0b127a9d9bd'),
    'source_acquisition': ('source-acquisition-audit.json', '5d63033097dec0d0d80518dd5cd5ec6af996793386b4afeb5ea17ff8badaf4c2'),
    'source_review': ('independent-source-static-review-v1.json', 'b57627404330f0f9d464525c723e32132461e7ef6a8b970e05acf69c20eaf967'),
}


def check_next4_execution_delta(values, raws):
    """Prove the only intervening change is the already reviewed 3215 pair."""
    from . import request_qualification as predecessor
    universe, old, old_receipts, new, receipts, review = (values[key] for key in
        ('universe', 'execution_catalogue', 'execution_receipts', 'catalogue', 'receipts', 'predecessor_review'))
    validate(universe, old, old_receipts)
    validate(universe, new, receipts)
    artifacts = review.get('candidate_artifact_sha256', {})
    if (artifacts.get('candidate-catalogue.json') != sha(raws['catalogue']) or
            artifacts.get('candidate-verified-receipts.json') != sha(raws['receipts']) or
            not review.get('reviewer') or review.get('service_activation_authorized') is not False or
            review.get('source_publication_authorized') is not False or
            review.get('source_serving_permission_expanded') is not False):
        raise ValueError('independent 3215 predecessor artifact binding required')
    replayed = review.get('independent_observation_replay', {})
    if (replayed.get('actual_new_adapter_read_only_replay_passed') is not True or
            replayed.get('source_language_pairs') != 2 or replayed.get('observations') != 2 * predecessor.CASE_COUNT or
            replayed.get('failures') != 0 or replayed.get('candidate_reexecutions') != 0 or
            replayed.get('original_artifacts_modified') is not False):
        raise ValueError('actual predecessor observation review required')
    restored = copy.deepcopy(new)
    old_rows = {row['problem_id']: row for row in old['problems']}
    new_rows = {row['problem_id']: row for row in restored['problems']}
    added = set()
    for language in LANGUAGES:
        impl = new_rows['leetcode:3215']['implementations'][language]
        prior = impl.get('provenance', {}).get('previous_canonical', {})
        old_impl = old_rows['leetcode:3215']['implementations'][language]
        batch = impl.get('provenance', {}).get('public_batch', {})
        if (impl.get('status') != 'qualified' or impl.get('evidence_class') != 'normative-typed-effects' or
                impl.get('source_sha256') != predecessor.SOURCE_SHA256[language] or
                impl.get('canonical_variant_id') != language + ':' + predecessor.SOURCE_SHA256[language] or
                prior.get('implementation_sha256') != digest(old_impl) or
                digest(prior.get('implementation')) != digest(old_impl) or
                prior.get('receipt_sha256') != old_impl.get('receipt_sha256') or
                prior.get('base_catalogue_sha256') != sha(raws['execution_catalogue']) or
                batch.get('lane') != REQUEST3215_LANE or
                batch.get('problem_contract', {}).get('qualification_freeze_sha256') != review.get('native_freeze_sha256') or
                batch.get('verification_sha256') != review.get('native_independent_verification_sha256') or
                batch.get('report_sha256') != review.get('native_report_sha256') or
                batch.get('review_sha256') != review.get('review_sha256')):
            raise ValueError('exact 3215 predecessor delta differs')
        rid = impl['receipt_sha256']
        if receipts[rid].get('original_independent_verification_sha256') != review.get('native_independent_verification_sha256'):
            raise ValueError('3215 predecessor receipt differs')
        added.add(rid)
        new_rows['leetcode:3215']['implementations'][language] = copy.deepcopy(old_impl)
    # Canonical JSON comparison distinguishes bool/int and preserves row order.
    if digest(restored) != digest(old):
        raise ValueError('unrelated catalogue/header/order change across execution base')
    if (set(receipts) - set(old_receipts) != added or len(added) != 2 or
            any(key not in receipts or digest(receipts[key]) != digest(value) for key, value in old_receipts.items())):
        raise ValueError('original receipts changed or unrelated receipts added')
    return {'execution_catalogue_sha256': sha(raws['execution_catalogue']),
        'execution_receipts_sha256': sha(raws['execution_receipts']),
        'adoption_catalogue_sha256': sha(raws['catalogue']), 'adoption_receipts_sha256': sha(raws['receipts']),
        'preserved_3215_receipts': sorted(added), 'original_receipts_preserved': len(old_receipts),
        'unselected_execution_slots_unchanged': len(old['problems']) * 2 - 2,
        'predecessor_review_sha256': sha(raws['predecessor_review'])}


def check_next4_original_evidence(plan, values, raws, code):
    """Bind before-first-read chronology, not merely the native command freeze."""
    from . import request_next4_qualification as request
    from . import request_next4_oracles as oracle
    native, local = plan['native_bundle_root'], plan['artifact_root']
    for key, (name, expected) in NEXT4_ORIGINAL_EVIDENCE.items():
        if (sha(raws[key]) != expected or Path(plan[key]['path']) !=
                relocated_artifact(native + '/evidence/' + name, native, local)):
            raise ValueError('immutable original evidence identity differs')
    frozen, review, acquisition, static = (values[key] for key in NEXT4_ORIGINAL_EVIDENCE)
    pins = {key: sha(raws[key]) for key in NEXT4_ORIGINAL_EVIDENCE}
    if (frozen.get('source_payload_reads_at_freeze') != 0 or
            frozen.get('original_statement_byte_equivalence_claimed') is not False or
            review.get('reviewed_freeze', {}).get('sha256') != pins['original_freeze'] or
            acquisition.get('pre_source_oracle_freeze_sha256') != pins['original_freeze'] or
            acquisition.get('independent_pre_source_review_sha256') != pins['original_review'] or
            acquisition.get('status') != 'completed' or acquisition.get('source_payload_read_operations') != 8 or
            acquisition.get('unique_candidate_files_acquired') != 8 or acquisition.get('candidate_executions') != 0 or
            acquisition.get('historical_private_case_payload_reads') != 0 or
            acquisition.get('native_original_service_config_sha256') != sha(raws['qualification_service']) or
            static.get('pre_source_oracle_freeze', {}).get('sha256') != pins['original_freeze'] or
            static.get('pre_source_independent_review', {}).get('sha256') != pins['original_review'] or
            static.get('first_acquisition_audit', {}).get('sha256') != pins['source_acquisition'] or
            static.get('case_writes_after_source_exposure_in_this_review') != 0 or
            static.get('candidate_executions_in_this_review') != 0):
        raise ValueError('original freeze/review/acquisition chronology differs')
    expected_pairs = [(pid, language) for pid in request.IDS for language in LANGUAGES]
    if ([(row.get('problem_id'), row.get('language')) for row in acquisition['rows']] != expected_pairs or
            [(row.get('problem_id'), row.get('language')) for row in static['findings']] != expected_pairs):
        raise ValueError('original exact source review population differs')
    for acquired, finding in zip(acquisition['rows'], static['findings']):
        pid, language = acquired['problem_id'], acquired['language']
        if (acquired.get('sha256') != request.SOURCE_SHA256[pid][language] or
                finding.get('source', {}).get('sha256') != request.SOURCE_SHA256[pid][language] or
                finding.get('counterexample_found') is not False or
                finding.get('eligible_for_existing_bounded_execution_route') is not True or
                finding.get('candidate_executed_by_reviewer') is not False):
            raise ValueError('original source-specific static evidence differs')
    prefix = native + '/code/projects/algorithm_solver/catalogue/'
    for name, spec in review['reviewed_code'].items():
        if '/' in name or not name.endswith('.py'):
            raise ValueError('unexpected reviewed code path')
        path = relocated_artifact(prefix + name, native, local)
        if sha(bounded_regular_read(path)) != spec['sha256']:
            raise ValueError('original reviewed code differs')
    if (frozen.get('oracle_module', {}).get('sha256') != code[prefix + 'request_next4_oracles.py'] or
            frozen.get('original_manifest', {}).get('sha256') != request.MANIFEST_SHA256 or
            frozen.get('total_cases_per_language') != sum(oracle.CASE_COUNT.values()) or
            [row.get('problem_id') for row in frozen['problems']] != list(request.IDS)):
        raise ValueError('original generated population differs')
    return {row['problem_id']: row for row in frozen['problems']}


def replay_request_next4(plan, values, raws):
    """Fixed next-four retained replay under unchanged native evidence identities."""
    from . import imported_qualification as q
    from . import request_next4_qualification as request
    from . import request_next4_oracles as oracle
    from . import verify_imported_qualification as verifier
    freeze, report, verification, review = (values[k] for k in ('freeze', 'report', 'verification', 'review'))
    native, local = plan['native_bundle_root'], plan['artifact_root']
    def mapped(path):
        return relocated_artifact(path, native, local)
    native_freeze = native + '/run-next4/freeze'
    if (mapped(native_freeze + '/contract.json') != Path(plan['freeze']['path']) or
            mapped(native + '/run-next4/observations/report.json') != Path(plan['report']['path']) or
            mapped(native + '/run-next4/independent-verification.json') != Path(plan['verification']['path']) or
            report.get('freeze') != native_freeze or report.get('freeze_sha256') != sha(raws['freeze']) or
            report.get('schema') != 'gamma.imported-independent-report.v1' or
            report.get('status') != 'completed' or report.get('new_qualifications') != 0):
        raise ValueError('native next-four replay mapping or completion differs')
    jobs = freeze.get('jobs', [])
    if (freeze.get('schema') != 'gamma.imported-independent-execution.v1' or
            freeze.get('selected_problem_ids') != list(request.IDS) or
            [(j.get('id'), j.get('language')) for j in jobs] != [(pid, lang) for pid in request.IDS for lang in LANGUAGES] or
            freeze.get('pending') != [] or freeze.get('automatic_promotion') is not False or
            freeze.get('protected_access') is not False or freeze.get('original_statement_byte_equivalence') is not False or
            freeze.get('limits') != q.LIMITS or freeze.get('max_packet_bytes') != q.MAX_PACKET):
        raise ValueError('fixed next-four population, limits or scope differs')
    for job in jobs:
        pid, language = job['id'], job['language']; suffix = 'js' if language == 'javascript' else 'py'
        fields(job, ('id', 'language', 'source', 'source_sha256', 'original_source', 'tests',
            'tests_raw_sha256', 'tests_canonical_sha256', 'case_count', 'statement',
            'domain_validator', 'comparison_policy', 'source_interface'))
        interface = 'commonjs-object-solve-v1' if language == 'javascript' else 'global-solve-v1'
        if (q.source_interface(job) != interface or job['source'] != f'sources/{pid}.{suffix}' or
                job['tests'] != f'tests/{pid}.json' or job['source_sha256'] != request.SOURCE_SHA256[pid][language] or
                job['original_source'] != native + f'/inputs/sources/{language}/{pid}.{suffix}' or
                job['statement'] != {'path': native_freeze + f'/statements/{pid}.md', 'sha256': oracle.STATEMENT_SHA256[pid]} or
                job['domain_validator'] != REQUEST_NEXT4_LANE or job['comparison_policy'] != 'exact' or
                job['case_count'] != oracle.CASE_COUNT[pid] or job['tests_raw_sha256'] != oracle.CASES_SHA256[pid]):
            raise ValueError('fixed next-four source/domain/interface differs')
    repo = HERE.parents[2]
    code = {native + '/code/' + str(Path(path).relative_to(repo)): value for path, value in q.code_pins().items()}
    additional = {native + '/code/' + str(Path(path).relative_to(repo)): value for path, value in request.additional_code().items()}
    verifier_path = native + '/code/' + str(Path(verifier.__file__).relative_to(repo))
    if freeze.get('code') != code or freeze.get('additional_code') != additional:
        raise ValueError('frozen next-four code population or bytes differ')
    for path, expected in {**code, verifier_path: q.file_hash(verifier.__file__)}.items():
        if sha(bounded_regular_read(mapped(path))) != expected:
            raise ValueError('retained next-four code differs')
    runtime = freeze.get('runtime')
    if not isinstance(runtime, dict) or not {'/usr/bin/node', '/usr/bin/python3', '/usr/bin/bwrap', '/usr/bin/prlimit'} <= set(runtime):
        raise ValueError('native runtime identity missing')
    for path, identity in runtime.items():
        fields(identity, ('resolved', 'sha256'))
        if not Path(path).is_absolute() or not Path(identity['resolved']).is_absolute() or not hash_value(identity['sha256']):
            raise ValueError('invalid native runtime identity')
    expected_sources = {str(pid): request.SOURCE_SHA256[pid] for pid in request.IDS}
    if (review.get('independent_review') is not True or
            not (REQUEST3215_REVIEW | {'execution_base_delta'}) <= set(review.get('reviewed', [])) or
            any(review.get(k + '_sha256') != sha(raws[k]) for k in
                ('freeze', 'report', 'verification', 'predecessor_review', *NEXT4_ORIGINAL_EVIDENCE)) or
            review.get('source_sha256') != expected_sources or review.get('native_runtime_sha256') != digest(runtime) or
            any(review.get(name + '_sha256') != sha(raws[key]) for name, key in (
                ('execution_catalogue', 'execution_catalogue'), ('execution_receipts', 'execution_receipts'),
                ('adoption_catalogue', 'catalogue'), ('adoption_receipts', 'receipts')))):
        raise ValueError('independent next-four review and execution-base bindings required')
    gate, native_gate, service = (values[k] for k in ('boundary_gate', 'qualification_boundary_gate', 'qualification_service'))
    for item in (gate, native_gate):
        fields(item, ('schema', 'artifact_paths', 'trusted_hashes'))
    if (gate['schema'] != 'gamma.boundary-gate-config.v1' or native_gate['schema'] != gate['schema'] or
            gate['trusted_hashes'] != native_gate['trusted_hashes'] or
            gate['trusted_hashes']['universe'] != sha(raws['universe']) or
            freeze.get('service_config_sha256') != sha(raws['qualification_service']) or
            service.get('schema') != 'gamma.known-spec-service.v2' or
            service['source_access']['boundary_gate']['sha256'] != sha(raws['qualification_boundary_gate']) or
            any(service[name]['sha256'] != sha(raws[key]) for name, key in (
                ('universe', 'universe'), ('catalogue', 'execution_catalogue'), ('verified_receipts', 'execution_receipts')))):
        raise ValueError('native original execution authority differs')
    for pid in request.IDS:
        for language in LANGUAGES:
            boundary_policy.authorize_before_open(f'leetcode:{pid}', gate['artifact_paths'], gate['trusted_hashes'], language=language)
        boundary_policy.authorize_before_open(f'leetcode:{pid}', gate['artifact_paths'], gate['trusted_hashes'], language='python', payload_kind='statement')
    contracts = check_authority(values['authority_review'], lane=REQUEST_NEXT4_LANE,
        freeze_sha256=sha(raws['freeze']), review_sha256=sha(raws['review']), ids=request.IDS)
    if any(contracts[f'leetcode:{pid}']['statement_sha256'] != oracle.STATEMENT_SHA256[pid] for pid in request.IDS):
        raise ValueError('next-four statement authority differs')
    original_cases = check_next4_original_evidence(plan, values, raws, code)
    root = mapped(native_freeze + '/contract.json').parent
    pre, _ = pinned({'path': str(root / 'pre-source-freeze.json'), 'sha256': freeze['pre_source_freeze_sha256']})
    provenance, _ = pinned({'path': str(root / 'case-provenance.json'), 'sha256': freeze['case_provenance_sha256']})
    expected_pre = request.pre_source_record(pre.get('generated_cases'))
    expected_pre.update(observer_code=code, additional_code=additional)
    if pre != expected_pre:
        raise ValueError('native command-local pre-source freeze differs')
    manifest, _ = pinned({'path': str(root / 'original-manifest.json'), 'sha256': request.MANIFEST_SHA256})
    originals = [row for row in manifest if row.get('problem_id') in request.IDS]
    if len(originals) != 4 or {row['problem_id'] for row in originals} != set(request.IDS):
        raise ValueError('original authoring manifest population differs')
    originals = {row['problem_id']: row for row in originals}
    cases_by_id, designs, origins = {}, {}, {}
    for pid in request.IDS:
        for language, suffix in (('javascript', 'js'), ('python', 'py')):
            if originals[pid]['source_files'][language] != {'path': f'{language}/{pid}.{suffix}', 'sha256': request.SOURCE_SHA256[pid][language]}:
                raise ValueError('original source authoring binding differs')
        definition, _ = pinned({'path': str(root / f'statements/{pid}.provenance.json'), 'sha256': request.PROVENANCE_SHA256[pid]})
        if (definition.get('problem_id') != pid or definition.get('new_statement_prefix_sha256') != oracle.STATEMENT_SHA256[pid] or
                definition.get('original_manifest_sha256') != request.MANIFEST_SHA256 or
                definition.get('original_statement_equivalence_established') is not False):
            raise ValueError('new definition provenance differs')
        boundary_policy.authorize_before_open(f'leetcode:{pid}', gate['artifact_paths'], gate['trusted_hashes'], language='python', payload_kind='statement')
        statement = bounded_regular_read(root / f'statements/{pid}.md', maximum_bytes=131072)
        cases, design, origin = request.generated(pid, statement)
        raw = bounded_regular_read(root / f'tests/{pid}.json')
        old_cases = bounded_regular_read(mapped(native + f'/inputs/generated-before-source/{pid}.cases.json'))
        old_categories = bounded_regular_read(mapped(native + f'/inputs/generated-before-source/{pid}.categories.json'))
        original = original_cases[pid]
        if (raw != q.encoded(cases) or old_cases != raw or sha(old_cases) != original['cases']['sha256'] or
                old_categories != q.encoded(origin['categories']) or sha(old_categories) != original['categories']['sha256'] or
                original['case_count'] != len(cases) or original['statement']['sha256'] != oracle.STATEMENT_SHA256[pid] or
                original['provenance']['sha256'] != request.PROVENANCE_SHA256[pid] or
                any(job['tests_canonical_sha256'] != q.canonical_tests_hash(cases) for job in jobs if job['id'] == pid)):
            raise ValueError('before-first-read and native generated cases differ')
        cases_by_id[pid], designs[str(pid)], origins[str(pid)] = cases, design, origin
    if designs != pre['generated_cases'] or provenance != origins:
        raise ValueError('native case design provenance differs')
    for job in jobs:
        boundary_policy.authorize_before_open(f"leetcode:{job['id']}", gate['artifact_paths'], gate['trusted_hashes'], language=job['language'])
        if sha(bounded_regular_read(root / job['source'], maximum_bytes=1_048_576)) != job['source_sha256']:
            raise ValueError('exact next-four passed source bytes differ')
    outcomes = _request_observations(report, jobs, cases_by_id, Path(plan['report']['path']).parent)
    replayed = {'schema': 'gamma.imported-independent-verification.v1', 'verified': True,
        'report_sha256': sha(raws['report']), 'freeze_sha256': sha(raws['freeze']),
        'verifier_sha256': q.file_hash(verifier.__file__), 'outcomes': outcomes,
        'passed': sum(row['passed'] for row in outcomes), 'total': len(outcomes),
        'cases': sum(row['cases'] for row in outcomes), 'new_qualifications': 0,
        'scope': freeze['scope'], 'automatic_promotion': False}
    if replayed != verification or not all(row['passed'] for row in outcomes):
        raise ValueError('actual next-four independent verification differs or failed')
    return contracts, originals, root


def adopt_request_next4_plan(plan, trusted_plan_sha256):
    """Prospective candidate successor; preserve the original execution base."""
    from . import request_next4_qualification as request
    from . import request_next4_oracles as oracle
    fields(plan, ('schema', 'universe', 'catalogue', 'receipts', 'execution_catalogue', 'execution_receipts',
        'predecessor_review', 'boundary_gate', 'freeze', 'report', 'verification', 'review', 'authority_review',
        'qualification_service', 'qualification_boundary_gate', 'native_bundle_root', 'artifact_root',
        *NEXT4_ORIGINAL_EVIDENCE))
    if plan['schema'] != 'gamma.request-next4-adoption-plan.v1':
        raise ValueError('unsupported fixed next-four adoption plan')
    values, raws = {}, {}
    for key in set(plan) - {'schema', 'native_bundle_root', 'artifact_root'}:
        values[key], raws[key] = pinned(plan[key])
    delta = check_next4_execution_delta(values, raws)
    contracts, originals, root = replay_request_next4(plan, values, raws)
    universe, catalogue, receipts = (values[key] for key in ('universe', 'catalogue', 'receipts'))
    freeze = values['freeze']; code = freeze['code']
    rows = {row['problem_id']: row for row in catalogue['problems']}
    replacements, additions, locators, descriptors = {}, {}, {}, {}
    prefix = plan['native_bundle_root'] + '/code/projects/algorithm_solver/'
    generator_sha = code[prefix + 'catalogue/request_next4_oracles.py']
    for job in freeze['jobs']:
        pid, language = job['id'], job['language']; gid = f'leetcode:{pid}'
        old = rows[gid]['implementations'][language]
        contract = {'schema': 'gamma.reviewed-public-batch-contract.v1', 'reviewed_statement_contract': contracts[gid],
            'authority_review_sha256': sha(raws['authority_review']), 'qualification_freeze_sha256': sha(raws['freeze']),
            'original_statement_byte_equivalence': False,
            'input_validator': {'lane': REQUEST_NEXT4_LANE, 'module_sha256': generator_sha,
                'numeric_problem_id': pid, 'entrypoint': 'validate', 'required_before_candidate_execution': True}}
        interface = {'schema': 'gamma.call-interface.v1', 'entrypoint': 'solve', 'arguments': 'ordered-positional', 'typed_contract': digest(contract)}
        runtime = {'language': language, 'runtime': freeze['runtime'], 'limits': freeze['limits'],
            'sandbox_sha256': code[prefix + 'algsolve/judge/sandbox.py'],
            'runner_sha256': code[prefix + 'catalogue/imported_qualification.py'],
            'source_interface': job['source_interface'], 'native_runtime_only': True}
        harness = ('imported-commonjs-observer-v1/harness.cjs' if language == 'javascript' else
                   'public-domain-qualification-medium32-wave2-observer-v1/harness.py')
        effects = {'local_effects': contracts[gid]['local_effects'], 'observed_effect_policy': freeze['effects'],
            'observed_result_policy': freeze['comparison'], 'oracle_sha256': generator_sha,
            'harness_sha256': code[prefix + 'catalogue/' + harness],
            'observer_helper_sha256': code[prefix + 'catalogue/public-domain-qualification-medium32-wave2-observer-v1/harness.cjs'] if language == 'javascript' else None,
            'verifier_sha256': values['verification']['verifier_sha256'], 'review_sha256': sha(raws['review'])}
        provenance = {'public_batch': {'lane': REQUEST_NEXT4_LANE, 'problem_contract': contract,
            'source_provenance': {'original_manifest_sha256': request.MANIFEST_SHA256,
                'original_manifest_path': 'projects/algorithm_solver/catalogue/authored/request-252-v1/batch1/manifest.json',
                'original_source': originals[pid]['source_files'][language], 'frozen_job': job,
                'new_definition_provenance_sha256': request.PROVENANCE_SHA256[pid]},
            'report_sha256': sha(raws['report']), 'verification_sha256': sha(raws['verification']),
            'review_sha256': sha(raws['review']), 'case_count': oracle.CASE_COUNT[pid]},
            'execution_to_adoption_base_delta': delta,
            'original_evidence_sha256': {key: sha(raws[key]) for key in NEXT4_ORIGINAL_EVIDENCE},
            'previous_canonical': {'implementation_sha256': digest(old), 'receipt_sha256': old.get('receipt_sha256'),
                'base_catalogue_sha256': sha(raws['catalogue']), 'implementation': copy.deepcopy(old)},
            'source_publication_authorized': False, 'historical_receipts_unchanged': True}
        scope = f'Reviewed problem {pid} domain; exact source-specific solve interface, numeric and local-effect contract.'
        caveats = qualification_caveats(REQUEST_NEXT4_LANE, pid) + [
            'Finite public-definition checks; original pre-source cases are retained, not fresh heldout confirmation.',
            'New statement snapshots are not claimed byte-identical to historical definitions.',
            'Native execution authority was original 943; candidate 944 is separately proved to differ only by the preserved 3215 pair.',
            'Candidate catalogue only; no serving subset, runtime, browser, recognition or publication activation.']
        impl = {'status': 'qualified', 'canonical_variant_id': language + ':' + job['source_sha256'],
            'source_sha256': job['source_sha256'], 'problem_contract_sha256': digest(contract),
            'interface': interface, 'interface_sha256': digest(interface), 'runtime_sha256': digest(runtime),
            'tests_sha256': oracle.CASES_SHA256[pid], 'effects_sha256': digest(effects),
            'evidence_class': 'normative-typed-effects', 'contract_scope': scope, 'caveats': caveats, 'provenance': provenance}
        receipt = {key: impl[key] for key in (*BINDINGS, 'canonical_variant_id', 'evidence_class', 'contract_scope', 'caveats')}
        receipt.update(problem_id=gid, language=language, verdict='qualified', independent_verifier=True,
            provenance_sha256=digest(provenance), original_independent_verification_sha256=sha(raws['verification']),
            review_sha256=sha(raws['review']), per_problem_case_count=oracle.CASE_COUNT[pid],
            verification_mode='fixed next-four imported-observation replay plus externally anchored independent authority review')
        rid = digest(receipt); impl['receipt_sha256'] = rid
        replacements[(gid, language)] = impl; additions[rid] = receipt
        locators.setdefault(gid, {})[language] = str(root / job['source'])
        descriptors[f'{language}:{pid}'] = {'problem_contract': contract, 'runtime': runtime, 'effects': effects}
    updated, retained, summary = replace_canonicals(universe, catalogue, receipts, replacements, additions)
    return {'catalogue': updated, 'verified_receipts': retained, 'summary': summary,
        'source_locators': {'schema': 'gamma.dual.source-locators.v1', 'problems': locators},
        'binding_descriptors': descriptors, 'audit': {'schema': 'gamma.public-batch-adoption.v1',
            'plan_sha256': trusted_plan_sha256, 'adopted_source_language_pairs': len(replacements),
            'previous_receipts_preserved': len(receipts), 'new_receipts': len(additions),
            'source_publication_authorized': False, 'candidate_executions': 0, 'candidate_only': True,
            'active_config_modified': False, 'execution_to_adoption_base_delta': delta,
            'original_evidence_sha256': {key: sha(raws[key]) for key in NEXT4_ORIGINAL_EVIDENCE},
            'historical_m1_qualified': False}}


def adopt_plan(plan_path, trusted_plan_sha256):
    """Build successor artifacts in memory; caller separately persists/publishes."""
    plan, _ = pinned({'path': str(plan_path), 'sha256': trusted_plan_sha256})
    if isinstance(plan, dict) and plan.get('schema') == 'gamma.request-next4-adoption-plan.v1':
        return adopt_request_next4_plan(plan, trusted_plan_sha256)
    if isinstance(plan, dict) and plan.get('schema') == 'gamma.request3215-adoption-plan.v1':
        return adopt_request3215_plan(plan, trusted_plan_sha256)
    fields(plan, ('schema', 'lane', 'universe', 'catalogue', 'receipts', 'boundary_gate',
                  'freeze', 'report', 'run_contract', 'verification', 'review', 'authority_review'))
    if plan['schema'] != 'gamma.public-batch-adoption-plan.v1':
        raise ValueError('unsupported operator plan')
    directory = lane_path(plan['lane'])
    values, raws = {}, {}
    for key in ('universe', 'catalogue', 'receipts', 'boundary_gate', 'freeze', 'report',
                'run_contract', 'verification', 'review'):
        values[key], raws[key] = pinned(plan[key])
    universe, catalogue, receipts = (values[k] for k in ('universe', 'catalogue', 'receipts'))
    validate(universe, catalogue, receipts)
    gate, freeze = values['boundary_gate'], values['freeze']
    fields(gate, ('schema', 'artifact_paths', 'trusted_hashes'))
    if gate['schema'] != 'gamma.boundary-gate-config.v1' or sha(raws['universe']) != gate['trusted_hashes']['universe']:
        raise ValueError('independent boundary universe binding mismatch')
    ids, languages = freeze.get('ids'), freeze.get('languages')
    if (not isinstance(ids, list) or not ids or any(type(x) is not int or x <= 0 for x in ids) or
            len(set(ids)) != len(ids) or languages != list(LANGUAGES)):
        raise ValueError('invalid frozen source-language population')
    for pid in ids:
        for language in languages:
            boundary_policy.authorize_before_open(f'leetcode:{pid}', gate['artifact_paths'], gate['trusted_hashes'], language=language)
    if (freeze.get('boundary_config_sha256') != sha(raws['boundary_gate']) or
            Path(freeze.get('boundary_config_path', '')).resolve() != Path(plan['boundary_gate']['path']).resolve()):
        raise ValueError('freeze boundary identity mismatch')
    run, verification, review = (values[k] for k in ('run_contract', 'verification', 'review'))
    freeze_dir, report_dir = Path(plan['freeze']['path']).parent, Path(plan['report']['path']).parent
    if (Path(plan['freeze']['path']).name != 'contract.json' or Path(plan['report']['path']).name != 'report.json' or
            Path(plan['run_contract']['path']) != report_dir / 'contract.json' or
            Path(plan['review']['path']) != report_dir / 'review.json' or Path(run.get('freeze', '')) != freeze_dir or
            run.get('freeze_sha256') != sha(raws['freeze']) or run.get('review_sha256') != sha(raws['review'])):
        raise ValueError('pinned replay path/binding mismatch')
    for pid in ids:
        boundary_policy.authorize_before_open(f'leetcode:{pid}', gate['artifact_paths'], gate['trusted_hashes'],
            language='python', payload_kind='statement')
    values['authority_review'], raws['authority_review'] = pinned(plan['authority_review'])
    check_observation_policy(plan['lane'], freeze)
    contracts = check_authority(values['authority_review'], lane=plan['lane'], freeze_sha256=sha(raws['freeze']),
        review_sha256=sha(raws['review']), ids=ids)
    if review.get('independent_review') is not True or 'boundary_policy' not in review.get('reviewed', []):
        raise ValueError('independent pre-open verifier review required')
    expected_keys = {f'{language}:{pid}' for language in languages for pid in ids}
    if set(freeze['sources']) != expected_keys:
        raise ValueError('extra or missing frozen source')
    source_paths = []
    for key, source in freeze['sources'].items():
        language, pid_text = key.split(':'); pid = int(pid_text)
        expected_name = f"{pid}.{'js' if language == 'javascript' else 'py'}"
        if source['id'] != pid or source['language'] != language or source['path'] != expected_name:
            raise ValueError('frozen source identity/path mismatch before replay')
        boundary_policy.authorize_before_open(f'leetcode:{pid}', gate['artifact_paths'], gate['trusted_hashes'], language=language)
        source_path = freeze_dir / expected_name
        data = bounded_regular_read(source_path, maximum_bytes=1_048_576)
        if sha(data) != source['sha256'] or len(data) != source['bytes']:
            raise ValueError('frozen source differs before independent replay')
        source_paths.append(source_path)
    cases_raw = bounded_regular_read(freeze_dir / 'public-cases.json')
    if sha(cases_raw) != freeze['cases_sha256']:
        raise ValueError('frozen synthetic tests changed before replay')
    cases = json.loads(cases_raw)
    # Verifier's actual reopens use anchored no-follow reads too; a pathname
    # replacement after this precheck cannot bypass the regular-file guard.
    replayed = replay(plan['lane'], freeze, Path(plan['report']['path']), source_paths=source_paths)
    if replayed != verification or verification.get('verified') is not True or verification.get('report_sha256') != sha(raws['report']):
        raise ValueError('actual independent observation replay differs')
    outcomes = verification.get('outcomes', [])
    if [(r['language'], r['id']) for r in outcomes] != [(language, pid) for language in languages for pid in ids]:
        raise ValueError('complete source-specific outcome population required')
    rows = {r['problem_id']: r for r in catalogue['problems']}
    replacements, additions, locators, descriptors = {}, {}, {}, {}
    prefix = 'catalogue/' + directory.name + '/'
    for outcome in outcomes:
        pid, language = outcome['id'], outcome['language']; gid = f'leetcode:{pid}'
        key = f'{language}:{pid}'; source = freeze['sources'][key]
        if outcome.get('passed') is not True:
            continue  # Failures retained in original report; never converted to qualified.
        expected_name = f"{pid}.{'js' if language == 'javascript' else 'py'}"
        if source['id'] != pid or source['language'] != language or source['path'] != expected_name or outcome['source_sha256'] != source['sha256']:
            raise ValueError('source-specific passed verdict binding mismatch')
        boundary_policy.authorize_before_open(gid, gate['artifact_paths'], gate['trusted_hashes'], language=language)
        source_raw = bounded_regular_read(freeze_dir / expected_name, maximum_bytes=1_048_576)
        if sha(source_raw) != source['sha256'] or len(source_raw) != source['bytes']:
            raise ValueError('exact passed source bytes changed')
        per_cases = cases[str(pid)]
        tests_sha = sha((json.dumps(per_cases, sort_keys=True, separators=(',', ':'), allow_nan=False)+'\n').encode())
        contract = {'schema': 'gamma.reviewed-public-batch-contract.v1', 'reviewed_statement_contract': contracts[gid],
            'authority_review_sha256': sha(raws['authority_review']), 'qualification_freeze_sha256': sha(raws['freeze']),
            'input_validator': {'lane': plan['lane'], 'module_sha256': freeze['code_sha256'][prefix+'oracle.py'],
                'numeric_problem_id': pid, 'entrypoint': 'validate', 'required_before_candidate_execution': True}}
        interface = {'schema': 'gamma.call-interface.v1', 'entrypoint': 'solve', 'arguments': 'ordered-positional', 'typed_contract': digest(contract)}
        runtime = {'language': language, 'runtime': freeze['node_runtime'] if language == 'javascript' else {'python_executable_sha256': freeze['python_runtime_sha256']},
            'limits': freeze['limits'], 'sandbox_sha256': freeze['code_sha256']['algsolve/judge/sandbox.py'],
            'runner_sha256': freeze['code_sha256'][prefix+'qualify.py']}
        effects = {'local_effects': contracts[gid]['local_effects'], 'observed_effect_policy': freeze['effect_policy'],
            'observed_result_policy': freeze['result_policy'], 'oracle_sha256': freeze['code_sha256'][prefix+'oracle.py'],
            'harness_sha256': freeze['code_sha256'][prefix+('harness.cjs' if language == 'javascript' else 'harness.py')],
            'verifier_sha256': freeze['code_sha256'][prefix+'verify.py'], 'review_sha256': sha(raws['review'])}
        old = rows[gid]['implementations'][language]
        provenance = {'public_batch': {'lane': plan['lane'], 'problem_contract': contract,
            'source_provenance': source, 'report_sha256': sha(raws['report']), 'verification_sha256': sha(raws['verification']),
            'review_sha256': sha(raws['review']), 'case_count': len(per_cases)},
            'previous_canonical': {'implementation_sha256': digest(old), 'receipt_sha256': old.get('receipt_sha256'),
                'base_catalogue_sha256': sha(raws['catalogue'])}, 'source_publication_authorized': False,
            'historical_receipts_unchanged': True}
        scope = f'Reviewed statement domain for problem {pid}; exact ordered solve interface and explicitly reviewed local effects only.'
        caveats = qualification_caveats(plan['lane'], pid)
        impl = {'status': 'qualified', 'canonical_variant_id': language+':'+source['sha256'], 'source_sha256': source['sha256'],
            'problem_contract_sha256': digest(contract), 'interface': interface, 'interface_sha256': digest(interface),
            'runtime_sha256': digest(runtime), 'tests_sha256': tests_sha, 'effects_sha256': digest(effects),
            'evidence_class': 'normative-typed-effects', 'contract_scope': scope, 'caveats': caveats, 'provenance': provenance}
        receipt = {k: impl[k] for k in (*BINDINGS, 'canonical_variant_id', 'evidence_class', 'contract_scope', 'caveats')}
        receipt.update(problem_id=gid, language=language, verdict='qualified', independent_verifier=True,
            provenance_sha256=digest(provenance), original_independent_verification_sha256=sha(raws['verification']),
            review_sha256=sha(raws['review']), per_problem_case_count=len(per_cases),
            verification_mode='actual fixed-lane verifier replay plus externally anchored independent authority review')
        rid = digest(receipt); impl['receipt_sha256'] = rid
        replacements[(gid, language)] = impl; additions[rid] = receipt
        locators.setdefault(gid, {})[language] = str(freeze_dir / expected_name)
        descriptors[key] = {'problem_contract': contract, 'runtime': runtime, 'effects': effects}
    updated, all_receipts, summary = replace_canonicals(universe, catalogue, receipts, replacements, additions)
    return {'catalogue': updated, 'verified_receipts': all_receipts, 'summary': summary,
        'source_locators': {'schema': 'gamma.dual.source-locators.v1', 'problems': locators}, 'binding_descriptors': descriptors,
        'audit': {'schema': 'gamma.public-batch-adoption.v1', 'plan_sha256': trusted_plan_sha256,
            'adopted_source_language_pairs': len(replacements), 'previous_receipts_preserved': len(receipts),
            'new_receipts': len(additions), 'source_publication_authorized': False, 'candidate_executions': 0,
            'historical_m1_qualified': False}}


def validate_batch_inputs(implementation, args):
    """Frozen strict domain predicate; no candidate or arbitrary import path."""
    if implementation.get('status') != 'qualified' or implementation.get('evidence_class') != 'normative-typed-effects':
        raise ValueError('not a reviewed public batch implementation')
    contract = implementation.get('provenance', {}).get('public_batch', {}).get('problem_contract')
    if not isinstance(contract, dict) or digest(contract) != implementation.get('problem_contract_sha256'):
        raise ValueError('reviewed problem contract changed')
    predicate = contract.get('input_validator', {})
    fields(predicate, ('lane', 'module_sha256', 'numeric_problem_id', 'entrypoint', 'required_before_candidate_execution'))
    fixed_request = predicate['lane'] in (REQUEST3215_LANE, REQUEST_NEXT4_LANE)
    directory = HERE if fixed_request else lane_path(predicate['lane'])
    module_name = ('request_qualification.py' if predicate['lane'] == REQUEST3215_LANE else
                   'request_next4_oracles.py' if predicate['lane'] == REQUEST_NEXT4_LANE else 'oracle.py')
    module_path = directory / module_name
    pid = predicate['numeric_problem_id']
    declared = contract.get('reviewed_statement_contract', {})
    if (type(pid) is not int or declared.get('numeric_problem_id') != pid or declared.get('problem_id') != f'leetcode:{pid}' or
            predicate['entrypoint'] != 'validate' or predicate['required_before_candidate_execution'] is not True or
            sha(bounded_regular_read(module_path)) != predicate['module_sha256']):
        raise ValueError('frozen input predicate identity mismatch')
    if predicate['lane'] == REQUEST3215_LANE:
        from . import request_qualification as module
        ids = (module.PID,)
    elif predicate['lane'] == REQUEST_NEXT4_LANE:
        from . import request_next4_oracles as module
        ids = module.IDS
    else:
        module = _module('_public_batch_input_validator', module_path)
        ids = module.IDS
    if pid not in ids:
        raise ValueError('predicate ID not admitted by fixed lane')
    module.validate(pid, args)
    return {'accepted': True, 'problem_contract_sha256': digest(contract), 'candidate_executed': False}
