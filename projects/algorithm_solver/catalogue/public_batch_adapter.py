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


def adopt_plan(plan_path, trusted_plan_sha256):
    """Build successor artifacts in memory; caller separately persists/publishes."""
    plan, _ = pinned({'path': str(plan_path), 'sha256': trusted_plan_sha256})
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
    directory = lane_path(predicate['lane'])
    pid = predicate['numeric_problem_id']
    declared = contract.get('reviewed_statement_contract', {})
    if (type(pid) is not int or declared.get('numeric_problem_id') != pid or declared.get('problem_id') != f'leetcode:{pid}' or
            predicate['entrypoint'] != 'validate' or predicate['required_before_candidate_execution'] is not True or
            sha((directory / 'oracle.py').read_bytes()) != predicate['module_sha256']):
        raise ValueError('frozen input predicate identity mismatch')
    module = _module('_public_batch_input_validator', directory / 'oracle.py')
    if pid not in module.IDS:
        raise ValueError('predicate ID not admitted by fixed lane')
    module.validate(pid, args)
    return {'accepted': True, 'problem_contract_sha256': digest(contract), 'candidate_executed': False}
