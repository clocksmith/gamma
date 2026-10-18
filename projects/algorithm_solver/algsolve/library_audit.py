"""Inventory the complete library; execute eligible exact queries via answer().

Independent tests score the original question, never the retrieved identity.
Protected composition aliases are excluded before any code or test execution.
The existing production index and historical validation cache are not modified.
"""
from __future__ import annotations

import argparse
from collections import Counter
from dataclasses import replace
import hashlib
import json
import os
from pathlib import Path
import platform
import time

from . import corpus, validate
from .answer import answer
from .lookup import LookupIndex, load_thresholds
from .public_examples import recover
from .recognition_boundary import exclusion_closure
from .records import DERIVED, LANE_ROOT, Problem, load_hidden_tests
from .routes import Budget, Context
from .splits import IndexEntry, sibling_base


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def rows(path):
    with Path(path).open() as stream:
        return [json.loads(line) for line in stream if line.strip()]


def write(path, value):
    Path(path).write_text(json.dumps(value, indent=2, allow_nan=False) + '\n')


def inputs():
    raw = rows(corpus.ENTRIES_PATH)
    problems = rows(DERIVED / 'problems.jsonl')
    reservation = json.loads((LANE_ROOT / 'contracts/typed_confirmation_v1.json').read_text())
    boundary = exclusion_closure(raw, [{'uid': p['uid'], 'slug': p['slug']} for p in problems],
                                 reservation, json.loads((DERIVED / 'near_duplicates.json').read_text()))
    blocked = set(boundary['keys'])
    excluded_uids = set(boundary['uids'])
    eligible = [IndexEntry(**r) for r in raw if r['key'] not in blocked]
    # Do not construct, recover examples, or load tests for reserved records.
    allowed_uids = {uid for e in eligible for uid in e.members}
    allowed = {p['uid']: Problem.from_dict(p) for p in problems
               if p['uid'] in allowed_uids and p['uid'] not in excluded_uids}
    return raw, eligible, allowed, boundary


def original_for(entry, problems):
    """Use only a matching interface; missing evidence never becomes a pass."""
    members = [problems[u] for u in entry.members if u in problems]
    compatible = [p for p in members if p.entry == entry.entry and p.params == entry.params]
    independent = [p for p in compatible if p.evidence_ceiling == 'independent_tests_passed'
                   and p.hidden_tests_path and 'unusable' not in p.import_notes]
    independent.sort(key=lambda p: (p.uid != entry.judge_uid, p.uid))
    primary = next((p for p in compatible if p.uid == entry.judge_uid), None)
    primary = primary or next(iter(compatible), None)
    return primary, independent


def exact_query(entry, original):
    if original is None:
        original = Problem(uid='inventory:' + entry.key, source='corpus', source_id=entry.key,
                           title=entry.title, slug=entry.slug, statement=entry.statement,
                           io_mode='functional', entry=entry.entry, params=entry.params)
    # Preserve the indexed statement and starter exactly. Only imported public
    # examples with the same interface are attached, never independent tests.
    return recover(replace(original, statement=entry.statement, starter_code=entry.starter_code,
                           hidden_tests_path='', reference_solutions=[], import_notes={}))


