"""Bounded CPU pilot: parallel graph prediction versus nearest training graph.

This is a development pattern-split diagnostic, not the protected confirmation
campaign. Frozen local embeddings guide both routes. No downloads, generation,
search, retries, RL, or evaluation-driven model selection.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import time

import numpy as np
import torch

from .. import splits, validate
from ..embed import Embedder, EXPECTED_SHA256
from ..records import LANE_ROOT, load_hidden_tests
from . import call_graph, mine, training_pairs
from .parallel_graph import Codec, ParallelGraphPredictor, supervised_loss

INSTRUCTION = 'Instruct: Retrieve reusable algorithms that solve this programming task\nQuery: '


def evaluate(pair, codes, codec, problem, embedding_seconds, prediction_seconds):
    started = time.perf_counter()
    try:
        graph = codec.decode(*codes, params=[p[0] for p in problem.params])
        compiled = call_graph.compile_graph(graph, method=problem.entry['method'], params=[p[0] for p in problem.params])
    except (ValueError, TypeError, IndexError, SyntaxError) as error:
        return {'decision': 'abstain', 'reason': 'invalid_prediction', 'error': str(error),
                'first_prediction_correct': False, 'seconds': embedding_seconds + prediction_seconds + time.perf_counter()-started}
    public = validate.judge_problem(problem, compiled.source, problem.public_tests)
    public_seconds = time.perf_counter() - started
    # Scoring only; this outcome never changes the prediction or acceptance.
    independent = validate.judge_problem(problem, compiled.source, load_hidden_tests(problem)) if public.passed else None
    return {'decision': 'answered' if public.passed else 'abstain', 'graph': graph,
            'public': public.to_dict(), 'independent': independent.to_dict() if independent else None,
            'first_prediction_correct': bool(independent and independent.passed),
            'source_sha256': hashlib.sha256(compiled.source.encode()).hexdigest(),
            'embedding_seconds': embedding_seconds, 'prediction_seconds': prediction_seconds,
            'assembly_public_check_seconds': public_seconds,
            'seconds': embedding_seconds + prediction_seconds + public_seconds,
            'independent_scoring_seconds': time.perf_counter() - started - public_seconds}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--dataset', type=Path, required=True)
    parser.add_argument('--name', required=True)
    parser.add_argument('--steps', type=int, default=200)
    args = parser.parse_args()
    if not args.name.replace('-', '').replace('_', '').isalnum() or not 1 <= args.steps <= 1000:
        raise ValueError('Invalid run name or bounded step count')
    import transformers
    torch.set_num_threads(4)
    torch.manual_seed(17)
    probe = torch.ones(2, 2) @ torch.ones(2, 2)
    assert torch.equal(probe, torch.full((2, 2), 2.))
    print(f'[compute] torch={torch.__version__} transformers={transformers.__version__} '
          f'cuda_available={torch.cuda.is_available()} cuda_count={torch.cuda.device_count()} '
          'target=cpu matmul=passed', flush=True)
    pairs = [json.loads(line) for line in args.dataset.read_text().splitlines()]
    summary = json.loads(args.dataset.with_name('summary.json').read_text())
    if summary['pairs_sha256'] != training_pairs.sha(args.dataset):
        raise ValueError('Dataset receipt mismatch')
    if any(p['target']['vocabulary_sha256'] != call_graph.vocabulary_hash() for p in pairs):
        raise ValueError('Dataset vocabulary drift')
    training = [p for p in pairs if p['learning_split'] == 'training']
    confirmation = [p for p in pairs if p['learning_split'] == 'pattern_confirmation']
    if not training or not confirmation:
        raise ValueError('Need nonempty training and pattern-confirmation groups')
    for key in ('uid', 'problem_family', 'split_group_sha256', 'pattern_sha256'):
        if {p[key] for p in training} & {p[key] for p in confirmation}:
            raise ValueError(f'Training/confirmation overlap: {key}')
    codec = Codec.fit(training)
    targets = tuple(torch.stack([codec.encode(pair)[i] for pair in training]) for i in range(3))
    directory = LANE_ROOT/'runs'/args.name
    directory.mkdir(parents=True, exist_ok=False)
    contract = {'dataset_sha256': training_pairs.sha(args.dataset), 'vocabulary_sha256': call_graph.vocabulary_hash(),
                'embedding_weights': EXPECTED_SHA256, 'query_instruction': INSTRUCTION,
                'training_uids': [p['uid'] for p in training], 'pattern_confirmation_uids': [p['uid'] for p in confirmation],
                'templates': codec.templates, 'seed': 17, 'steps': args.steps, 'width': 64, 'layers': 2,
                'optimizer': 'AdamW', 'learning_rate': .001, 'retrieved_contracts': 4,
                'device': 'cpu', 'threads': 4, 'decode': 'one parallel forward, independent argmax, deterministic validation',
                'source_sha256': {name: training_pairs.sha(Path(__file__).with_name(name))
                                  for name in ('parallel_graph.py', 'train_parallel.py')},
                'evaluation_policy': 'one frozen checkpoint; no retries; independent tests for scoring only',
                'scope': 'selected development tasks, pattern split; not reserved external confirmation'}
    (directory/'contract.json').write_text(json.dumps(contract, indent=2)+'\n')
    print(f'[run-contract] run_name={args.name} pairs_input_spec={args.dataset} resume_from=none '
          'resume_stage=none decode=parallel-argmax eval_dataset_paths=development-pattern-confirmation '
          'device=cpu schedule=full_batch runtime_mode=cpu sweep_mode=after_train', flush=True)
    started = time.perf_counter()
    embedder = Embedder(device='cpu')
    cold_embedding_seconds = time.perf_counter() - started
    names = sorted(call_graph.catalog())
    descriptions = [name + ': ' + call_graph.catalog()[name]['contract'] for name in names]
    contract_vectors = embedder.encode(descriptions, batch_size=4)
    vectors, encode_seconds = [], []
    for pair in pairs:
        started = time.perf_counter()
        text = pair['input']['statement'] + '\n\n' + pair['input']['starter_code']
        vectors.append(embedder.encode([text], query=True, instruction=INSTRUCTION)[0])
        encode_seconds.append(time.perf_counter() - started)
    vectors = np.array(vectors)
    neighbors = np.argsort(-(vectors @ contract_vectors.T), axis=1, kind='stable')[:, :4]
    query = torch.from_numpy(vectors)
    memory = torch.from_numpy(contract_vectors[neighbors])
    train_indices = [i for i, p in enumerate(pairs) if p['learning_split'] == 'training']
    model = ParallelGraphPredictor(vectors.shape[1], len(codec.templates))
    optimizer = torch.optim.AdamW(model.parameters(), lr=.001)
    started = time.perf_counter()
    model.train()
    with (directory/'metrics.jsonl').open('w') as stream:
        for step in range(args.steps):
            optimizer.zero_grad()
            loss = supervised_loss(model(query[train_indices], memory[train_indices]), targets)
            loss.backward()
            optimizer.step()
            if step == 0 or (step+1) % 20 == 0 or step+1 == args.steps:
                row = {'step': step+1, 'loss': float(loss.detach()), 'seconds': time.perf_counter()-started}
                stream.write(json.dumps(row)+'\n'); stream.flush()
                print('[train] ' + json.dumps(row), flush=True)
    training_seconds = time.perf_counter()-started
    torch.save({'state_dict': model.state_dict(), 'contract': contract}, directory/'model.pt')
    checkpoint_sha = training_pairs.sha(directory/'model.pt')
    model.eval()
    problems = splits.load_all()
    rows = []
    with (directory/'evaluation.jsonl').open('w') as stream, torch.inference_mode():
        for i, pair in enumerate(pairs):
            started = time.perf_counter()
            logits = model(query[i:i+1], memory[i:i+1])
            predicted = tuple(output[0].argmax(dim=-1) for output in logits)
            prediction_seconds = time.perf_counter()-started
            neural = evaluate(pair, predicted, codec, problems[pair['uid']], encode_seconds[i], prediction_seconds)
            started = time.perf_counter()
            closest = int(np.argmax(vectors[train_indices] @ vectors[i]))
            baseline_codes = codec.encode(training[closest])
            baseline_seconds = time.perf_counter()-started
            baseline = evaluate(pair, baseline_codes, codec, problems[pair['uid']], encode_seconds[i], baseline_seconds)
            try:
                codec.encode(pair)
                representable = True
            except ValueError:
                representable = False
            row = {'uid': pair['uid'], 'split': pair['learning_split'], 'target_in_training_template_bank': representable,
                   'retrieved_contracts': [names[j] for j in neighbors[i]], 'neural': neural, 'nearest_training_graph': baseline}
            rows.append(row); stream.write(json.dumps(row)+'\n'); stream.flush()
            print(f'[predict] {pair["uid"]} {pair["learning_split"]} correct={neural["first_prediction_correct"]}', flush=True)
    result = {'checkpoint_sha256': checkpoint_sha, 'parameters': sum(p.numel() for p in model.parameters()),
              'cold_embedding_load_seconds': cold_embedding_seconds, 'training_seconds': training_seconds,
              'template_count': len(codec.templates), 'splits': {}}
    for split in ('training', 'pattern_confirmation'):
        selected = [r for r in rows if r['split'] == split]
        result['splits'][split] = {'tasks': len(selected),
                                  'teacher_targets_representable': sum(r['target_in_training_template_bank'] for r in selected)}
        for route in ('neural', 'nearest_training_graph'):
            result['splits'][split][route] = {
                'first_prediction_correct': sum(r[route]['first_prediction_correct'] for r in selected),
                'answered': sum(r[route]['decision'] == 'answered' for r in selected),
                'wrong_acceptances': sum(r[route]['decision'] == 'answered' and not r[route]['first_prediction_correct'] for r in selected),
                'p50_seconds': float(np.percentile([r[route]['seconds'] for r in selected], 50)),
                'p95_seconds': float(np.percentile([r[route]['seconds'] for r in selected], 95))}
    result['limits'] = ['Small selected development set, not a benchmark coverage estimate.',
                        'Frozen embedding plus train-only expression bank; no general AST prediction.',
                        'Measured task times include warm embedding, prediction, assembly and public checks; independent scoring excluded.',
                        'Teacher-tested graphs do not establish student generalization.']
    (directory/'summary.json').write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
