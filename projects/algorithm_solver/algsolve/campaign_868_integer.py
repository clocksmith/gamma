"""Single reviewed868 qualification admission; no author code is imported or run.

This intentionally admits only the exact v2 source and saved qualification. A new
candidate, test set, codec, runtime, or reviewer requires a reviewed successor.
"""
import hashlib
import json
from pathlib import Path
from . import campaign_exact_integer as common
from . import campaign_toolchain

need = common.need
sha = common.sha
ref = common.ref
digest = common.digest
distinct = common.distinct
key = common.key
check = common.check
PROFILE = 'lc868-uint1024-number-bigint-v1'
INTERFACE = 'exact-public-spelling:lc868-uint1024-to-small-number.v1'
POLICY_SCHEMA = 'algsolve.integer868-admission-policy.v1'
DOMAIN = {'minimum': '0', 'maximum': '9' * 1024, 'maximum_decimal_digits': 1024,
          'result_minimum': 0, 'result_maximum': 3401, 'javascript_result': 'number'}
AUTHOR = '/root/normalize_539_541'
REVIEWER = '/root/w002_reconcile_next'
SOURCE = 'f7f6a40a7536779c3c8e95cff0cb342808c77f99d4773a7def71bdd2b65106a5'
ANCHORS = {
    'freeze': 'c32b8f4fc1d190a7313479e14f812d964c39b62ef92387c529710e9bda510788',
    'handoff': '0948b8af274b235d53052125dc0674240040c034ca9054b24aac257a36476d3f',
    'evidence_index': 'eb4e27943685e1bfaf1b2cb94b4b82f0f1c142f5e0249e85785915229ba47651',
    'technical_review': '8d7e0674d97f9a1108eadb3546e51a45abca15206592607bd388499e0bb79d17',
    'runtime_contract': 'db0bf29cf1b462f753fb28e7cd033fc587379a8aa72819c157ed2c0111105a76',
    'toolchain_manifest': 'd532ef4a38fae7056de2259fc753c601538685a2a61bc6dae47af635e1900b75',
    'reader_activation': 'aa26f522b07f08fd3583d55b8f70dbfd3e77c320ab099bb25ebafc0f1d791de0',
    'historical_reader': 'f8a40daeb3b1e3d2f9bd962eac64dbb948d3539dab56deafd1a86daa107b6f5d',
    'number_failure': '86757ee13b54e57e1021fa88d050fd4dc67ba00701090c2494564e8e93ec0fb6',
    'reference_incident': 'ae863650c797f324268681187567ec2f3a781ee08e2377054f49d85fccb7452f',
}
BINDINGS = tuple(ANCHORS) + ('standard', 'host_tests')
MODULES = ('campaign_868_integer.py', 'campaign_868_replay.py', 'campaign_868_dispatch.py',
           'campaign_868_transition.py', 'campaign_738_integer.py',
           'campaign_uint1024_dispatch.py', 'campaign_integer_dispatch.py',
           'campaign_633_integer.py', 'campaign_exact_integer.py',
           'campaign_toolchain.py', 'corpus_campaign.py')
RUNTIME = common.RUNTIME

def module_hashes():
    folder = Path(__file__).parent
    return {name: sha(folder / name) for name in MODULES}

def descriptor(policy_ref, allowed):
    return {'profile': PROFILE, 'entry': '0868:javascript', 'numeric_domain': DOMAIN,
            'policy_sha256': policy_ref['sha256'],
            'bindings': {name: allowed[name]['sha256'] for name in BINDINGS},
            'runtime': allowed['runtime']}