def inventory_entry(entry, problems, cache):
    primary, independent = original_for(entry, problems)
    query = exact_query(entry, primary)
    errors, test_sets = [], []
    for source in independent:
        try:
            tests = load_hidden_tests(source)
            test_sets.append({'uid': source.uid, 'tests': len(tests), 'sha256': digest(tests),
                              'path': source.hidden_tests_path})
        except (OSError, ValueError, TypeError, KeyError) as exc:
            errors.append({'uid': source.uid, 'error': type(exc).__name__, 'detail': str(exc)})
    states = [cache.get(uid, {}) for uid in entry.members]
    unusable = {u: problems[u].import_notes['unusable'] for u in entry.members
                if u in problems and 'unusable' in problems[u].import_notes}
    coverage = ('available' if any(t['tests'] for t in test_sets) else
                'test_artifact_error' if errors else 'incompatible_interface' if primary is None else
                'unusable_imported_evidence' if unusable else 'missing_independent_tests')
    return {'key': entry.key, 'family': sibling_base(entry.slug),
            'difficulty': entry.difficulty, 'tags': entry.tags, 'members': entry.members,
            'identity_valid': entry.key == 'lc:' + entry.slug and bool(entry.title and entry.members),
            'provenance_present': bool(entry.license and entry.attribution) and all(
                r.get('uid') in entry.members and r.get('source') and r.get('code') for r in entry.references),
            'references': [{k: r.get(k) for k in ('uid', 'source', 'validated')} |
                           {'code_sha256': hashlib.sha256(r['code'].encode()).hexdigest()} for r in entry.references],
            'interface_compatible': primary is not None, 'public_examples': len(query.public_tests) if query else 0,
            'historical_verified': bool(entry.judge_uid), 'independent_coverage': coverage,
            'independent_test_sets': test_sets, 'test_errors': errors,
            'historical_failure_reasons': [r.get('reason') for r in states if r and not r.get('eligible')],
            'unusable_members': unusable}


def freeze(directory):
    raw, eligible, problems, boundary = inputs()
    if len({r['key'] for r in raw}) != len(raw):
        raise ValueError('Duplicate library identities')
    cache = validate.load_cache()
    by_key = {e.key: e for e in eligible}
    inventory = []
    for r in raw:
        if r['key'] not in by_key:
            inventory.append({'key': r['key'], 'excluded': 'protected_composition_alias',
                              'historical_verified': bool(r['judge_uid'])})
        else:
            inventory.append(inventory_entry(by_key[r['key']], problems, cache))
    files = [corpus.ENTRIES_PATH, corpus.EMBEDDINGS_PATH, corpus.KEYS_PATH,
             DERIVED / 'problems.jsonl', DERIVED / 'reference_validation.jsonl', DERIVED / 'near_duplicates.json',
             LANE_ROOT / 'contracts/typed_confirmation_v1.json', LANE_ROOT / 'contracts/run_contract.json',
             LANE_ROOT / 'contracts/lookup_thresholds.json', LANE_ROOT / 'contracts/recognition_qualification_v1.json']
    source = sorted((LANE_ROOT / 'algsolve').rglob('*.py'))
    # Scoring-only test identity is separately sealed without exporting payloads.
    contract = {'schema': 'algsolve.library-audit.v1', 'inventory_entries': len(raw),
                'executable_entries': len(eligible), 'excluded_entries': len(raw)-len(eligible),
                'historical_gaps': sum(not r['judge_uid'] for r in raw),
                'inputs_sha256': {str(p.relative_to(LANE_ROOT)): sha(p) for p in files},
                'source_sha256': {str(p.relative_to(LANE_ROOT)): sha(p) for p in source},
                'inventory_sha256': digest(inventory), 'boundary_sha256': digest(boundary),
                'device': 'cpu', 'torch_threads': 4, 'generation': False, 'reranker': False,
                'answer_path': 'algsolve.answer.answer, original indexed query, unchanged acceptance thresholds',
                'independent_wall_seconds': 30, 'test_policy': 'all available compatible independent sets; empty never passes',
                'scope': 'development library qualification; fresh independent recognition evaluation remains sealed'}
    directory.mkdir(parents=True, exist_ok=False)
    write(directory / 'contract.json', contract)
    write(directory / 'exclusions.json', boundary)
    with (directory / 'inventory.jsonl').open('x') as stream:
        for row in inventory:
            stream.write(json.dumps(row) + '\n')
    summarize(directory)
    return contract


def check_seal(directory, contract, boundary):
    for section in ('inputs_sha256', 'source_sha256'):
        for relative, expected in contract[section].items():
            if sha(LANE_ROOT / relative) != expected:
                raise ValueError(f'Frozen input changed: {relative}')
    if digest(boundary) != contract['boundary_sha256']:
        raise ValueError('Exclusion boundary changed')
    if digest(rows(directory / 'inventory.jsonl')) != contract['inventory_sha256']:
        raise ValueError('Inventory changed')


