"""The authorized BITS pilot: verify qualified targets, train the TypedPredictor
once with the frozen configuration, decide every route from public inputs,
seal the decisions, then score them independently.

  python -m algsolve.synth.bits_pilot --dataset … --authorizations … --plan …
      --build <bits_step1 build output> --name <new run>

Phases (each refuses to continue on a failed check):
1. Verify the target build: artifact hashes from its summary, repository-sandbox
   verification authority (fixtures and test doubles are rejected), every pair
   training-eligible, development_fit and in the frozen plan, and the split
   checks (held-out rows disjoint from every training pair).
2. Train: 400 full-batch AdamW steps, seed 17, width 64, two layers, lr 0.001,
   minimum loss over each problem's qualified alternatives. Retrieval memory is
   the development_fit target graphs only.
3. Decide: for every development_fit, heldout_combination and heldout_family
   problem, from its public input only, with complete captures (all heads):
   raw, constrained, repaired (constrained + guarded recipe/literal repair),
   nearest_training_graph, and direct_bits_search (bounded base-v2 search).
   All decisions are written and hashed before any independent test is read.
4. Score each route with the evaluation reader's independent tests.
Held-out payloads never enter training, teacher generation, retrieval or tuning.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import time

import numpy as np
import torch

from .. import values
from ..embed import Embedder, EXPECTED_SHA256
from ..records import LANE_ROOT
from . import bits_step1, typed_codec, typed_confirmation, typed_base_search
from . import semantic_target_pipeline as pipeline
from .train_typed import INSTRUCTION, query_text, signature
from .typed_comparison import nearest_graph, run_route, score_fixed
from .typed_guard_filter import unreachable_numeric_guard
from .typed_prediction_codec import PredictionCodec
from .typed_predictor import TypedPredictor, decisions, per_example_loss
from .typed_semantic_repair import run_semantic_route

CONFIG = {'steps': 400, 'seed': 17, 'width': 64, 'layers': 2, 'optimizer': 'AdamW', 'learning_rate': .001,
          'retrieval_k': 4, 'decision_wall_seconds': 2.0}
STRUCTURAL = {'fields': ['op', 'first', 'next', 'binding', 'types'], 'alternatives_per_field': 2,
              'max_edit_options': 64, 'max_candidates': 128, 'max_edits': 2, 'wall_seconds': .2}
LITERAL = {'pool_size': 8, 'max_executions': 4, 'max_edits': 2, 'wall_seconds': .25}
ROUTES = ('raw', 'constrained', 'repaired', 'nearest_training_graph', 'direct_bits_search')
SPLITS = ('development_fit', 'heldout_combination', 'heldout_family')


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write(path, value):
    with Path(path).open('x', encoding='utf-8') as stream:
        stream.write(json.dumps(value, indent=1, sort_keys=True) + '\n')


class EvaluationReader:
    """Reads held-out rows for evaluation only, under the pilot authorization.

    ``public_input`` is used to make route decisions; ``independent_tests`` is
    available only after the decisions are sealed (``seal`` must be called).
    The training phase never constructs this reader.
    """

    def __init__(self, adapter, plan, authorization):
        if not isinstance(authorization, dict) or authorization.get('authorized') is not True:
            raise PermissionError('Held-out evaluation requires the pilot training and evaluation authorization')
        self.adapter, self.sealed = adapter, None
        self.rows = {row['uid']: row for row in plan['rows'] if row['split'] in SPLITS}

    def problem(self, uid):
        row = self.rows[uid]
        problem, tests = self.adapter._parse_normalized_pair(self.adapter._require_permitted_identity(uid, row['key']))
        if pipeline.digest(json.loads(problem.to_json())) != row['problem_sha256']:
            raise ValueError(f'Evaluation payload for {uid} differs from the frozen plan')
        return problem, tests

    def public_input(self, uid):
        return pipeline._public_input(self.problem(uid)[0])

    def seal(self, decisions_sha256):
        self.sealed = decisions_sha256

    def independent_tests(self, uid):
        if self.sealed is None:
            raise PermissionError('Independent tests are read only after every decision is sealed')
        problem, tests = self.problem(uid)
        if pipeline.digest(tests) != self.rows[uid]['independent_tests_sha256']:
            raise ValueError(f'Independent tests for {uid} differ from the frozen plan')
        return problem, tests


class PoolReader:
    """Reads a frozen fresh evaluation pool from the pinned dataset, under the pilot authorization.

    Only the pool's problem IDs are kept while scanning; reference solutions are
    dropped on read. Public inputs are used to decide; independent tests only
    after ``seal``.
    """

    def __init__(self, adapter, pool, authorization):
        if not isinstance(authorization, dict) or authorization.get('authorized') is not True:
            raise PermissionError('Fresh-pool evaluation requires the pilot training and evaluation authorization')
        if pool.get('status') != 'frozen' or not pool.get('frozen_by'):
            raise PermissionError('The evaluation pool must be frozen by the owner before use')
        self.adapter, self.sealed = adapter, None
        wanted = {row['uid'] for row in pool['rows']}
        self.raw = {}
        with Path(adapter.dataset_path).open(encoding='utf-8') as stream:
            for line in stream:
                if not line.strip():
                    continue
                record = json.loads(line)
                uid = f"lcd:{record['question_id']}"
                if uid in wanted:
                    self.raw[uid] = {k: str(record[k]) if k not in ('tags',) else list(record.get(k) or [])
                                     for k in ('question_id', 'task_id', 'entry_point', 'starter_code',
                                               'problem_description', 'test', 'estimated_date', 'difficulty', 'tags')}
        missing = wanted - set(self.raw)
        if missing:
            raise ValueError(f'Pool rows absent from the pinned dataset: {sorted(missing)[:5]}')
        self.rows = {row['uid']: dict(row, split='fresh_pool') for row in pool['rows']}

    def problem(self, uid):
        return self.adapter._parse_normalized_pair(self.raw[uid])

    def seal(self, decisions_sha256):
        self.sealed = decisions_sha256

    def independent_tests(self, uid):
        if self.sealed is None:
            raise PermissionError('Independent tests are read only after every decision is sealed')
        return self.problem(uid)


def verify_build(build, plan):
    contract = json.loads((build / 'contract.json').read_text())
    summary = json.loads((build / 'summary.json').read_text())
    if contract.get('verification_authority') != 'repository-sandbox' or not contract.get('authorizations'):
        raise PermissionError('Targets were not qualified by the repository sandbox (fixture or test double)')
    if contract['plan_sha256'] != plan['plan_sha256'] or summary['plan_sha256'] != plan['plan_sha256']:
        raise ValueError('Target build belongs to a different plan')
    for name, digest in summary['artifacts_sha256'].items():
        if name != 'summary.json' and sha(build / name) != digest:
            raise ValueError(f'Target build artifact changed: {name}')
    fit = {row['uid'] for row in plan['rows'] if row['split'] == 'development_fit'}
    heldout = {row['uid'] for row in plan['rows'] if row['split'] in ('heldout_combination', 'heldout_family')}
    pairs = [json.loads(line) for line in (build / 'pairs.jsonl').read_text().splitlines()]
    for pair in pairs:
        if (pair.get('training_eligible') is not True or pair['learning_split'] != 'development_fit'
                or pair['uid'] not in fit or pair['provenance']['verification_authority'] != 'repository-sandbox'):
            raise PermissionError(f'Ineligible training pair: {pair["uid"]}')
    if heldout & {p['uid'] for p in pairs}:
        raise PermissionError('Held-out problems appear among training pairs')
    if not pairs:
        raise ValueError('No qualified training pairs')
    return contract, summary, pairs


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--dataset', required=True, type=Path)
    parser.add_argument('--authorizations', required=True, type=Path)
    parser.add_argument('--plan', required=True, type=Path)
    parser.add_argument('--build', required=True, type=Path)
    parser.add_argument('--name', required=True)
    parser.add_argument('--steps', type=int, default=CONFIG['steps'],
                        help='Training steps (the pilot contract froze 400; the approved reproduction uses 4000)')
    parser.add_argument('--pool', type=Path, default=None,
                        help='Frozen fresh evaluation pool; the plan held-out rows are then reported as development_heldout')
    args = parser.parse_args()
    steps = args.steps
    if type(steps) is not int or steps < 1:
        raise ValueError('steps must be a positive integer')
    if not args.name.replace('-', '').isalnum():
        raise ValueError('Invalid run name')
    records, records_sha = bits_step1.load_authorizations(args.authorizations)
    authorization = records.get('pilot_training_and_evaluation')
    if not isinstance(authorization, dict) or authorization.get('authorized') is not True:
        raise PermissionError('Pilot training and evaluation are not authorized')
    plan = pipeline.validate_plan(json.loads(args.plan.read_bytes()))
    build_contract, build_summary, pairs = verify_build(args.build, plan)
    identity = typed_codec.frozen(LANE_ROOT / 'contracts/typed_codec_v1.json')
    torch.set_num_threads(4); torch.manual_seed(CONFIG['seed'])
    assert torch.equal(torch.ones(2, 2) @ torch.ones(2, 2), torch.full((2, 2), 2.))
    output = LANE_ROOT / 'runs' / args.name
    output.mkdir(exist_ok=False)
    split_checks = {'training_pairs': len(pairs), 'training_problems': len({p['uid'] for p in pairs}),
                    'heldout_in_training': 0, 'retrieval_memory': 'development_fit target graphs only',
                    'teacher_inputs': 'development_fit public inputs only (build contract)'}

    # Phase 2: training on development_fit pairs only.
    encoding = PredictionCodec.fit(pairs)
    labels = {k: torch.tensor([encoding.encode(p['target']['program'])[k] for p in pairs])
              for k in encoding.encode(pairs[0]['target']['program'])}
    fit_uids = list(dict.fromkeys(p['uid'] for p in pairs))
    groups = [[j for j, p in enumerate(pairs) if p['uid'] == uid] for uid in fit_uids]
    started = time.perf_counter(); embedder = Embedder(device='cpu'); embedder_load = time.perf_counter() - started
    memory_text = [typed_codec.digest(p['target']) + ' ' + json.dumps(p['target']['program'], sort_keys=True) for p in pairs]
    started = time.perf_counter(); contracts = embedder.encode(memory_text, batch_size=4); memory_seconds = time.perf_counter() - started
    fit_input = {p['uid']: p for p in pairs}
    fit_vectors = np.array([embedder.encode([query_text(fit_input[uid])], query=True, instruction=INSTRUCTION)[0] for uid in fit_uids])
    neighbor_index = [np.argsort(-(contracts @ v), kind='stable')[:CONFIG['retrieval_k']] for v in fit_vectors]
    model = TypedPredictor(fit_vectors.shape[1], encoding.slots, len(encoding.types), width=CONFIG['width'])
    optimizer = torch.optim.AdamW(model.parameters(), lr=CONFIG['learning_rate'])
    query = torch.from_numpy(fit_vectors); memory = torch.from_numpy(contracts[np.array(neighbor_index)])
    row_of = {uid: i for i, uid in enumerate(fit_uids)}
    targets = [row_of[p['uid']] for p in pairs]
    contract = {'schema': 'algsolve.bits-pilot.v1', 'config': {**CONFIG, 'steps': steps}, 'structural_config': STRUCTURAL,
                'evaluation_pool_sha256': sha(args.pool) if args.pool else None,
                'literal_config': LITERAL, 'codec_sha256': identity, 'prediction_encoding': encoding.descriptor(),
                'plan_sha256': plan['plan_sha256'], 'build_summary_sha256': sha(args.build / 'summary.json'),
                'build_pairs_sha256': sha(args.build / 'pairs.jsonl'), 'authorizations_sha256': records_sha,
                'embedding_weights': EXPECTED_SHA256, 'split_checks': split_checks, 'routes': ROUTES,
                'selection': 'fixed final step; no sweep, early stopping or held-out-driven retries'}
    write(output / 'contract.json', contract)
    print(f'[run-contract] run_name={args.name} pairs_input_spec={args.build / "pairs.jsonl"} resume_from=none '
          'resume_stage=none decode=parallel-argmax+bounded-repair eval_dataset_paths=frozen-plan-splits device=cpu '
          'schedule=full_batch runtime_mode=cpu sweep_mode=after_train', flush=True)
    started = time.perf_counter(); model.train()
    with (output / 'metrics.jsonl').open('w') as stream:
        for step in range(steps):
            optimizer.zero_grad()
            logits = model(query[targets], memory[targets])
            per_target = per_example_loss(logits, labels)
            loss = torch.stack([per_target[g].min() for g in groups]).mean()
            loss.backward(); optimizer.step()
            if step == 0 or (step + 1) % 20 == 0:
                metric = {'step': step + 1, 'loss': float(loss.detach()), 'elapsed_seconds': time.perf_counter() - started}
                stream.write(json.dumps(metric) + '\n'); stream.flush(); print('[train] ' + json.dumps(metric), flush=True)
    training_seconds = time.perf_counter() - started
    torch.save({'state_dict': model.state_dict(), 'contract': contract}, output / 'model.pt')
    # Everything needed to reload the trained predictor for inference without the training code.
    write(output / 'codec.json', encoding.descriptor())
    write(output / 'inference.json', {'model': 'model.pt', 'architecture': 'TypedPredictor', 'width': CONFIG['width'],
                                      'embedding_dim': int(fit_vectors.shape[1]), 'slots': encoding.slots,
                                      'type_count': len(encoding.types), 'codec': 'codec.json', 'codec_sha256': identity,
                                      'embedding_weights': EXPECTED_SHA256, 'query_instruction': INSTRUCTION,
                                      'retrieval_k': CONFIG['retrieval_k'],
                                      'retrieval_memory': 'development_fit target graphs of the build pairs, in pairs.jsonl order',
                                      'build_pairs_sha256': sha(args.build / 'pairs.jsonl'),
                                      'structural_config': STRUCTURAL, 'literal_config': LITERAL,
                                      'decision_wall_seconds': CONFIG['decision_wall_seconds'], 'routes': ROUTES})
    model.eval()

    # Phase 3: decisions from public inputs only, sealed before scoring.
    _, adapter = bits_step1.open_adapter(args.dataset, records)
    adapter.bind_plan(plan)
    reader = EvaluationReader(adapter, plan, authorization)
    requests = [row for row in plan['rows'] if row['split'] in SPLITS]
    pool_reader = None
    if args.pool is not None:
        pool_reader = PoolReader(adapter, json.loads(args.pool.read_text()), authorization)
        # The plan's held-out rows were evaluated by the first pilot: development only.
        requests = [dict(row, split='development_fit' if row['split'] == 'development_fit' else 'development_heldout')
                    for row in requests] + list(pool_reader.rows.values())
    def reader_for(uid):
        return pool_reader if pool_reader is not None and uid in pool_reader.rows else reader
    request_rows = []
    for row in requests:
        problem, _ = reader_for(row['uid']).problem(row['uid'])
        public = pipeline._public_input(problem)
        pair = {'uid': row['uid'], 'learning_split': row['split'], 'input': public, 'problem_family': row['family']}
        params = [p[0] for p in problem.params]
        started = time.perf_counter()
        vector = embedder.encode([query_text(pair)], query=True, instruction=INSTRUCTION)[0]
        embedding = time.perf_counter() - started
        started = time.perf_counter(); similarities = contracts @ vector
        neighbors = np.argsort(-similarities, kind='stable')[:CONFIG['retrieval_k']]; retrieval = time.perf_counter() - started
        started = time.perf_counter()
        with torch.inference_mode():
            logits = model(torch.from_numpy(vector[None]), torch.from_numpy(contracts[neighbors][None]))
            raw = decisions(logits)
            scores = {k: v[0].tolist() for k, v in logits.items()}
        prediction = time.perf_counter() - started
        shared = embedding + retrieval + prediction
        capture = {'uid': row['uid'], 'split': row['split'], 'codes': raw, 'logits': {k: v for k, v in scores.items() if k != 'bits'},
                   'literal_logits': scores['bits'], 'heads': sorted(scores), 'neighbors': [int(n) for n in neighbors],
                   'identity': {'codec_sha256': identity, 'request_sha256': typed_codec.digest(public)},
                   'embedding_seconds': embedding, 'retrieval_seconds': retrieval, 'prediction_seconds': prediction}
        full_logits = {**capture['logits'], 'bits': scores['bits']}
        routes = {}
        routes['raw'] = run_route('raw', problem, raw, capture['logits'], encoding, identity, shared, STRUCTURAL, 2.)
        routes['constrained'] = run_route('constrained', problem, raw, capture['logits'], encoding, identity, shared, STRUCTURAL, 2.)
        routes['repaired'] = run_semantic_route(routes['constrained'], problem, full_logits, encoding, identity, LITERAL, 2.,
                                                literal_filter=unreachable_numeric_guard)
        started = time.perf_counter()
        graph, graph_hash, reason = nearest_graph({'input': public}, pairs, similarities.tolist(), encoding)
        construction = time.perf_counter() - started
        routes['nearest_training_graph'] = run_route('nearest_training_graph', problem, raw, capture['logits'], encoding, identity,
                                                     shared, STRUCTURAL, 2., baseline_graph=graph, baseline_hash=graph_hash,
                                                     baseline_reason=reason, baseline_seconds=embedding + retrieval,
                                                     baseline_construction_seconds=construction)
        started = time.perf_counter()
        try:
            return_annotation = values.return_annotation(problem.starter_code, problem.entry['method'])
        except values.Unsupported:
            return_annotation = None
        found = typed_base_search.search(problem.params, return_annotation, problem.public_tests,
                                         deadline=started + CONFIG['decision_wall_seconds'])
        search_route = {'route': 'direct_bits_search', 'decision': 'abstain', 'reason': found['reason'], 'source': None,
                        'graph_sha256': None, 'final_graph': found['graph'], 'structurally_valid': found['graph'] is not None,
                        'infrastructure_failure': False, 'public': None,
                        'search': {k: found[k] for k in ('candidates', 'invalid', 'executions', 'reason', 'seconds')},
                        'timing': {'total_seconds': time.perf_counter() - started}}
        if found['graph'] is not None and search_route['timing']['total_seconds'] <= CONFIG['decision_wall_seconds']:
            target = typed_codec.encode(found['graph'], identity)
            search_route.update(decision='answered', graph_sha256=typed_codec.digest(target),
                                source=typed_codec.render(target, identity, method=problem.entry['method'], params=params))
        routes['direct_bits_search'] = search_route
        request_rows.append({'uid': row['uid'], 'split': row['split'], 'capture': capture, 'routes': routes})
        print(json.dumps({'decided': len(request_rows), 'total': len(requests), 'split': row['split'],
                          'decisions': {k: v['decision'] for k, v in routes.items()}}), flush=True)
    write(output / 'decisions.json', request_rows)
    decisions_sha = sha(output / 'decisions.json')
    reader.seal(decisions_sha)
    if pool_reader is not None:
        pool_reader.seal(decisions_sha)

    # Phase 4: independent scoring after the seal.
    scored = []
    for record in request_rows:
        problem, tests = reader_for(record['uid']).independent_tests(record['uid'])
        row = {'uid': record['uid'], 'split': record['split'], 'routes': {}}
        for name, route in record['routes'].items():
            started = time.perf_counter()
            result = score_fixed(route, problem, tests)
            repair = route.get('semantic_repair') or {}
            row['routes'][name] = {'decision': route['decision'], 'reason': route['reason'],
                                   'structurally_valid': route.get('structurally_valid', False),
                                   'accepted_correct': result['accepted_correct'], 'wrong_acceptance': result['wrong_acceptance'],
                                   'independently_correct': result['independently_correct'],
                                   'unsupported': route['reason'] == 'unsupported_signature',
                                   'public_executions': (1 if route.get('public') else 0) + repair.get('executions', 0)
                                                        + (route.get('search') or {}).get('executions', 0),
                                   'decision_seconds': route['timing']['total_seconds'],
                                   'independent_scoring_seconds': time.perf_counter() - started}
        scored.append(row)
    write(output / 'scores.json', scored)
    summary = {'schema': 'algsolve.bits-pilot-summary.v1', 'decisions_sha256': decisions_sha,
               'checkpoint_sha256': sha(output / 'model.pt'), 'training_seconds': training_seconds,
               'embedder_load_seconds': embedder_load, 'memory_embedding_seconds': memory_seconds,
               'split_checks': split_checks, 'splits': {}}
    for split in dict.fromkeys(r['split'] for r in scored):
        rows = [r for r in scored if r['split'] == split]
        summary['splits'][split] = {'problems': len(rows), 'routes': {}}
        for name in ROUTES:
            rs = [r['routes'][name] for r in rows]
            summary['splits'][split]['routes'][name] = {
                'accepted_correct': sum(r['accepted_correct'] for r in rs),
                'wrong_acceptances': sum(r['wrong_acceptance'] for r in rs),
                'abstentions': sum(r['decision'] == 'abstain' for r in rs),
                'unsupported': sum(r['unsupported'] for r in rs),
                'structurally_valid': sum(r['structurally_valid'] for r in rs),
                'public_executions': sum(r['public_executions'] for r in rs),
                'decision_seconds_p50': float(np.median([r['decision_seconds'] for r in rs])) if rs else None,
                'independent_scoring_seconds': sum(r['independent_scoring_seconds'] for r in rs)}
    summary['first_pass_vs_repaired'] = {s: {'first_pass': summary['splits'][s]['routes']['constrained']['accepted_correct'],
                                             'repaired': summary['splits'][s]['routes']['repaired']['accepted_correct']}
                                         for s in summary['splits']}
    summary['limits'] = ['One seed and one fixed configuration; not a generalization claim beyond these splits.',
                         'Targets come from one teacher run; problems without a qualified target are absent from training, not from evaluation.',
                         'Decision timing includes embedding, retrieval, prediction, repair and public checks; memory embedding setup is separate.']
    write(output / 'summary.json', summary)
    print(json.dumps(summary['splits'], indent=1))


if __name__ == '__main__':
    main()
