"""Independently verify a closed relational comparison and prepare driver records.

Usage: python -m gamma_enwiki9.adapters.fx2_relational_terminal ROOT CANDIDATE JOB
Run from the repository root. The terminal and driver index are published once;
the lab reflection must bind the index before record_driver_result can append it.
This interpreter is bound in its own terminal record, separately from execution.
"""
from pathlib import Path
import json, math, sys
from gamma_enwiki9.evidence.artifacts import canonical_bytes, fingerprint, publish_immutable_artifact

def verify_and_publish(root, n, job_id):
    r = Path(root).resolve()
    o = r / 'results' / n
    ref = lambda p: fingerprint(p, r)
    sha = lambda p: ref(p)['sha256']
    
    def write(p, v):
        publish_immutable_artifact(p, canonical_bytes(v) + b'\n')
    j = json.loads((o / 'comparison.json').read_bytes())
    manifest = json.loads((o / 'artifacts.json').read_bytes())
    for a in manifest['artifacts']:
        p = r / a['path']
        if not (p.stat().st_size == a['bytes'] and sha(p) == a['sha256']):
            raise ValueError("terminal verification failed: p.stat().st_size == a['bytes'] and sha(p) == a['sha256']")
    retained = {a['path']: a for a in manifest['artifacts']}
    if len(retained) != len(manifest['artifacts']):
        raise ValueError('duplicate artifact paths')

    def retained_ref(path):
        actual = ref(path)
        if retained.get(actual['path']) != actual:
            raise ValueError('required artifact absent from manifest: ' + actual['path'])
        return actual

    # Every evidence file read below must belong to the closed retained set.
    sha = lambda p: retained_ref(p)['sha256']
    retained_ref(o / 'comparison.json')
    if set(j['measurements']) != {'development', 'validation', 'confirmation'}:
        raise ValueError('incomplete population set')
    if any(set(arms) != set('PKISW') for arms in j['measurements'].values()):
        raise ValueError('incomplete arm set')
    jobs = list((r / 'operations/adaptive/completed').glob('*' + job_id + '.json'))
    if len(jobs) != 1:
        raise ValueError('expected one completed job')
    job_path = jobs[0]
    job = json.loads(job_path.read_bytes())
    if (job['job_id'] != job_id or job['candidate_id'] != n or
            job['state'] != 'completed' or j['candidate_id'] != n):
        raise ValueError('candidate or job identity mismatch')
    experiment_path = r / job['experiment']['path']
    if ref(experiment_path)['sha256'] != job['experiment']['sha256'].removeprefix('sha256:'):
        raise ValueError('bound experiment changed')
    experiment = json.loads(experiment_path.read_bytes())
    inputs = {v['path']: v['sha256'].removeprefix('sha256:') for v in experiment['inputs']}
    plan_path = r / 'operations/provenance' / (n + '_plan.json')
    if ref(plan_path)['sha256'] != inputs[plan_path.relative_to(r).as_posix()]:
        raise ValueError('bound plan changed')
    plan = json.loads(plan_path.read_bytes())
    package = j['package']
    parent = o / 'snapshot' / plan['parent_binary']
    if sha(parent) != inputs[plan['parent_binary']]:
        raise ValueError('original parent identity mismatch')
    binary = retained_ref(o / 'native/cmix')
    source = retained_ref(o / 'S-source.zip')
    if package['binary'] != binary or package['source'] != source:
        raise ValueError('package artifact identity mismatch')
    binary_delta = binary['bytes'] - parent.stat().st_size
    source_delta = source['bytes'] - retained_ref(o / 'P-source.zip')['bytes']
    expected_increment = min(2 * binary_delta, source_delta + binary_delta) + len('GAMMA_RELATIONAL_ARM=S')
    if package['counted_increment'] != expected_increment:
        raise ValueError('counted code increment does not match actual alternatives')
    guard_path = r / job['execution_resources']['guard_path']
    g = json.loads(guard_path.read_bytes())
    if not (job['returncode'] == 0 and job['execution_resources']['cleanup_complete'] and (g['status'] == 'complete') and (not any(g['guards'].values()))):
        raise ValueError("terminal verification failed: job['returncode'] == 0 and job['execution_resources']['cleanup_complete'] and (g['status'] == 'complete') and (not any(g['guards'].values()))")
    phases = {x['phase']: x for x in j['commands']}
    expected_phases = {'build', 'clean', 'build-repeat'}
    for pop in j['measurements']:
        expected_phases.add(pop + '-original')
        expected_phases.update(f'{pop}-{arm}-{action}' for arm in 'PKISW'
                               for action in ('encode', 'decode', 'repeat'))
    if len(j['commands']) != len(expected_phases) or set(phases) != expected_phases:
        raise ValueError('missing or duplicate command phase')
    for name, command in phases.items():
        path = o / (name + '.command.json')
        retained_ref(path)
        if json.loads(path.read_bytes()) != command:
            raise ValueError('command differs from retained phase record')
        if (command['returncode'] != 0 or command['timeout'] is not False or
                command['cleanup_complete'] is not True or command['error'] is not None or
                not math.isfinite(command['elapsed_seconds']) or command['elapsed_seconds'] < 0):
            raise ValueError('unsuccessful command phase: ' + name)
    deltas = {}
    positive = []
    for pop, arms in j['measurements'].items():
        for arm, cell in arms.items():
            for key in ('archive', 'inverse', 'repeat'):
                if cell[key] != retained_ref(r / cell[key]['path']):
                    raise ValueError('measurement artifact identity mismatch')
            summary_path = o / 'native' / f'{pop}-{arm}-encode.json'
            retained_ref(summary_path)
            if cell['diagnostics'] != json.loads(summary_path.read_bytes()):
                raise ValueError('diagnostics differ from retained native summary')
            if arm in 'KS' and sha(o / 'native' / f'{pop}-{arm}-encode.state') != sha(o / 'native' / f'{pop}-P-encode.state'):
                raise ValueError('bookkeeping/shared state differs from parent bookkeeping')
            expected_raw = inputs[plan['populations'][pop]['raw']]
            if sha(r / cell['inverse']['path']) != expected_raw:
                raise ValueError('independent inverse does not match bound raw input')
            if cell['archive_bytes'] != (r / cell['archive']['path']).stat().st_size:
                raise ValueError('reported archive byte count differs')
            for action in ('encode', 'decode', 'repeat'):
                if sha(o / 'native' / f'{pop}-{arm}-{action}.raw') != expected_raw:
                    raise ValueError('completed WRT emissions differ from bound raw input')
            if not all((cell[key] for key in ('exact_inverse', 'repeat_exact', 'parent_predictions_exact', 'introduced_state_exact'))):
                raise ValueError("terminal verification failed: all((cell[key] for key in ('exact_inverse', 'repeat_exact', 'parent_predictions_exact', 'introduced_state_exact')))")
            if not sha(r / cell['archive']['path']) == sha(r / cell['repeat']['path']):
                raise ValueError("terminal verification failed: sha(r / cell['archive']['path']) == sha(r / cell['repeat']['path'])")
            if arm in 'PK':
                if not sha(r / cell['archive']['path']) == sha(o / 'native' / f'{pop}-original.arc'):
                    raise ValueError("terminal verification failed: sha(r / cell['archive']['path']) == sha(o / 'native' / f'{pop}-original.arc')")
            for action in ('decode', 'repeat'):
                for suffix in ('state', 'parent', 'json'):
                    if not sha(o / 'native' / f'{pop}-{arm}-encode.{suffix}') == sha(o / 'native' / f'{pop}-{arm}-{action}.{suffix}'):
                        raise ValueError("terminal verification failed: sha(o / 'native' / f'{pop}-{arm}-encode.{suffix}') == sha(o / 'native' / f'{pop}-{arm}-{action}.{suffix}')")
            if not sha(o / 'native' / f'{pop}-{arm}-encode.parent') == sha(o / 'native' / f'{pop}-P-encode.parent'):
                raise ValueError("terminal verification failed: sha(o / 'native' / f'{pop}-{arm}-encode.parent') == sha(o / 'native' / f'{pop}-P-encode.parent')")
        d = {'shared_payload_gain': arms['P']['archive_bytes'] - arms['S']['archive_bytes'], 'shared_over_independent': arms['I']['archive_bytes'] - arms['S']['archive_bytes'], 'shared_over_wrong': arms['W']['archive_bytes'] - arms['S']['archive_bytes']}
        d['shared_net_gain'] = d['shared_payload_gain'] - j['package']['counted_increment']
        costs = {arm: cell['diagnostics'] for arm, cell in arms.items()}
        d['expert_attribution'] = {
            'shared_relation_bits_saved_vs_independent': costs['I']['relation_bits'] - costs['S']['relation_bits'],
            'shared_relation_bits_saved_vs_wrong': costs['W']['relation_bits'] - costs['S']['relation_bits'],
            'shared_relation_bits_lost_vs_parent': costs['S']['relation_bits'] - costs['S']['parent_bits'],
            'shared_mixture_bits_lost_vs_parent': costs['S']['mixed_bits'] - costs['S']['parent_bits'],
            'scope': 'Native floating log costs on the same complete modeled population; internal expert gains are not additional archive savings. Prediction-active subsets can differ between arms.',
        }
        deltas[pop] = d
        positive.append(all((d[key] > 0 for key in ('shared_payload_gain', 'shared_over_independent', 'shared_over_wrong'))))
    paid = all(d['shared_net_gain'] > 0 and d['shared_over_independent'] > 0 and
               d['shared_over_wrong'] > 0 for d in deltas.values())
    if j['mechanism_supported'] is not paid:
        raise ValueError('reported predicate differs from measured archives and package')
    report = {'schema': 'gamma.enwiki9.relational-binding-terminal.v1', 'comparison': ref(o / 'comparison.json'), 'verified_artifacts': len(manifest['artifacts']), 'job': ref(job_path), 'guard': ref(guard_path), 'comparison_valid': True, 'frozen_paid_fixture_predicate': j['mechanism_supported'], 'binding_payload_supported_all_populations': all(positive), 'deltas': deltas, 'package': j['package'], 'objective_credit_bytes': 0, 'full_corpus_score_bytes': None, 'resources': {'elapsed_seconds': g['elapsed_s'], 'peak_cgroup_bytes': g['peaks']['cgroup_memory_peak_bytes'], 'peak_scratch_allocated_bytes': g['peaks']['max_sampled_scratch_allocated_bytes'], 'cleanup_complete': True, 'timing_authority': 'diagnostic'}, 'interpretation_boundary': 'The frozen mechanism_supported predicate includes paying the full added code on EACH sample. It is stricter than evidence for shared binding. Report payload/control attribution separately. Full fixed code cost is counted once per actual delivery, never multiplied per sample or extrapolated to corpus.', 'verification_implementation': ref(Path(__file__).resolve()), 'next_action': 'Retain fixed binding realization and conditional costs. No larger run or algorithm-family rejection follows from this comparison alone.'}
    write(o / 'terminal.json', report)
    rev = {'candidateId': n, 'candidateTreeSha256': job['candidate_tree_sha256'], 'receipt': job['candidate_revision']}
    index = {'schema': 'gamma.enwiki9.terminal-result-index.v1', 'job': ref(job_path), 'guard': ref(guard_path), 'arms': [], 'evidence': [ref(o / 'comparison.json'), ref(o / 'terminal.json'), ref(o / 'artifacts.json')]}
    for pop, arms in j['measurements'].items():
        for arm, cell in arms.items():
            name = pop + '-' + arm
            archive = r / cell['archive']['path']
            inverse = r / cell['inverse']['path']
            repeat = r / cell['repeat']['path']
            row = {'schema': 'gamma.enwiki9.driver-result.v2', 'program_id': n, 'program_name': 'Causal relational shared binding', 'arm': name, 'candidate_revision': rev, 'timestamp': job['finished_at'], 'run_source': job_path.relative_to(r).as_posix(), 'run_purpose': 'diagnostic', 'run_scope_label': pop + '-raw-native', 'run_context': 'Fresh native P/K/I/S/W with depth-one exact-word latent bindings. Unchanged parent predictions and WRT, introduced state witnesses, independent inverse/repeat.', 'run_tags': ['relational-binding', 'single-coder', 'zero-score-credit'], 'data_size': inverse.stat().st_size, 'data_sha256': sha(inverse), 'compressed_size': archive.stat().st_size, 'compressed_sha256': sha(archive), 'roundtrip_ok': True, 'determinism': {'single_host_byte_equal': True}, 'compress_time_s': phases[name + '-encode']['elapsed_seconds'], 'decompress_time_s': phases[name + '-decode']['elapsed_seconds'], 'program_size': j['package']['binary']['bytes'], 'hutter_score': None, 'complete_package_bytes': None, 'full_corpus_score_bytes': None, 'objective_credit_bytes': 0, 'discovery_resource_gate_pass': True, 'resource_evidence_complete': False, 'score_accounting_complete': False, 'qualification_status': 'not-certified', 'prize_claimable': False, 'missing_diagnostics': ['Full-corpus score and independent resource qualification absent; incremental package only; no full submission frontend.'], 'source_terminal': ref(o / 'comparison.json')}
            p = o / (name + '.driver.json')
            write(p, row)
            index['arms'].append({'arm': name, 'result': ref(p), 'artifacts': {'archive': ref(archive), 'restored': ref(inverse), 'repeat': ref(repeat)}})
    write(o / 'terminal-index.json', index)
    return report

def main():
    print(json.dumps(verify_and_publish(*sys.argv[1:]), indent=2))

if __name__ == "__main__":
    main()
