"""Bounded, user-assisted requirement clarification over a retrieved shortlist.

No automatic semantic acceptance, generation, hidden-test access or source
insertion. Requirement records are curated; unknown candidates stay visible.
Only explicit confirmation of the full stored statement accepts an identity.
"""
from __future__ import annotations

import argparse
from collections import Counter
import copy
import hashlib
import json
from pathlib import Path
import secrets
import time

from .records import LANE_ROOT

PROFILES = LANE_ROOT / 'contracts/clarification_profiles_v1.json'


def load_profiles(path=PROFILES):
    catalog = json.loads(Path(path).read_text())
    if catalog.get('schema_version') != 1 or not catalog.get('authority'):
        raise ValueError('Invalid requirement catalog')
    facets, profiles = catalog['facets'], catalog['profiles']
    seen = set()
    for profile in profiles:
        key = profile['key']
        if key in seen or not key.startswith('lc:'):
            raise ValueError('Invalid or duplicate requirement identity')
        seen.add(key)
        if not profile.get('title') or not profile.get('contract') or len(profile.get('statement_sha256', '')) != 64:
            raise ValueError('Missing statement provenance or contract')
        if 'family' not in profile['facts']:
            raise ValueError('Every requirement record needs a family')
        for facet, value in profile['facts'].items():
            if facet not in facets or value not in facets[facet]['values']:
                raise ValueError('Undeclared requirement value')
    return catalog


class ClarificationSession:
    def __init__(self, query, candidates, catalog, *, max_questions=6, max_candidates=12):
        if not isinstance(query, str) or not query.strip() or len(query) > 60000:
            raise ValueError('A bounded nonempty description is required')
        if not 1 <= max_questions <= 12 or not 1 <= max_candidates <= 32:
            raise ValueError('Invalid interaction budget')
        self.query = query
        self.catalog = copy.deepcopy(catalog)
        self.profiles = {p['key']: p for p in self.catalog['profiles']}
        self.started = time.perf_counter()
        self.max_questions = max_questions
        self.questions = 0
        self.history = []
        self.pending = None
        self.terminal = None
        self.session_id = secrets.token_hex(12)
        self.revision = 0
        initial = list(dict.fromkeys(c['key'] for c in candidates[:5]))
        self.unknown = [key for key in initial if key not in self.profiles]
        seeds = [key for key in initial if key in self.profiles]
        families = {self.profiles[key]['facts']['family'] for key in seeds}
        # Explicit curated sibling expansion, never a hidden reranker or code path.
        expanded = seeds + [key for key, p in self.profiles.items()
                            if key not in seeds and p['facts']['family'] in families]
        self.active = expanded[:max_candidates]
        self.omitted = expanded[max_candidates:]
        self.initial = initial
        self.expanded = [key for key in self.active if key not in initial]

    def _finish(self, decision, reason, key=None):
        self.pending = None
        self.terminal = {'decision': decision, 'key': key, 'reason': reason,
                         'selection_basis': 'user_confirmed_statement' if key else None,
                         'questions': self.questions, 'interactions': len(self.history),
                         'unprofiled_candidates': self.unknown, 'omitted_candidates': self.omitted,
                         'code': None, 'example_passed': None}
        return copy.deepcopy(self.terminal)

    def next_step(self):
        if self.terminal:
            return copy.deepcopy(self.terminal)
        if self.pending:
            return copy.deepcopy(self.pending)
        if not self.active:
            return self._finish('abstain', 'no_supported_contract_remaining')
        common = set.intersection(*(set(self.profiles[k]['facts']) for k in self.active))
        varying = [facet for facet in self.catalog['facets'] if facet in common and
                   len({self.profiles[k]['facts'][facet] for k in self.active}) > 1]
        prompt_id = f'{self.session_id}:{self.revision}'
        if varying:
            if self.questions >= self.max_questions:
                return self._finish('abstain', 'question_budget_exhausted')
            # Minimize the largest remaining group; fixed catalog order breaks ties.
            facet = min(varying, key=lambda f: max(Counter(self.profiles[k]['facts'][f] for k in self.active).values()))
            definition = self.catalog['facets'][facet]
            values = {self.profiles[key]['facts'][facet] for key in self.active}
            options = [{'value': v, 'label': label} for v, label in definition['values'].items() if v in values]
            self.pending = {'decision': 'clarify', 'question_id': prompt_id, 'facet': facet,
                            'question': definition['question'], 'options': options,
                            'contrasts': [{'key': k, 'title': self.profiles[k]['title'],
                                           'value': self.profiles[k]['facts'][facet]} for k in self.active]}
        elif len(self.active) == 1:
            profile = self.profiles[self.active[0]]
            self.pending = {'decision': 'confirm', 'question_id': prompt_id,
                            'question': 'Does the full problem statement match your request, including input restrictions, allowed operations and output? Choose no if any requirement differs.',
                            'candidate': copy.deepcopy(profile),
                            'options': [{'value': 'yes', 'label': 'Yes, I reviewed the full statement and it matches'},
                                        {'value': 'no', 'label': 'No, a requirement differs'}]}
        else:
            return self._finish('abstain', 'contracts_do_not_distinguish_candidates')
        self.pending['options'] += [{'value': 'other', 'label': 'Another requirement or an unresolved candidate'},
                                    {'value': 'unsure', 'label': 'I do not know yet'}]
        self.pending['unprofiled_candidates'] = self.unknown[:]
        self.pending['omitted_candidates'] = self.omitted[:]
        return copy.deepcopy(self.pending)

    def answer(self, question_id, value, *, reviewed_statement_sha256=None):
        if not self.pending or self.pending['question_id'] != question_id:
            raise ValueError('Stale or unrelated clarification response')
        if value not in {option['value'] for option in self.pending['options']}:
            raise ValueError('Reply must select a displayed option')
        prompt = self.pending
        if prompt['decision'] == 'confirm' and value == 'yes':
            if reviewed_statement_sha256 != prompt['candidate']['statement_sha256']:
                raise ValueError('Confirmation must bind to the reviewed statement')
        self.history.append({'prompt': copy.deepcopy(prompt), 'answer': value})
        self.revision += 1
        self.pending = None
        if prompt['decision'] == 'clarify':
            self.questions += 1
        if value in ('other', 'unsure', 'no'):
            return self._finish('abstain', {'other': 'requirement_outside_options', 'unsure': 'requirements_unresolved', 'no': 'statement_rejected'}[value])
        if prompt['decision'] == 'confirm':
            return self._finish('match', 'explicit_statement_confirmation', prompt['candidate']['key'])
        self.active = [key for key in self.active if self.profiles[key]['facts'][prompt['facet']] == value]
        return self.next_step()

    def cancel(self):
        if self.terminal:
            return copy.deepcopy(self.terminal)
        return self._finish('abstain', 'cancelled')


