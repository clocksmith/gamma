"""Prospective, explicitly approved adoption of eight original400 Python gaps.

This is NOT an extension of python_receipt_adapter.SCHEMAS. Historical
compatibility reports remain qualified=0. Review produces no qualified receipt;
adoption requires a separately reviewed, externally pinned approval. Trust pins
and allowed_ids are operator inputs, NEVER fields accepted from a request.

reverify_original_report reruns the existing full-observation verifier, not a
candidate. review_gap checks that exact evidence chain and source bytes as data.
It cannot establish that an operator's trust anchors or approval are honest.
"""
from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path, PurePosixPath
import subprocess

from .catalogue import BINDINGS, digest, hash_value

GAP_IDS = (252, 1064, 1086, 1087, 1152, 1153, 1165, 2898)
LIMITS = {'cpu_seconds': 3, 'wall_seconds': 8, 'memory_bytes': 1024**3,
          'max_output_bytes': 4 * 1024**2}
COMPAT = 'extra-contract-reference-compatibility-probe'
EVIDENCE = 'frozen-admitted-typed-effects'
MAX_BYTES = 16 * 1024**2
CODE_PATHS = (
    'algsolve/judge/sandbox.py', 'algsolve/judge/judge.py',
    'algsolve/judge/functional_semantics.py', 'algsolve/judge/declared_comparison.py',
    'literals/admission500-v1/qualify_rules.py',
    'literals/paired-authoring-v1/baseline_replay.py',
    'literals/python-compat-replay-v1/qualify.py',
    'literals/python-compat-replay-v1/verify.py',
    'literals/python-compat-replay-v1/harness.py',
    'literals/python-compat-replay-v1/CONTRACT.md',
    'literals/readable-joint-blocks-v1/transfer.py',
)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def encoded(value):
    return (json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False) + '\n').encode()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def parse(raw):
    require(type(raw) is bytes and len(raw) <= MAX_BYTES, 'bounded raw bytes required')
    def pairs(items):
        result = {}
        for key, value in items:
            require(key not in result, 'duplicate JSON key')
            result[key] = value
        return result
    def invalid(_):
        raise ValueError('nonfinite JSON')
    return json.loads(raw, object_pairs_hook=pairs, parse_constant=invalid)


def pinned(raw, expected):
    require(hash_value(expected) and sha(raw) == expected, 'external raw hash anchor mismatch')
    value = parse(raw)
    require(type(value) is dict, 'metadata object required')
    return value


def ids(value):
    require(type(value) is list and value and all(type(i) is int and i > 0 for i in value),
            'nonempty numeric IDs required')
    require(value == sorted(set(value)), 'canonical unique ordered IDs required')
    return set(value)


def integer(value, minimum=0):
    return type(value) is int and value >= minimum


def _scope(value):
    require(value.get('protected_access') is False and value.get('m1_qualified') is False,
            'protected/M1 scope mismatch')


def _freeze(value, allowed):
    _scope(value)
    require(value.get('schema') == 'gamma.python.compatibility-source-freeze.v1', 'source freeze schema')
    population = ids(value.get('ids'))
    require(population <= allowed and set(value.get('sources', {})) == {str(i) for i in population},
            'source freeze outside original authorized population')
    require(value.get('partition') in ('dev_fit', 'dev_val') and
            value.get('source_frozen_before_replay') is True and
            value.get('dictionary_fitting_allowed') is False and
            value.get('normative_domain_resolved') is False and
            value.get('evidence_class') == COMPAT, 'historical freeze scope changed')
    require(set(value.get('code_sha256', {})) == set(CODE_PATHS) and
            all(hash_value(h) for h in value['code_sha256'].values()), 'incomplete frozen code identity')
    for pid in population:
        s = value['sources'][str(pid)]
        require(s.get('path') == f'{pid}.py' and s.get('method') == 'solve' and
                integer(s.get('bytes'), 1) and all(hash_value(s.get(k)) for k in
                ('sha256', 'semantics_sha256', 'reference_source_sha256')), 'source identity invalid')
    return population


