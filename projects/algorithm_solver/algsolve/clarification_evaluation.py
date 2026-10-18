"""Scripted development journeys for assisted selection, not human qualification."""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import json
from pathlib import Path
import re
import time

from .clarify import ClarificationSession, PROFILES, load_profiles, load_runtime
from .natural_description import load_dataset, percentile, sha
from .records import LANE_ROOT

DIALOGUES = LANE_ROOT / 'contracts/clarification_dialogues_dev_v1.json'


def drive(session, answers, confirmation):
    """Only explicit scripted replies cross this boundary; no target identities."""
    step = session.next_step()
    while step['decision'] in ('clarify', 'confirm'):
        requested = answers.get(step['facet'], 'unsure') if step['decision'] == 'clarify' else confirmation
        allowed = {option['value'] for option in step['options']}
        reply = requested if requested in allowed else 'other'
        step = session.answer(step['question_id'], reply,
                              reviewed_statement_sha256=step.get('candidate', {}).get('statement_sha256'))
    return step


def load_dialogues(path=DIALOGUES):
    document = json.loads(Path(path).read_text())
    if document.get('partition') != 'development' or document.get('schema_version') != 1:
        raise ValueError('Only development dialogues are admitted')
    if Path(document['base_dataset']).name != document['base_dataset']:
        raise ValueError('Base dataset must be a sibling file')
    base = load_dataset(Path(path).parent / document['base_dataset'])
    by_id = {row['id']: row for row in base['cases']}
    cases, seen = [], set()
    for spec in document['cases']:
        if spec['id'] in seen:
            raise ValueError('Duplicate dialogue identity')
        seen.add(spec['id'])
        if not isinstance(spec.get('answers'), dict) or spec.get('confirmation') not in ('yes', 'no', 'unsure'):
            raise ValueError('Every dialogue needs explicit answers and confirmation')
        if any(not isinstance(k, str) or not isinstance(v, str) for k, v in spec['answers'].items()):
            raise ValueError('Requirement replies must be string choices')
        if 'expected_key' not in spec or (spec['expected_key'] is not None and not spec['expected_key'].startswith('lc:')):
            raise ValueError('Missing scoring identity')
        case = {**by_id.get(spec['id'], {}), **spec}
        if not isinstance(case.get('query'), str) or not case['query'].strip() or not case.get('kind'):
            raise ValueError('Missing query or category')
        cases.append(case)
    if not cases:
        raise ValueError('Empty dialogue dataset')
    return document, cases