def independent_score(entry, code, problems, inventory):
    if not code:
        return {'status': 'no_code', 'verdicts': []}
    if inventory['independent_coverage'] != 'available':
        return {'status': inventory['independent_coverage'], 'verdicts': []}
    _, sources = original_for(entry, problems)
    verdicts = []
    expected = {s['uid']: s for s in inventory['independent_test_sets']}
    for source in sources:
        if source.uid not in expected:
            continue
        tests = load_hidden_tests(source)
        if digest(tests) != expected[source.uid]['sha256']:
            raise ValueError('Independent tests changed after seal')
        if tests:
            verdicts.append({'uid': source.uid, **validate.judge_problem(source, code, tests, wall_seconds=30).to_dict()})
    status = ('passed' if all(v['passed'] for v in verdicts) else 'failed') if verdicts else 'missing_tests'
    if any(v.get('reason') == 'sandbox_error' for v in verdicts):
        status = 'infrastructure_error'
    return {'status': status, 'verdicts': verdicts}


def audit_one(entry, context, problems, inventory):
    primary, _ = original_for(entry, problems)
    query = exact_query(entry, primary)
    result = answer(context, query)
    # Timing of independent qualification is NOT included in product latency.
    start = time.perf_counter()
    reference = next((r for r in entry.references if r.get('validated')), None) or next(iter(entry.references), None)
    stored_code = reference['code'] if reference else None
    stored = independent_score(entry, stored_code, problems, inventory)
    returned = (stored if result.get('code') == stored_code and stored_code else
                independent_score(entry, result.get('code'), problems, inventory))
    key = (result.get('match') or {}).get('key')
    accepted = result['decision'] == 'answered'
    candidates = (result.get('match') or {}).get('candidates', [])
    row = {'key': entry.key, 'family': inventory['family'], 'difficulty': entry.difficulty,
           'kind': 'exact_indexed_statement', 'historical_gap': not inventory['historical_verified'],
           'accepted': accepted, 'identity_correct': key == entry.key,
           'accepted_and_correct': accepted and key == entry.key and returned['status'] == 'passed',
           'wrong_acceptance': accepted and (key != entry.key or returned['status'] == 'failed'),
           'accepted_unqualified': accepted and key == entry.key and returned['status'] not in ('passed', 'failed'),
           'top_five': entry.key in [c['key'] for c in candidates[:5]],
           'retrieval_executed': bool(candidates), 'questions': 0, 'result': result,
           'stored_solution': stored, 'returned_solution': returned,
           'independent_scoring_seconds': time.perf_counter()-start}
    # Preserve source provenance and output hash without republishing stored code.
    row['result'] = dict(result)
    row['result']['code_sha256'] = hashlib.sha256(result['code'].encode()).hexdigest() if result.get('code') else None
    row['result'].pop('code', None)
    return row


