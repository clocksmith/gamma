"""Independently verify a closed relational comparison and prepare driver records.

Usage: python -m gamma_enwiki9.adapters.fx2_relational_terminal ROOT CANDIDATE JOB
Run from the repository root. The terminal and driver index are published once;
the lab reflection must bind the index before record_driver_result can append it.
This interpreter is bound in its own terminal record, separately from execution.
"""
from pathlib import Path
import json, sys
from gamma_enwiki9.evidence.artifacts import canonical_bytes, fingerprint, publish_immutable_artifact

def main():
    r = Path(sys.argv[1]).resolve()
    n = sys.argv[2]
    job_id = sys.argv[3]
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
    job_path = next((r / 'operations/adaptive/completed').glob('*' + job_id + '.json'))
    job = json.loads(job_path.read_bytes())
    experiment_path = r / job['experiment']['path']
    if sha(experiment_path) != job['experiment']['sha256'].removeprefix('sha256:'):
        raise ValueError('bound experiment changed')
    experiment = json.loads(experiment_path.read_bytes())
    inputs = {v['path']: v['sha256'].removeprefix('sha256:') for v in experiment['inputs']}
    plan_path = r / 'operations/provenance' / (n + '_plan.json')
    if sha(plan_path) != inputs[plan_path.relative_to(r).as_posix()]:
        raise ValueError('bound plan changed')
    plan = json.loads(plan_path.read_bytes())
    package = j['package']
    binary_delta = (o / 'native/cmix').stat().st_size - (r / plan['parent_binary']).stat().st_size
    source_delta = (o / 'S-source.zip').stat().st_size - (o / 'P-source.zip').stat().st_size
    expected_increment = min(2 * binary_delta, source_delta + binary_delta) + len('GAMMA_RELATIONAL_ARM=S')
    if package['counted_increment'] != expected_increment:
        raise ValueError('counted code increment does not match actual alternatives')
    guard_path = r / job['execution_resources']['guard_path']
    g = json.loads(guard_path.read_bytes())
    if not (job['returncode'] == 0 and job['execution_resources']['cleanup_complete'] and (g['status'] == 'complete') and (not any(g['guards'].values()))):
        raise ValueError("terminal verification failed: job['returncode'] == 0 and job['execution_resources']['cleanup_complete'] and (g['status'] == 'complete') and (not any(g['guards'].values()))")
    phases = {x['phase']: x for x in j['commands']}
    deltas = {}
    positive = []
    for pop, arms in j['measurements'].items():
        for arm, cell in arms.items():
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
        deltas[pop] = d
        positive.append(all((d[key] > 0 for key in ('shared_payload_gain', 'shared_over_independent', 'shared_over_wrong'))))
    if not len(j['commands']) == 51:
        raise ValueError("terminal verification failed: len(j['commands']) == 51")
    if not set(j['measurements']) == {'development', 'validation', 'confirmation'}:
        raise ValueError("terminal verification failed: set(j['measurements']) == {'development', 'validation', 'confirmation'}")
    if not all((set(arms) == set('PKISW') for arms in j['measurements'].values())):
        raise ValueError("terminal verification failed: all((set(arms) == set('PKISW') for arms in j['measurements'].values()))")
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
    print(json.dumps(report, indent=2))

if __name__ == "__main__":
    main()
