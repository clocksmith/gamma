"""Frozen recognition journey: stored answer, public gate, independent scoring.

The corpus index is intentionally available for known-problem recognition only.
Absent cases exclude the source's entire sibling family (controlled diagnostic).
No synthesis, generation, fitting, repair, or hidden-test feedback to the route.
"""
from __future__ import annotations
import argparse
from collections import Counter, defaultdict
from dataclasses import replace
import json
from pathlib import Path
import time

import numpy as np
import torch

from . import corpus, paraphrase, splits, validate
from .answer import answer
from .embed import Embedder, EXPECTED_SHA256
from .lookup import LookupIndex, load_thresholds
from .records import LANE_ROOT, load_hidden_tests
from .public_examples import recover
from .rerank_recognition import diagnostic_entries, digest
from .routes import Budget, Context
from .synth.training_pairs import sha


def make_query(spec, by_key, problems, paragraphs):
    if spec['kind'] == 'absent_exact':
        source = problems[spec['problem_uid']]
        return source, recover(replace(source, hidden_tests_path='', reference_solutions=[], import_notes={}))
    entry = by_key[spec['target']]
    source = problems[entry.judge_uid]
    if source.entry != entry.entry or source.params != entry.params:
        raise ValueError('Query and independent judge signatures disagree')
    statement = entry.statement if spec['kind'] == 'exact' else paragraphs[entry.key]['paraphrase']
    query = replace(recover(source), statement=statement, starter_code=entry.starter_code,
                    hidden_tests_path='', reference_solutions=[], import_notes={})
    return source, query


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--name', required=True)
    parser.add_argument('--device', choices=('cpu', 'cuda'), default='cuda')
    args = parser.parse_args()
    if not args.name.replace('-', '').replace('_', '').isalnum():
        raise ValueError('Invalid run name')
    torch.set_num_threads(4)
    x = torch.ones((2, 2), device=args.device)
    assert torch.equal((x@x).cpu(), torch.full((2, 2), 2.))
    entries = corpus.read_entries()
    if json.loads(corpus.KEYS_PATH.read_text()) != [e.key for e in entries]:
        raise ValueError('Corpus embedding order differs')
    vectors = np.load(corpus.EMBEDDINGS_PATH)
    by_key, problems = {e.key:e for e in entries}, splits.load_all()
    paragraphs = {r['key']:r for r in map(json.loads, paraphrase.PARAPHRASES_PATH.read_text().splitlines())}
    manifest = splits.load_manifest()
    route_contract = json.loads((LANE_ROOT/'contracts/run_contract.json').read_text())
    directory = LANE_ROOT/'runs'/args.name
    directory.mkdir(parents=True, exist_ok=False)
    contract = {'index': 'all-corpus known-problem service', 'entries': len(entries),
                'queries': manifest['recognition'], 'thresholds': load_thresholds(),
                'device': args.device, 'dtype': 'float16' if args.device == 'cuda' else 'float32',
                'torch': torch.__version__, 'embedding_weights': EXPECTED_SHA256,
                'files': {str(path.relative_to(LANE_ROOT)):sha(path) for path in
                          [corpus.ENTRIES_PATH, corpus.EMBEDDINGS_PATH, corpus.KEYS_PATH, paraphrase.PARAPHRASES_PATH,
                           LANE_ROOT/'contracts/sample_manifest.json']},
                'source': {name:sha(LANE_ROOT/'algsolve'/name) for name in
                           ['answer.py','answer_evaluation.py','embed.py','lookup.py','validate.py','records.py',
                            'public_examples.py','values.py','importers.py',
                            'test_corrections.py','judge/judge.py','judge/functional_semantics.py','judge/harness_functional.py']},
                'oracle_inputs': {q['qid']: {'public_sha256': digest(make_query(q, by_key, problems, paragraphs)[1].public_tests),
                                            'independent_sha256': digest(load_hidden_tests(make_query(q, by_key, problems, paragraphs)[0]))}
                                  for q in manifest['recognition']},
                'generation': False, 'reranking': False, 'hidden_test_role': 'scoring only, after answer decision',
                'absent_policy': 'exclude entire canonical sibling family per query; not natural absence'}
    (directory/'contract.json').write_text(json.dumps(contract, indent=2)+'\n')
    print(f'[run-contract] run_name={args.name} pairs_input_spec=frozen-recognition '
          f'resume_from=none resume_stage=none decode=none eval_dataset_paths=recognition '
          f'device={args.device} schedule=serial runtime_mode={args.device}+linux-sandbox sweep_mode=after_train', flush=True)
    started = time.perf_counter(); embedder = Embedder(device=args.device)
    load_seconds = time.perf_counter()-started
    groups, times, answered_times = defaultdict(Counter), defaultdict(list), defaultdict(list)
    with (directory/'answers.jsonl').open('w') as stream:
        for i, spec in enumerate(manifest['recognition']):
            original, query = make_query(spec, by_key, problems, paragraphs)
            indices = diagnostic_entries(entries, spec, problems)
            active = [entries[j] for j in indices]
            context = Context(generator=None, embedder=embedder, lookup=LookupIndex(active, vectors[indices]),
                              thresholds=contract['thresholds'], classifier=None, entries=active,
                              budget=Budget.from_contract(route_contract))
            result = answer(context, query)
            independent = load_hidden_tests(original)
            score = validate.judge_problem(original, result['code'], independent) if result['code'] and independent else None
            kind = 'controlled_absent' if spec['kind'] == 'absent_exact' else spec['kind']
            count = groups[kind]; count['queries'] += 1
            count['query_has_public_examples'] += int(bool(query.public_tests))
            count['answered'] += int(result['decision'] == 'answered')
            count['abstained'] += int(result['decision'] != 'answered')
            count['missing_public_examples'] += int(result.get('reason') == 'query_has_no_public_examples')
            count['independently_correct'] += int(bool(score and score.passed))
            count['wrong_accepted_answer'] += int(bool(score and not score.passed))
            count['answer_without_independent_evidence'] += int(bool(result['code'] and not score))
            matched = (result.get('match') or {}).get('key')
            count['wrong_retrieval_match'] += int(matched is not None and matched != spec['target'])
            times[kind].append(result['seconds'])
            if result['decision'] == 'answered':
                answered_times[kind].append(result['seconds'])
            stream.write(json.dumps({'qid':spec['qid'], 'kind':kind, 'target':spec['target'], 'result':result,
                                     'independent':score.to_dict() if score else None})+'\n'); stream.flush()
            print(f'[answer] {i+1}/{len(manifest["recognition"])} {spec["qid"]} {result["decision"]}', flush=True)
    summary = {'contract_sha256':sha(directory/'contract.json'), 'answers_sha256':sha(directory/'answers.jsonl'),
               'embedding_load_seconds':load_seconds, 'by_kind': {kind:{**dict(count),
                    'p50_seconds':float(np.percentile(times[kind],50)),
                    'p95_seconds':float(np.percentile(times[kind],95)),
                    'answered_p50_seconds':float(np.percentile(answered_times[kind],50)) if answered_times[kind] else None,
                    'answered_p95_seconds':float(np.percentile(answered_times[kind],95)) if answered_times[kind] else None}
                    for kind,count in groups.items()},
               'limits': ['Known-problem service evaluation, not unfamiliar composition.',
                          'Paraphrases retain original signatures and use original public examples.',
                          'Absent cases exclude known source families; natural absence is unmeasured.',
                          'Latency includes warm embedding/retrieval/assembly/public checks; cold loading and independent scoring are separate.',
                          'Finite independent tests do not prove general correctness.']}
    (directory/'summary.json').write_text(json.dumps(summary, indent=2)+'\n')
    print(json.dumps(summary, indent=2))


if __name__ == '__main__':
    main()