def execute(directory):
    start = time.perf_counter()
    import numpy as np
    import torch
    from .embed import Embedder, EXPECTED_SHA256
    contract = json.loads((directory / 'contract.json').read_text())
    raw, entries, problems, boundary = inputs()
    check_seal(directory, contract, boundary)
    keys = json.loads(corpus.KEYS_PATH.read_text())
    if keys != [r['key'] for r in raw]:
        raise ValueError('Embedding identity order differs')
    torch.set_num_threads(4)
    x = torch.ones((2, 2), device='cpu')
    if not torch.equal(x @ x, torch.full((2, 2), 2.)):
        raise ValueError('CPU compute probe failed')
    indices = [i for i, key in enumerate(keys) if key not in set(boundary['keys'])]
    lookup = LookupIndex(entries, np.load(corpus.EMBEDDINGS_PATH)[indices])
    loading = time.perf_counter()
    embedder = Embedder(device='cpu')
    context = Context(generator=None, embedder=embedder, lookup=lookup, thresholds=load_thresholds(),
                      classifier=None, entries=entries,
                      budget=Budget.from_contract(json.loads((LANE_ROOT/'contracts/run_contract.json').read_text())))
    runtime = {'platform': platform.platform(), 'python': platform.python_version(), 'torch': torch.__version__,
               'device': 'cpu', 'threads': 4, 'compute_probe': 'passed', 'embedding_sha256': EXPECTED_SHA256,
               'embedding_load_seconds': time.perf_counter()-loading,
               'startup_seconds': time.perf_counter()-start, 'os_caches_flushed': False}
    # Linux /proc includes interpreter/module imports before execute() entered.
    # Clock ticks since boot and CLOCK_BOOTTIME share the same origin.
    stat_fields = Path('/proc/self/stat').read_text().rsplit(')', 1)[1].split()
    runtime['cold_process_to_ready_seconds'] = (time.clock_gettime(time.CLOCK_BOOTTIME)
                                               - int(stat_fields[19]) / os.sysconf('SC_CLK_TCK'))
    runtime['cold_scope'] = 'fresh Python process through model ready; OS/file caches not flushed'
    runs = directory / 'openings.jsonl'
    with runs.open('a') as stream:
        stream.write(json.dumps(runtime) + '\n')
    inventory = {r['key']: r for r in rows(directory / 'inventory.jsonl')}
    output = directory / 'answers.jsonl'
    previous = rows(output) if output.exists() else []
    done = {r['key'] for r in previous}
    if len(done) != len(previous) or not done <= {e.key for e in entries}:
        raise ValueError('Invalid prior results')
    print(f'[run-contract] run_name={directory.name} pairs_input_spec=eligible-corpus resume_from={len(done)} '
          'resume_stage=exact-answer decode=none eval_dataset_paths=library-qualification device=cpu '
          'schedule=serial runtime_mode=cpu+linux-sandbox sweep_mode=after_train', flush=True)
    with output.open('a') as stream:
        for entry in entries:
            if entry.key in done:
                continue
            row = audit_one(entry, context, problems, inventory[entry.key])
            stream.write(json.dumps(row, allow_nan=False) + '\n')
            stream.flush()
            done.add(entry.key)
            print(f'[audit] {len(done)}/{len(entries)} {entry.key} {row["result"]["decision"]} '
                  f'stored={row["stored_solution"]["status"]}', flush=True)
            if len(done) % 100 == 0:
                summarize(directory)
    summarize(directory)


def summarize(directory):
    from .recognition_metrics import summarize_results
    inventory = rows(directory / 'inventory.jsonl')
    results = rows(directory / 'answers.jsonl') if (directory / 'answers.jsonl').exists() else []
    eligible = [r for r in inventory if not r.get('excluded')]
    gaps = [r for r in eligible if not r['historical_verified']]
    summary = {'inventory_entries': len(inventory), 'eligible_entries': len(eligible),
               'excluded_entries': len(inventory)-len(eligible), 'executed': len(results),
               'complete': len(results) == len(eligible),
               'historical_gaps_total': sum(not r['historical_verified'] for r in inventory),
               'historical_gaps_eligible': len(gaps),
               'gap_coverage': dict(Counter(r['independent_coverage'] for r in gaps)),
               'gap_interface_incompatible': sum(not r['interface_compatible'] for r in gaps),
               'gap_unusable_members': sum(bool(r['unusable_members']) for r in gaps),
               'gap_execution_status': dict(Counter(r['stored_solution']['status'] for r in results if r['historical_gap'])),
               'inventory_defects': {key: sum(not r[key] for r in eligible) for key in
                                     ('identity_valid', 'provenance_present', 'interface_compatible')},
               'metrics': summarize_results(results),
               'limits': ['Metadata inventory includes all entries; reserved aliases are not executed.',
                          'Missing independent tests are evidence gaps, not failed solutions.',
                          'Wrong identity and test failures are separate; public passes alone are not accepted-and-correct.',
                          'Available finite tests are not a correctness proof; old cache flags are historical only.',
                          'Top-five denominator includes pre-retrieval abstentions; conditional retrieval also reported.']}
    write(directory / 'summary.json', summary)
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('freeze', 'execute', 'summary'))
    parser.add_argument('--name', required=True)
    args = parser.parse_args()
    if not args.name.replace('-', '').replace('_', '').isalnum():
        raise ValueError('Invalid run name')
    directory = LANE_ROOT / 'runs' / args.name
    result = {'freeze': freeze, 'execute': execute, 'summary': summarize}[args.action](directory)
    if args.action != 'execute':
        print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