def _replay(run, report, verified, run_hash, report_hash, freeze, freeze_hash, allowed):
    for value in (run, report, verified):
        _scope(value)
    require(run.get('schema') == report.get('schema') == 'gamma.python.compatibility-runtime-replay.v1'
            and verified.get('schema') == 'gamma.python.compatibility-independent-verification.v1',
            'unsupported replay/verifier schema')
    population = ids(run.get('ids'))
    require(population <= allowed and run['ids'] == freeze['ids'] and
            run.get('source_freeze_sha256') == freeze_hash and
            run.get('code_sha256') == freeze['code_sha256'], 'run/freeze chain mismatch')
    require(run.get('limits') == LIMITS and all(type(v) is int for v in run['limits'].values()) and
            type(run.get('batch_cases')) is int and run['batch_cases'] == 32 and
            integer(run.get('max_wall_seconds'), 1) and run['max_wall_seconds'] <= 3600 and
            hash_value(run.get('python_runtime_sha256')) and
            hash_value(run.get('input_manifest_sha256')), 'runtime/resource contract mismatch')
    require(report.get('status') == 'completed' and report.get('contract_sha256') == run_hash and
            verified.get('report_sha256') == report_hash and verified.get('verified') is True,
            'incomplete independently verified replay')
    require(report.get('qualified') == 0 and type(report.get('qualified')) is int and
            verified.get('qualified') == 0 and type(verified.get('qualified')) is int and
            all(v.get('evidence_class') == COMPAT and v.get('normative_domain_resolved') is False
                for v in (report, verified)), 'historical compatibility verdict rewritten')
    require(all(integer(report.get(k)) for k in ('compatible', 'checks_passed', 'candidate_executions')) and
            all(integer(verified.get(k)) for k in ('programs', 'compatible', 'checks', 'executions')),
            'aggregate counts must be integers')
    require(set(run.get('input_hashes', {})) == {str(i) for i in population}, 'input denominator mismatch')
    for hashes in run['input_hashes'].values():
        require(set(hashes) == {'source', 'cases', 'baseline'} and all(hash_value(h) for h in hashes.values()),
                'invalid input binding')
    rows = report.get('rows')
    require(type(rows) is list and [r.get('id') for r in rows] == run['ids'], 'execution denominator mismatch')
    groups = [verified.get(k) for k in ('compatible_ids', 'failed_ids', 'blocked_ids')]
    require(all(type(g) is list and all(type(i) is int for i in g) for g in groups), 'outcome partition malformed')
    flat = sum(groups, [])
    require(len(flat) == len(set(flat)) == len(population) and set(flat) == population,
            'outcome partition omits or duplicates failures')
    require(verified.get('programs') == len(population) and
            verified.get('compatible') == report.get('compatible') == len(groups[0]), 'aggregate population mismatch')
    checks = calls = 0
    for row in rows:
        pid, n = row['id'], row.get('cases')
        require(integer(n, 1) and integer(row.get('checks_passed')) and row['checks_passed'] <= n,
                'invalid case denominator')
        require(type(row.get('calls')) is list and type(row.get('failures')) is list, 'missing observations/failures')
        if pid in groups[2]:
            require(row.get('blocked') and row['calls'] == [] and row['checks_passed'] == 0 and
                    row.get('passed') is False, 'blocked observation mismatch')
        else:
            require(not row.get('blocked') and len(row['calls']) == (n + 31) // 32, 'incomplete batch coverage')
            for offset, call in zip(range(0, n, 32), row['calls']):
                require(call.get('stem') == f'{pid}-{offset}' and type(call.get('exit_code')) is int and
                        type(call.get('timed_out')) is bool and type(call.get('output_limit_exceeded')) is bool and
                        hash_value(call.get('stdout_sha256')) and hash_value(call.get('stderr_sha256')),
                        'invalid raw-observation binding')
            passed = row['checks_passed'] == n and not row['failures']
            require(row.get('passed') is passed and (pid in groups[0]) == passed, 'verifier/row disagreement')
            if passed:
                require(all(c['exit_code'] == 0 and not c['timed_out'] and not c['output_limit_exceeded']
                            for c in row['calls']), 'passing row contains failed process')
        checks += row['checks_passed']
        calls += len(row['calls'])
    require(report.get('checks_passed') == verified.get('checks') == checks and
            report.get('candidate_executions') == verified.get('executions') == calls, 'observation aggregate mismatch')
    return {r['id']: r for r in rows}, set(groups[0])


def reverify_original_report(project_root, inputs_root, report_path, *, trusted_hashes, allowed_ids):
    """Rerun the existing verifier on ALL original report rows, not a filtered report.

    All paths/pins are trusted operator configuration. The existing bounded
    transfer loader authorizes original400 membership BEFORE payload reads.
    This executes verifier code only; its verify path never calls sandbox.run.
    Returns original metadata bytes and a fresh raw verification result, whose
    exact hash must equal the previously independently trusted verifier result.
    """
    project_root, report_path = Path(project_root), Path(report_path)
    require(report_path.name == 'report.json', 'canonical report path required')
    def read(path):
        with Path(path).open('rb') as stream:
            raw = stream.read(MAX_BYTES + 1)
        require(len(raw) <= MAX_BYTES, 'file exceeds bound')
        return raw
    report_raw = read(report_path)
    run_raw = read(report_path.parent / 'contract.json')
    report = pinned(report_raw, trusted_hashes['report'])
    run = pinned(run_raw, trusted_hashes['run'])
    allowed = ids(sorted(allowed_ids))
    require(ids(run.get('ids')) <= allowed, 'deny unauthorized report BEFORE payload opening')
    freeze_raw = read(Path(run['source_freeze']) / 'contract.json')
    freeze = pinned(freeze_raw, trusted_hashes['freeze'])
    _freeze(freeze, allowed)
    require(run.get('source_freeze_sha256') == sha(freeze_raw) and run.get('code_sha256') == freeze['code_sha256']
            and run.get('ids') == freeze['ids'], 'pre-open freeze mismatch')
    for name in CODE_PATHS:
        require(str(PurePosixPath(name)) == name and sha(read(project_root / name)) == run['code_sha256'][name],
                'verifier dependency drift: ' + name)
    # Match the frozen native Python path, not whichever Python imports this adapter.
    python = Path('/usr/bin/python3')
    require(sha(python.read_bytes()) == run['python_runtime_sha256'], 'verifier runtime drift')
    result = subprocess.run([str(python), '-I', str(project_root / 'literals/python-compat-replay-v1/verify.py'),
                             '--inputs', str(inputs_root), '--report', str(report_path)],
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=180, check=False)
    require(result.returncode == 0, 'full observation verifier failed: ' + result.stderr[:2048].decode(errors='replace'))
    verified = pinned(result.stdout, trusted_hashes['verified'])
    _replay(run, report, verified, sha(run_raw), sha(report_raw), freeze, sha(freeze_raw), allowed)
    return {'report': report_raw, 'run': run_raw, 'verified': result.stdout}


def _javascript(js, pid):
    key = f'development400:{pid}'
    impl = js['implementations'][key]
    binding = js['binding_descriptors'][key]
    receipt = js['verified_receipts'][impl['receipt_sha256']]
    require(impl.get('status') == receipt.get('verdict') == 'qualified' and
            impl.get('evidence_class') == receipt.get('evidence_class') == EVIDENCE and
            receipt.get('independent_verifier') is True and receipt.get('language') == 'javascript' and
            receipt.get('problem_id') == key and digest(receipt) == impl['receipt_sha256'], 'JS admitted authority missing')
    for name in (*BINDINGS, 'canonical_variant_id', 'evidence_class', 'contract_scope', 'caveats'):
        require(receipt.get(name) == impl.get(name), 'JS receipt binding mismatch')
    require(receipt.get('provenance_sha256') == digest(impl['provenance']), 'JS provenance not bound')
    require(all(hash_value(impl.get(k)) for k in BINDINGS), 'JS receipt hash malformed')
    contract = binding['problem_contract']
    require(contract.get('schema') == 'gamma.existing-javascript-admission-binding.v1' and
            type(contract.get('numeric_development_id')) is int and contract['numeric_development_id'] == pid and
            digest(contract) == impl['problem_contract_sha256'] and
            digest(binding['runtime']) == impl['runtime_sha256'] and
            digest(binding['effects']) == impl['effects_sha256'] and
            digest(impl['interface']) == impl['interface_sha256'] and
            impl['interface'] == {'schema': 'gamma.call-interface.v1', 'entrypoint': 'solve',
                                 'arguments': 'ordered-positional', 'typed_contract': digest(contract)}, 'JS descriptor mismatch')
    require(impl['source_sha256'] == contract.get('admitted_reference_sha256') and
            impl['tests_sha256'] == contract.get('tests_sha256') and
            binding['effects'].get('historical_observation_sha256') == contract.get('behavior_effects_sha256') and
            contract.get('qualification_contract_sha256') == impl['provenance'].get('qualification_contract_sha256') and
            hash_value(contract.get('qualification_contract_sha256')) and
            integer(impl['provenance'].get('case_count'), 1), 'selected JS source is not exact admitted reference')
    return impl, binding


def review_gap(javascript_raw, freezes, replays, source_raws, semantics_raws, *, trusted_hashes, allowed_ids):
    """Build a draft for exactly eight IDs; absent/failed native evidence stays blocked.

    freezes is name->raw contract; replays is name->{report,run,verified} bytes.
    trusted_hashes keys are javascript, freeze:<name>, <name>:<artifact>.
    The verified pin must come from reverify_original_report or an independently
    repeated full-observation verifier, not a self-generated summary/flag.
    """
    expected = {'javascript'} | {'freeze:' + n for n in freezes}
    for name, replay in replays.items():
        require(set(replay) == {'report', 'run', 'verified'}, 'replay artifact set mismatch')
        expected.update(name + ':' + k for k in replay)
    require(set(trusted_hashes) == expected, 'explicit complete external artifact pins required')
    allowed = ids(sorted(allowed_ids))
    require(set(GAP_IDS) <= allowed, 'eight gaps must be original authorized IDs')
    require(set(source_raws) == set(semantics_raws) == set(GAP_IDS), 'exact eight source/sidecar bytes required')
    js = pinned(javascript_raw, trusted_hashes['javascript'])
    parsed_freezes = {}; source_index = {}
    for name, raw in freezes.items():
        freeze = pinned(raw, trusted_hashes['freeze:' + name]); _freeze(freeze, allowed)
        parsed_freezes[sha(raw)] = freeze
        for pid in set(freeze['ids']) & set(GAP_IDS):
            require(pid not in source_index, 'ambiguous frozen gap source')
            source_index[pid] = (freeze['sources'][str(pid)], sha(raw))
    require(set(source_index) == set(GAP_IDS), 'missing frozen gap source')
    evidence = {}
    for name, replay in replays.items():
        run, report, verified = (pinned(replay[k], trusted_hashes[name + ':' + k]) for k in ('run', 'report', 'verified'))
        freeze_hash = run.get('source_freeze_sha256')
        require(freeze_hash in parsed_freezes, 'replay source freeze unavailable')
        rows, passing = _replay(run, report, verified, sha(replay['run']), sha(replay['report']),
                                parsed_freezes[freeze_hash], freeze_hash, allowed)
        for pid in set(rows) & set(GAP_IDS):
            require(pid not in evidence, 'multiple replay outcomes: explicit successor selection required')
            evidence[pid] = (run, rows[pid], pid in passing, {k: sha(v) for k, v in replay.items()})
    proposals = {}; blocked = []; ready = []
    for pid in GAP_IDS:
        key = f'development400:{pid}'; source, freeze_hash = source_index[pid]
        require(sha(source_raws[pid]) == source['sha256'] and len(source_raws[pid]) == source['bytes'] and
                sha(semantics_raws[pid]) == source['semantics_sha256'], 'Python source/semantics drift')
        semantics = parse(semantics_raws[pid])
        require(semantics.get('problem_id') == pid and semantics.get('language') == 'python' and
                semantics.get('entry_point') == 'solve', 'source interface identity mismatch')
        js_impl, js_binding = _javascript(js, pid)
        contract = js_binding['problem_contract']
        require(source['reference_source_sha256'] == contract['admitted_reference_sha256'], 'different admitted reference')
        proposal = {'source_sha256': source['sha256'], 'semantics_sha256': source['semantics_sha256'],
                    'source_freeze_sha256': freeze_hash, 'javascript_receipt_sha256': js_impl['receipt_sha256'],
                    'status': 'blocked', 'reason': 'No completed independently reverified native evidence.'}
        proposals[key] = proposal
        if pid not in evidence:
            blocked.append(pid); continue
        run, row, passing, ancestry = evidence[pid]
        require(run['source_freeze_sha256'] == freeze_hash, 'execution does not bind selected source')
        expected_inputs = {'cases': contract['tests_sha256'], 'baseline': contract['behavior_effects_sha256'],
                           'source': contract['admitted_reference_sha256']}
        require(run['input_hashes'][str(pid)] == expected_inputs and
                run['input_manifest_sha256'] == contract['frozen_input_manifest_sha256'] and
                row['cases'] == js_impl['provenance']['case_count'], 'JS/Python admitted input specification differs')
        if not passing:
            proposal['reason'] = 'Native evidence failed or blocked; historical failures retained.'
            proposal['replay_ancestry'] = ancestry; blocked.append(pid); continue
        pins = run['code_sha256']; ch = digest(contract)
        interface = {'schema': 'gamma.call-interface.v1', 'entrypoint': 'solve',
                     'arguments': 'ordered-positional', 'typed_contract': ch}
        runtime = {'python_executable_sha256': run['python_runtime_sha256'],
                   'sandbox_sha256': pins['algsolve/judge/sandbox.py'], 'limits': run['limits']}
        effects = {'historical_behavior_effects_sha256': expected_inputs['baseline'],
                   'typed_transport_sha256': pins['literals/python-compat-replay-v1/harness.py'],
                   'host_judge_sha256': pins['algsolve/judge/judge.py'],
                   'functional_semantics_sha256': pins['algsolve/judge/functional_semantics.py'],
                   'declared_comparison_sha256': pins['algsolve/judge/declared_comparison.py'],
                   'admitted_comparison_rules_sha256': pins['literals/admission500-v1/qualify_rules.py'],
                   'comparison_runner_sha256': pins['literals/python-compat-replay-v1/qualify.py'],
                   'full_observation_verifier_sha256': pins['literals/python-compat-replay-v1/verify.py'],
                   'checks': ['typed-return', 'host-oracle', 'exact-result', 'args-before', 'args-after', 'alias-edges', 'no-errors']}
        require(effects['host_judge_sha256'] == js_binding['effects']['host_judge_sha256'], 'host oracle changed')
        provenance = {'scope': 'prospective-admitted-spec-adoption-review', 'numeric_development_id': pid,
                      'javascript_receipt_sha256': js_impl['receipt_sha256'], 'source_freeze_sha256': freeze_hash,
                      'source_semantics_sha256': source['semantics_sha256'], 'replay_ancestry': ancestry,
                      'case_count': row['cases'], 'all_domain_proof': False, 'normative_domain_resolved': False,
                      'recognition_qualified': False, 'current_serving_runtime_verified': False}
        caveats = ['Finite independently rechecked return/type/mutation/alias evidence, not universal-domain or complexity proof.',
                   'Original compatibility receipts retain qualified=0; no official normative-domain correctness claim.',
                   'The hash-bound Python semantics sidecar retains its declared supported domain and numeric/Unicode limits.',
                   'Recorded runtime only; current serving, recognition and publication permission are separate.']
        if pid == 1152:
            caveats.append('Declared ASCII website-string scope; Python scalar and JavaScript UTF16 lexical ordering can differ outside it.')
        if pid == 1165:
            caveats.append('All word characters must exist in the keyboard; missing-character nonfinite behavior remains unsupported.')
        impl = {'status': 'authored', 'reason': 'Explicit independent adoption review required.',
                'source_sha256': source['sha256'], 'canonical_variant_id': 'python:' + source['sha256'],
                'problem_contract_sha256': ch, 'interface': interface, 'interface_sha256': digest(interface),
                'runtime_sha256': digest(runtime), 'tests_sha256': expected_inputs['cases'], 'effects_sha256': digest(effects),
                'provenance': provenance, 'evidence_class': EVIDENCE,
                'contract_scope': 'Exact existing admitted frozen specification shared with the pinned JavaScript reference; Python typed/effect bridge independently checked.',
                'caveats': caveats}
        proposal.update(status='review-ready', reason='Full native observations independently reverified; adoption not granted.',
                        implementation=impl, binding_descriptors={'problem_contract': contract, 'runtime': runtime, 'effects': effects})
        ready.append(pid)
    return {'schema': 'gamma.python-admitted-gap-review.v1', 'ids': list(GAP_IDS), 'ready_ids': ready,
            'blocked_ids': blocked, 'proposals': proposals, 'artifact_sha256': dict(trusted_hashes),
            'qualified': 0, 'adoption_authorized': False, 'normative_domain_resolved': False,
            'protected_access': False, 'new_candidate_executions': 0, 'current_serving_runtime_verified': False}


def adopt_review(review_raw, approval_raw, *, trusted_review_sha256, trusted_approval_sha256):
    """Create new receipts ONLY after separate, externally authenticated approval.

    The caller must obtain approval from the owner/root reviewer out of band.
    Computing a hash of one's own approval object is NOT such authority. This
    function changes no catalogue or service and grants no publication rights.
    """
    review = pinned(review_raw, trusted_review_sha256)
    approval = pinned(approval_raw, trusted_approval_sha256)
    required = {'schema', 'decision', 'scope', 'review_sha256', 'approved_ids', 'approver',
                'normative_domain_resolved', 'protected_access', 'publication_authorized'}
    require(set(approval) == required and approval['schema'] == 'gamma.python-admitted-gap-approval.v1' and
            approval['decision'] == 'approve' and approval['scope'] == 'exact-reviewed-frozen-admitted-typed-effects' and
            approval['review_sha256'] == trusted_review_sha256 and approval['approver'] in ('owner', 'root-delegate') and
            all(approval[k] is False for k in ('normative_domain_resolved', 'protected_access', 'publication_authorized')),
            'explicit scoped independent approval required')
    require(review.get('schema') == 'gamma.python-admitted-gap-review.v1' and review.get('ids') == list(GAP_IDS) and
            type(review.get('qualified')) is int and review['qualified'] == 0 and review.get('adoption_authorized') is False and
            review.get('protected_access') is False and review.get('normative_domain_resolved') is False,
            'not a preserved draft review')
    approved = ids(approval['approved_ids'])
    require(approved <= set(review['ready_ids']) <= set(GAP_IDS) and
            set(review['ready_ids']).isdisjoint(review['blocked_ids']) and
            set(review['ready_ids']) | set(review['blocked_ids']) == set(GAP_IDS), 'cannot adopt absent/failed native evidence')
    implementations = {}; receipts = {}; bindings = {}
    for pid in sorted(approved):
        key = f'development400:{pid}'; proposal = review['proposals'][key]
        require(proposal.get('status') == 'review-ready', 'proposal not ready')
        impl = copy.deepcopy(proposal['implementation']); impl.pop('reason')
        require(impl['status'] == 'authored', 'draft was already promoted')
        impl['status'] = 'qualified'
        impl['provenance'].update(scope='explicit-prospective-admitted-spec-adoption',
                                  adoption_review_sha256=trusted_review_sha256, adoption_approval_sha256=trusted_approval_sha256)
        receipt = {k: impl[k] for k in (*BINDINGS, 'canonical_variant_id', 'evidence_class', 'contract_scope', 'caveats')}
        receipt.update(problem_id=key, language='python', verdict='qualified', independent_verifier=True,
                       provenance_sha256=digest(impl['provenance']),
                       adoption_review_sha256=trusted_review_sha256, adoption_approval_sha256=trusted_approval_sha256,
                       verification_mode='existing full-observation verifier rerun plus explicit prospective admitted-spec review')
        rid = digest(receipt); impl['receipt_sha256'] = rid
        implementations[key] = impl; receipts[rid] = receipt; bindings[key] = proposal['binding_descriptors']
    return {'schema': 'gamma.python-admitted-gap-adoption.v1', 'implementations': implementations,
            'verified_receipts': receipts, 'binding_descriptors': bindings, 'eligible_ids': sorted(approved),
            'unadopted_ids': sorted(set(GAP_IDS) - approved), 'new_candidate_executions': 0,
            'normative_domain_resolved': False, 'protected_access': False, 'publication_authorized': False,
            'current_serving_runtime_verified': False, 'recognition_qualified': False}
