"""Bind the existing pre-mining reservation to a typed-composer experiment.

No protected statements, references or tests are exported, and no teacher,
predictor or evaluation is run. Metadata screening is not target qualification.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from .. import splits
from ..records import LANE_ROOT
from . import mine, typed_codec as codec, typed_support

SCHEMA = 'algsolve.typed-confirmation.v1'
EXPOSURE_GLOBS = ('*/audit.jsonl', '*/pairs.jsonl', '*/verdicts.jsonl',
                  '*/evaluation.jsonl', '*/solving.jsonl', '*/source-rows.json',
                  '*/reserved-rows.json', 'mine-v2-candidates-20261017/clusters.jsonl')
REQUIRED_EXPOSURES = ('audit-dev-1/audit.jsonl', 'audit-heldout-1/audit.jsonl',
                      'mine-v2-candidates-20261017/clusters.jsonl',
                      'parallel-graph-pilot-v1/evaluation.jsonl',
                      'binary-javascript-v2/source-rows.json',
                      'binary-python-v1/source-rows.json', 'typed-real-dev-v5/pairs.jsonl')
ROUTES = ('parallel_first', 'unguided_search', 'retrieval_guided_search', 'nearest_training_graph')


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read_rows(path):
    return [json.loads(line) for line in Path(path).read_text().splitlines() if line.strip()]


def exposed_families(value, uid_slugs):
    """Read identity fields only; text/code and test payloads do not drive selection."""
    result = set()
    if isinstance(value, list):
        for item in value:
            result.update(exposed_families(item, uid_slugs))
    elif isinstance(value, dict):
        for key, item in value.items():
            slug = None
            if key in ('uid', 'problem_uid') and isinstance(item, str):
                if item not in uid_slugs:
                    raise ValueError(f'Unknown exposure identity: {item}')
                slug = uid_slugs[item]
            elif key in ('key', 'target') and isinstance(item, str) and item.startswith('lc:'):
                slug = item[3:]
            elif key in ('slug', 'family', 'problem_family') and isinstance(item, str):
                slug = item
            elif isinstance(item, (list, dict)):
                result.update(exposed_families(item, uid_slugs))
            if slug:
                result.add(splits.sibling_base(slug))
    return result


def exposure_audit(runs, uid_slugs, reserved_families):
    runs = Path(runs)
    for relative in REQUIRED_EXPOSURES:
        if not (runs/relative).is_file():
            raise ValueError(f'Missing exposure authority: {relative}')
    paths = sorted({path for pattern in EXPOSURE_GLOBS for path in runs.glob(pattern)})
    sources, overlap = [], set()
    for path in paths:
        rows = read_rows(path) if path.suffix == '.jsonl' else json.loads(path.read_text())
        families = exposed_families(rows, uid_slugs)
        found = families & reserved_families
        overlap.update(found)
        sources.append({'path': str(path.relative_to(runs)), 'sha256': sha(path),
                        'identity_families': len(families), 'reserved_overlap': sorted(found)})
    return {'sources': sources, 'overlap_families': sorted(overlap),
            'scope': 'recorded composer audits, mining provenance, pairs, solving runs and binary-input source exposure',
            'limits': ['Not a complete log of human inspection or unrecorded sessions.',
                       'Known-problem lookup/index validation is separate exposure, not composer training.',
                       'Prior foundation-model training exposure is unknown.']}


def verify_development(pairs_path, summary_path, identity):
    summary = json.loads(Path(summary_path).read_text())
    if sha(pairs_path) != summary['artifacts_sha256']['pairs.jsonl'] or summary['codec_sha256'] != identity:
        raise ValueError('Development corpus or codec differs from qualification')
    pairs = read_rows(pairs_path)
    if len(pairs) != summary['qualified_pairs']:
        raise ValueError('Qualified pair count differs')
    for pair in pairs:
        codec.decode(pair['target'], identity)
        if pair['graph_sha256'] != codec.digest(pair['target']):
            raise ValueError('Development graph identity differs')
        if pair['learning_split'] not in ('development_fit', 'development_audit'):
            raise ValueError('Unexpected development partition')
    fit = [p for p in pairs if p['learning_split'] == 'development_fit']
    audit = [p for p in pairs if p['learning_split'] == 'development_audit']
    if not fit or not typed_support.audit(fit, audit)['partition_eligible']:
        raise ValueError('Development feature support/overlap gate failed')
    return pairs


def comparison_protocol():
    return {
        'question': 'Can one parallel prediction assemble a correct unfamiliar typed program faster than bounded search?',
        'routes': list(ROUTES),
        'decision_wall_seconds': 2.0,
        'decision_budget_scope': 'same warm request budget for every route including public checking; timeout is abstention',
        'parallel_first': {'graphs': 1, 'forward_passes': 1, 'refinement_rounds': 0,
                           'source_generation': False, 'repair': False,
                           'heads': ['operation_or_recipe', 'control_structure', 'operand_and_resource_binding', 'bounded_parameter'],
                           'invalid_graph': 'abstain; retain raw first prediction'},
        'search': {'max_candidates': 128, 'wall_seconds': 2.0,
                   'shared_space': 'same typed grammar, graph limits, constants, bindings and expansions as predictor',
                   'ordering': 'unguided uses canonical order; guided changes ranking only',
                   'feedback': 'public examples only; independent scoring never guides search',
                   'fallback': 'reported separately from first-prediction correctness'},
        'inputs': ['statement', 'signature_only_starter', 'parameter_types', 'public_examples'],
        'retrieval': {'allowed': 'frozen fit-side graphs and admitted component contracts only',
                      'forbidden': ['production known-problem index', 'protected references', 'audit targets', 'independent tests'],
                      'embedding': 'same locally available hash-verified Qwen3-Embedding-0.6B across guided routes',
                      'top_k': 4, 'neural_reranker': False},
        'development_selection': {'training_partition': 'development_fit', 'selection_partition': 'development_audit',
                                  'maximum_configurations': 4, 'seed': 17, 'refit_on_audit': False,
                                  'rule': 'highest development first-graph independent correctness; then lower complete latency; then smaller head'},
        'pre_evaluation_seal': ['all route implementation hashes', 'prediction encoding/slot and parameter limits',
                                'checkpoint and embedding hashes', 'training dataset hash',
                                'qualified protected cohort and rejection receipt hashes',
                                'same host/runtime identity', 'route budgets and deterministic tie-breaking'],
        'primary_metrics': ['teacher coverage over fixed pool', 'first-graph correctness over fixed pool',
                            'first-graph correctness on supported teacher-qualified cohort',
                            'wrong acceptance', 'answer coverage', 'abstention', 'human corrections'],
        'timing': {'report': ['cold loading', 'warm embedding', 'retrieval', 'prediction_or_search',
                              'assembly', 'public checking', 'complete decision latency', 'independent scoring'],
                   'complete': 'embedding + retrieval + prediction/search + assembly + public checking; include failures',
                   'distribution': ['p50', 'p95', 'maximum'],
                   'warm_latency_targets_seconds': {'p50': 1.0, 'p95': 2.0},
                   'targets_are': 'experiment targets, not established performance',
                   'quality_passes': 1, 'timing_repeats': 5,
                   'timing_policy': 'freeze all predictions before scoring; repeat frozen routes without changing checkpoints or decisions'},
        'acceptance': 'Report correctness/coverage and latency jointly; faster abstention is not a solving win.',
        'correctness': 'Independent execution agreement accepts any valid graph; exact teacher graph match is diagnostic only.',
        'evaluation': 'One scoring pass of every sealed route, no result-driven changes or replacement tasks; interrupted runs keep their identity.',
        'generative_control': 'Existing 80.2% Codex result is historical, not matched to this pool. A fresh matched control requires its own pre-score seal; no provider launched here.',
    }


def build(entries, problems, reservation, pairs, exposure, identity, sources):
    if mine.digest([e.__dict__ for e in entries]) != reservation['source_sha256']:
        raise ValueError('Research index differs from pre-mining reservation')
    by_key = {e.key: e for e in entries}
    keys = reservation['confirmation_keys']
    if not keys or len(set(keys)) != len(keys) or set(keys)-by_key.keys():
        raise ValueError('Invalid reserved identities')
    protected = {splits.sibling_base(by_key[k].slug) for k in keys}
    if protected & {p['problem_family'] for p in pairs}:
        raise ValueError('Development family overlaps protected pool')
    if exposure['overlap_families']:
        raise ValueError('Recorded exposure reached protected families; quarantine before a new version')
    pool = []
    for key in sorted(keys):
        e = by_key[key]
        p = problems.get(e.judge_uid)
        numeric = bool(e.params) and all(t.replace(' ', '').lower() in
                      ('int', 'bool', 'list[int]', 'list[list[int]]') for _, t in e.params)
        pool.append({'key': key, 'family': splits.sibling_base(e.slug), 'members': sorted(e.members),
                     'judge_uid': e.judge_uid, 'params': e.params,
                     'independent_evidence_available': bool(p and p.evidence_ceiling == 'independent_tests_passed'),
                     'numeric_interface_candidate': numeric,
                     'interface_note': 'Parameter metadata only; bounds, operations and target support unqualified.'})
    return {'schema': SCHEMA, 'codec_sha256': identity, 'sources': sources,
            'reservation': {'policy': 'retain every member of existing pre-mining reservation; no redraw or replacements',
                            'entries': len(pool), 'sibling_families': len(protected), 'pool': pool},
            'exposure_audit': exposure,
            'development': {'fit_graphs': sum(p['learning_split']=='development_fit' for p in pairs),
                            'audit_graphs': sum(p['learning_split']=='development_audit' for p in pairs),
                            'identities': [{'uid': p['uid'], 'family': p['problem_family'], 'graph_sha256':p['graph_sha256'],
                                            'pattern_sha256':p['pattern_sha256'], 'split':p['learning_split']} for p in pairs]},
            'target_qualification': {'status': 'pending', 'protected_targets_opened': False,
                'requirements': ['separate teacher-only artifacts excluded from student and search access',
                                 'frozen codec and complete input/resource bounds',
                                 'all primitive, port, binding, effect, literal and recipe features supported in fit',
                                 'no fit/audit expanded-pattern or sibling-family overlap',
                                 'public and independent oracle qualification; retain invalid test-suite exclusions',
                                 'retain every unsupported target and reason in fixed-pool coverage denominator',
                                 'freeze admitted targets before training; no protected feedback into vocabulary or model selection'],
                'scope': 'Pattern novelty and complete support must be certified; metadata reservation establishes neither.'},
            'comparison': comparison_protocol(),
            'state': {'reservation_frozen': True, 'comparison_policy_frozen': True,
                      'target_cohort_qualified': False, 'training_started': False,
                      'evaluation_ready': False, 'evaluation_opened': False}}


def check(contract_path, pairs_path):
    contract = json.loads(Path(contract_path).read_text())
    if contract['schema'] != SCHEMA:
        raise ValueError('Unknown typed confirmation contract')
    for source in contract['sources'].values():
        path = LANE_ROOT/source['path']
        if sha(path) != source['sha256']:
            raise ValueError(f'Frozen source changed: {source["path"]}')
    identity = codec.frozen(LANE_ROOT/'contracts/typed_codec_v1.json')
    if identity != contract['codec_sha256'] or sha(pairs_path) != contract['sources']['pairs']['sha256']:
        raise ValueError('Codec or training corpus changed')
    pairs = verify_development(pairs_path, LANE_ROOT/contract['sources']['development_summary']['path'], identity)
    protected = {p['family'] for p in contract['reservation']['pool']}
    if protected & {p['problem_family'] for p in pairs}:
        raise ValueError('Protected family entered development corpus')
    for source in contract['exposure_audit']['sources']:
        if sha(LANE_ROOT/'runs'/source['path']) != source['sha256']:
            raise ValueError(f'Exposure authority changed: {source["path"]}')
    entries, problems = splits.read_index_entries(), splits.load_all()
    reservation = json.loads((LANE_ROOT/contract['sources']['reservation']['path']).read_text())
    current = exposure_audit(LANE_ROOT/'runs', {uid:p.slug for uid,p in problems.items()}, protected)
    rebuilt = build(entries, problems, reservation, pairs, current, identity, contract['sources'])
    if rebuilt != contract:
        raise ValueError('Reservation, policy, exposure inventory or development identities changed')
    return contract, pairs


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('freeze', 'check'))
    parser.add_argument('--contract', type=Path, required=True)
    parser.add_argument('--pairs', type=Path, default=LANE_ROOT/'runs/typed-real-dev-v5/pairs.jsonl')
    args = parser.parse_args()
    if args.action == 'check':
        contract, _ = check(args.contract, args.pairs)
    else:
        identity = codec.frozen(LANE_ROOT/'contracts/typed_codec_v1.json')
        paths = {'codec': LANE_ROOT/'contracts/typed_codec_v1.json',
                 'reservation': LANE_ROOT/'findings/mine-v2-candidates-20261017/split.json',
                 'development_summary': LANE_ROOT/'findings/typed-real-dev-v5/summary.json',
                 'development_support': LANE_ROOT/'findings/typed-real-dev-v5/support_audit.json',
                 'pairs': args.pairs, 'sample_manifest': LANE_ROOT/'contracts/sample_manifest.json',
                 'support_implementation': Path(typed_support.__file__),
                 'protocol_implementation': Path(__file__)}
        pairs = verify_development(args.pairs, paths['development_summary'], identity)
        entries, problems = splits.read_index_entries(), splits.load_all()
        reservation = json.loads(paths['reservation'].read_text())
        protected = {splits.sibling_base(k.removeprefix('lc:')) for k in reservation['confirmation_keys']}
        exposure = exposure_audit(LANE_ROOT/'runs', {uid:p.slug for uid,p in problems.items()}, protected)
        sources = {k:{'path':str(p.relative_to(LANE_ROOT)), 'sha256':sha(p)} for k,p in paths.items()}
        contract = build(entries, problems, reservation, pairs, exposure, identity, sources)
        with args.contract.open('x') as stream:
            stream.write(json.dumps(contract,indent=2)+'\n')
    print(json.dumps({'contract_sha256':sha(args.contract), 'pool':contract['reservation']['entries'],
                      'families':contract['reservation']['sibling_families'],
                      'state':contract['state'], 'exposure_sources':len(contract['exposure_audit']['sources'])},indent=2))


if __name__ == '__main__': main()