def load_runtime(device, catalog):
    import numpy as np
    import torch
    from . import corpus
    from .embed import Embedder
    from .lookup import LookupIndex

    torch.set_num_threads(4)
    print(f'cuda_available={torch.cuda.is_available()} device_count={torch.cuda.device_count()} target_device={device}', flush=True)
    probe = torch.ones((2, 2), device=device)
    if not torch.equal((probe @ probe).cpu(), torch.full((2, 2), 2.)):
        raise RuntimeError('Device compute probe failed')
    entries = corpus.read_entries()
    keys = [e.key for e in entries]
    if len(keys) != len(set(keys)) or json.loads(corpus.KEYS_PATH.read_text()) != keys:
        raise ValueError('Corpus key order differs')
    by_key = {e.key: e for e in entries}
    for profile in catalog['profiles']:
        entry = by_key.get(profile['key'])
        if entry is None or hashlib.sha256(entry.statement.encode()).hexdigest() != profile['statement_sha256']:
            raise ValueError(f'Requirement source changed: {profile["key"]}')
    vectors = np.load(corpus.EMBEDDINGS_PATH)
    if vectors.ndim != 2 or len(vectors) != len(keys) or not np.isfinite(vectors).all():
        raise ValueError('Invalid corpus vectors')
    index = LookupIndex(entries, vectors)
    started = time.perf_counter()
    embedder = Embedder(device=device)
    load_seconds = time.perf_counter() - started

    def retrieve(query):
        return index.scored_candidates(query, embedder.encode([query], query=True)[0])[:5]

    return retrieve, by_key, load_seconds


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('query')
    parser.add_argument('--device', choices=('cpu', 'cuda'), default='cpu')
    parser.add_argument('--receipt', type=Path, help='New local receipt file; never overwritten')
    args = parser.parse_args()
    if args.receipt and args.receipt.exists():
        parser.error('Receipt already exists')
    catalog = load_profiles()
    print(f'[run-contract] run_name=interactive-clarification pairs_input_spec=user-query resume_from=none resume_stage=none decode=none eval_dataset_paths=none device={args.device} schedule=serial runtime_mode={args.device} sweep_mode=live')
    retrieve, entries, load_seconds = load_runtime(args.device, catalog)
    started = time.perf_counter()
    candidates = retrieve(args.query)
    retrieval_seconds = time.perf_counter() - started
    session = ClarificationSession(args.query, candidates, catalog)
    try:
        step = session.next_step()
        while step['decision'] in ('clarify', 'confirm'):
            print('\n' + step['question'])
            if step['decision'] == 'confirm':
                entry = entries[step['candidate']['key']]
                print(entry.title + '\n' + entry.statement)
                print('Source: ' + '; '.join(entry.attribution))
                print('License: ' + '; '.join(entry.license))
            else:
                for item in step['contrasts']:
                    label = catalog['facets'][step['facet']]['values'][item['value']]
                    print(f'  {item["title"]}: {label}')
            unresolved = step['unprofiled_candidates'] + step['omitted_candidates']
            if unresolved:
                print('Other candidates remain unresolved: ' + ', '.join(entries[key].title for key in unresolved))
            for index, option in enumerate(step['options'], 1):
                print(f'{index}. {option["label"]}')
            raw = input('Choose a number (or q to stop): ').strip()
            if raw.lower() == 'q':
                step = session.cancel()
                break
            if not raw.isdigit() or not 1 <= int(raw) <= len(step['options']):
                print('Select one of the displayed numbers.')
                continue
            option = step['options'][int(raw) - 1]['value']
            statement_sha = step.get('candidate', {}).get('statement_sha256')
            step = session.answer(step['question_id'], option, reviewed_statement_sha256=statement_sha)
    except (EOFError, KeyboardInterrupt):
        step = session.cancel()
    receipt = {'result': step, 'query': args.query, 'retrieval': candidates,
               'profiles_sha256': hashlib.sha256(PROFILES.read_bytes()).hexdigest(),
               'sibling_expansion': session.expanded, 'history': session.history,
               'embedding_load_seconds': load_seconds, 'retrieval_seconds': retrieval_seconds,
               'journey_seconds_including_user_wait': time.perf_counter() - started}
    print(json.dumps(receipt['result'], indent=2))
    if args.receipt:
        with args.receipt.open('x') as output:
            output.write(json.dumps(receipt, indent=2) + '\n')


if __name__ == '__main__':
    main()