def summarize(rows):
    groups = defaultdict(list)
    for row in rows:
        groups[row['kind']].append(row)

    def counts(items):
        result = Counter()
        for row in items:
            key = row['result']['key']
            result['journeys'] += 1
            result['intended_matches'] += row['expected_key'] is not None
            result['correct_selected_identity'] += key is not None and key == row['expected_key']
            result['wrong_acceptances'] += key is not None and key != row['expected_key']
            result['abstained'] += row['result']['decision'] == 'abstain'
            result['clarification_questions'] += row['result']['questions']
            result['confirmations'] += sum(h['prompt']['decision'] == 'confirm' for h in row['history'])
        return {**dict(result),
                'questions_p50': percentile([r['result']['questions'] for r in items], .5),
                'questions_max': max(r['result']['questions'] for r in items),
                'machine_journey_p50_seconds': percentile([r['machine_seconds'] for r in items], .5),
                'machine_journey_p95_seconds': percentile([r['machine_seconds'] for r in items], .95),
                'dialogue_only_p50_seconds': percentile([r['dialogue_seconds'] for r in items], .5)}

    if not rows:
        raise ValueError('Empty journey report')
    return {'overall': counts(rows), 'by_kind': {kind: counts(items) for kind, items in groups.items()},
            'genuine_absent_algorithm_cases': 0, 'human_journey_time': None}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--name', required=True)
    parser.add_argument('--device', choices=('cpu', 'cuda'), default='cpu')
    args = parser.parse_args()
    if not re.fullmatch('[A-Za-z0-9_-]+', args.name):
        parser.error('Invalid run name')
    directory = LANE_ROOT / 'runs' / args.name
    if directory.exists():
        raise ValueError('Use a new run name')
    catalog = load_profiles()
    document, cases = load_dialogues()
    print(f'[run-contract] run_name={args.name} pairs_input_spec={DIALOGUES} resume_from=none '
          f'resume_stage=none decode=none eval_dataset_paths=development-dialogues device={args.device} '
          f'schedule=serial runtime_mode={args.device} sweep_mode=after_train', flush=True)
    retrieve, entries, load_seconds = load_runtime(args.device, catalog)
    if any(c['expected_key'] and c['expected_key'] not in entries for c in cases):
        raise ValueError('A scoring identity is absent from the fixed corpus')
    from . import corpus
    from .embed import EXPECTED_SHA256
    import torch
    contract = {
        'partition': 'development', 'journeys': len(cases), 'profile_count': len(catalog['profiles']),
        'dataset_sha256': sha(DIALOGUES), 'base_dataset_sha256': sha(DIALOGUES.parent / document['base_dataset']),
        'profiles_sha256': sha(PROFILES), 'authorship': document['authorship'],
        'source_sha256': {name: sha(LANE_ROOT / 'algsolve' / name) for name in
                          ('clarify.py', 'clarification_evaluation.py', 'natural_description.py', 'lookup.py', 'embed.py', 'corpus.py', 'splits.py', 'records.py')},
        'index_sha256': {p.name: sha(p) for p in (corpus.ENTRIES_PATH, corpus.KEYS_PATH, corpus.EMBEDDINGS_PATH)},
        'embedding_weights': EXPECTED_SHA256, 'embedding_device': args.device,
        'torch': torch.__version__, 'threads': 4, 'top_k': 5, 'max_candidates': 12,
        'max_questions': 6, 'additional_confirmation_required': True,
        'generation': False, 'automatic_identity_acceptance': False,
        'query_understanding': 'retrieval only; no automatic extraction of requirements from initial prose',
        'limits': document['limits'],
    }
    directory.mkdir(parents=True, exist_ok=False)
    (directory / 'contract.json').write_text(json.dumps(contract, indent=2) + '\n')
    rows = []
    with (directory / 'journeys.jsonl').open('x') as stream:
        for case in cases:
            started = time.perf_counter()
            candidates = retrieve(case['query'])
            retrieval_seconds = time.perf_counter() - started
            dialogue_start = time.perf_counter()
            session = ClarificationSession(case['query'], candidates, catalog)
            result = drive(session, case['answers'], case['confirmation'])
            dialogue_seconds = time.perf_counter() - dialogue_start
            machine_seconds = time.perf_counter() - started
            row = {'id': case['id'], 'kind': case['kind'], 'expected_key': case['expected_key'],
                   'result': result, 'history': session.history, 'candidates': candidates,
                   'sibling_expansion': session.expanded, 'retrieval_seconds': retrieval_seconds,
                   'dialogue_seconds': dialogue_seconds, 'machine_seconds': machine_seconds}
            rows.append(row)
            stream.write(json.dumps(row, allow_nan=False) + '\n')
            stream.flush()
            print(f'[journey] {len(rows)}/{len(cases)} {row["id"]}: {result["decision"]} {result["key"]}', flush=True)
    summary = {'complete': len(rows) == len(cases), 'contract_sha256': sha(directory / 'contract.json'),
               'journeys_sha256': sha(directory / 'journeys.jsonl'), 'embedding_load_seconds': load_seconds,
               **summarize(rows), 'limits': document['limits'],
               'latency_scope': 'live retrieval plus deterministic scripted dialogue; human reading/response time unmeasured'}
    (directory / 'summary.json').write_text(json.dumps(summary, indent=2) + '\n')
    print(json.dumps(summary, indent=2))


if __name__ == '__main__':
    main()