def profile(data, entry, contract):
    need(key(entry) == '0868:javascript' and entry['key'] == 'lc:binary-gap',
         'Only0868JavaScript supported')
    need(contract.get('schema') == 'algsolve.campaign-contract.v3' and
         contract.get('interface') == INTERFACE and contract.get('comparison') == 'unchanged',
         'Exact868 v3 interface and unchanged comparison required')
    need(not any(k in contract for k in ['public_comparison', 'independent_comparison']),
         'Combined comparison profiles forbidden')
    policy_ref = data.get('inputs', {}).get('integer868_policy')
    policy = check(policy_ref)
    need(policy.get('schema') == POLICY_SCHEMA and policy.get('status') == 'approved' and
         type(policy.get('entries')) is dict and set(policy['entries']) == {'0868:javascript'},
         'Explicit entry-only approved868 policy required')
    allowed = policy['entries']['0868:javascript']
    need(contract.get('source_author') == allowed.get('source_author') == AUTHOR and
         distinct(policy.get('approved_by'), AUTHOR), 'Independent coordinator approval required')
    need(allowed.get('profile') == PROFILE and digest(allowed.get('numeric_domain')) == digest(DOMAIN) and
         allowed.get('normalized_sha256') == contract.get('normalized_sha256') == SOURCE,
         'Unreviewed candidate/profile/domain')
    need(allowed.get('admission_modules') == module_hashes(), '868 admission module drift')
    need(contract.get('standard_sha256') == allowed['standard']['sha256'],
         'Frozen checker policy changed')
    bound = {}
    refs = [policy_ref]
    for name in BINDINGS:
        reference = allowed.get(name)
        need(type(reference) is dict and
             (name not in ANCHORS or reference.get('sha256') == ANCHORS[name]),
             'Wrong exact868 qualification anchor: ' + name)
        if name == 'historical_reader':
            need(sha(reference['path']) == reference['sha256'], 'Historical reader changed')
            bound[name] = Path(reference['path']).read_text()
        else:
            bound[name] = check(reference)
        refs.append(reference)
    from . import campaign_868_transition, corpus_campaign
    need(Path(corpus_campaign.__file__).read_text() ==
         campaign_868_transition.expected_reader(bound['historical_reader']),
         '868 combined reader changed beyond two exact dispatch imports')
    need(allowed.get('runtime') == {n: sha(p) for n, p in RUNTIME.items()},
         'Trusted judge runtime drift')
    refs += [ref(p) for p in RUNTIME.values()]
    frozen = bound['freeze']
    need(frozen.get('schema') == 'algsolve.integer868-preexecution-freeze.v2',
         'Exact v2 preexecution freeze required')
    folder = Path(allowed['freeze']['path']).resolve().parent
    need(len(frozen['sources']) == 57 and len(frozen['host_dependencies']) == 11,
         'Incomplete source/host closure')
    for name, wanted in frozen['sources'].items():
        path = (folder / name).resolve()
        need(path.is_relative_to(folder) and sha(path) == wanted, 'Frozen source drift')
        refs.append(ref(path))
    for reference in frozen['host_dependencies']:
        need(sha(reference['path']) == reference['sha256'], 'Host dependency drift')
        refs.append({'path': reference['path'], 'sha256': reference['sha256']})
    need(frozen['sources']['normalized/0868.js'] == SOURCE and
         frozen['sources']['policy.json'] == allowed['standard']['sha256'],
         'Source/standard not in preexecution freeze')
    for name in ('evidence_index', 'technical_review'):
        for reference in bound[name].get('artifacts' if name == 'evidence_index' else 'evidence', []):
            need(sha(reference['path']) == reference['sha256'], 'Saved qualification artifact drift')
            refs.append(reference)
    index = bound['evidence_index']
    need(index.get('schema') == 'algsolve.integer868-evidence-index.v1',
         'Wrong raw evidence index')
    reviewed = bound['technical_review']
    need(reviewed.get('schema') == 'algsolve.exact-integer-profile-independent-review.v2' and
         reviewed.get('runtime_qualification_status') == 'passed' and
         reviewed.get('runtime_profile') == PROFILE and
         reviewed.get('entry') == key(entry) and reviewed.get('author') == AUTHOR and
         reviewed.get('reviewer') == REVIEWER and distinct(REVIEWER, AUTHOR) and
         reviewed.get('freeze', {}).get('sha256') == ANCHORS['freeze'],
         'Named independent runtime review missing')
    reviewed_refs = {r['sha256'] for r in reviewed['evidence']}
    need(set(ANCHORS.values()) - {ANCHORS['technical_review'], ANCHORS['historical_reader']}
         <= reviewed_refs, 'Independent review does not bind full qualification')
    need(any(r['sha256'] == SOURCE for r in reviewed['sources']), 'Candidate not reviewed')
    packet = check(ref(folder / '0868-packet.json'))
    need(packet['id'] == 868 and packet['key'] == entry['key'] and
         packet['entry'] == {'class': 'Solution', 'method': 'binaryGap'} and
         packet['params'] == [['n', 'int']], 'Wrong frozen public interface')
    need(entry['independent_sets'] == packet['independent_test_sets'] ==
         bound['runtime_contract']['independent_sets'], 'Independent identity drift')
    need(type(contract.get('public_tests')) is int and contract['public_tests'] == 3,
         'All three public examples required')
    groups = bound['host_tests']
    need(type(groups) is list and [g.get('name') for g in groups] ==
         ['public', 'independent-lcd-868'], 'Exact two test groups required')
    need(digest(groups[0]['tests']) == digest(packet['public_tests']) and
         len(groups[0]['tests']) == 3, 'Public expectations changed')
    pin = entry['independent_sets'][0]
    need(len(entry['independent_sets']) == 1 and pin['uid'] == 'lcd:868' and
         pin['tests'] == 65 and pin['path'] == 'tests/lcd__868.json' and
         len(groups[1]['tests']) == 65 and digest(groups[1]['tests']) == pin['sha256'],
         'Unchanged full65 independent cases required')
    for case in groups[0]['tests'] + groups[1]['tests']:
        from .campaign_868_replay import encode_calls
        encode_calls([case])
        need(type(case.get('expected')) is int and 0 <= case['expected'] <= 3401 and
             case.get('compare', 'return') == 'return', 'Exact original comparison required')
    static = check(ref(folder / 'javascript-static.json'))
    need(static['errors'] == [] and hashlib.sha256(static['formatted'].encode()).hexdigest() == SOURCE,
         'Frozen standard evidence differs')
    measured = campaign_toolchain.verify(bound['toolchain_manifest'])
    refs += [{'path': r['path'], 'sha256': r['sha256']} for r in measured]
    wanted = descriptor(policy_ref, allowed)
    need(digest(contract.get('runtime_profile')) == digest(wanted), 'Runtime policy descriptor mismatch')
    bound['_folder'] = folder
    return wanted, bound, refs

def execution_profile(data, entry, contract, execution, review):
    wanted, bound, refs = profile(data, entry, contract)
    need(digest(execution.get('runtime_profile')) == digest(review.get('runtime_profile')) == digest(wanted),
         'Execution/review profile mismatch')
    need(review.get('reviewer') == REVIEWER and
         distinct(review.get('reviewer'), contract['source_author']) and
         review.get('runtime_profile_reviewed') is True and
         review.get('runtime_qualification_sha256') == ANCHORS['technical_review'],
         'Named independent admission review required')
    from .campaign_868_replay import replay
    observed = replay(bound, refs)
    for name, value in {'public_total': 3, 'public_passed': 3,
                        'independent_total': 65, 'independent_passed': 65,
                        'infrastructure_errors': 0, 'decoding_errors': 0}.items():
        need(type(execution.get(name)) is int and execution[name] == value,
             'Execution count mismatch: ' + name)
    need(observed == {'cases': 68, 'passed': 68, 'official': 52, 'extended': 16,
                      'calls': 114, 'control_calls': 77}, 'Full qualification incomplete')
    declared = {(str(Path(r['path']).resolve()), r['sha256']) for r in execution.get('artifacts', [])}
    need(all((str(Path(r['path']).resolve()), r['sha256']) in declared for r in refs),
         'Execution receipt omits preserved evidence')
    return refs
