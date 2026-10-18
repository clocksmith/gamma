"""Example-gated retrieval for editor consumers; separate from frozen comparisons.

No downloads, hidden-test reads or automatic provider selection. A caller may
inject a calibrated reranker and an explicitly enabled generator. A passing
stored reference is evidence about its original problem, not the new query.
"""
from __future__ import annotations

import argparse
import copy
from dataclasses import replace
import json
import math
from pathlib import Path
import sys
import time

from . import validate
from .judge import judge
from .lookup import MatchResult, adapt_solution, decide, fingerprint
from .records import LANE_ROOT, Problem
from .public_examples import recover
from .routes import Budget, Context, RouteResult, run_generative


def check_stored(query, entry, wall_seconds):
    """Shared public-example boundary after automatic or explicit selection."""
    if not query.public_tests:
        raise ValueError('Query public examples are required')
    if wall_seconds <= 0:
        raise ValueError('Public checking requires remaining request budget')
    reference = next((r for r in entry.references if r.get('validated')), None)
    reference = reference or next(iter(entry.references), None)
    if reference is None:
        return None, None
    if not query.entry.get('method'):
        # A statement-only request provides positional public examples. Binding
        # comes from the selected source, never from an evaluator's target label.
        query = replace(query, entry=entry.entry, params=entry.params)
    try:
        code = adapt_solution(reference['code'], entry, fingerprint(query.query_text()).method or None)
    except ValueError as error:
        return None, judge.Verdict(False,judge.LOAD_ERROR,len(query.public_tests),0,0.,
                                   {'detail':str(error),'stage':'interface_adaptation'})
    verdict = validate.judge_problem(query, code, query.public_tests, wall_seconds=wall_seconds)
    return code if verdict.passed else None, verdict


def answer(context: Context, query: Problem, *, reranker=None, rerank_thresholds=None,
           allow_generation: bool = False, approved_library=None) -> dict:
    if approved_library is not None and allow_generation:
        raise ValueError('Approved-library lookup does not permit generated fallback')
    started = time.perf_counter()
    # Only query inputs and public examples cross the route boundary.
    query = replace(query, hidden_tests_path='', reference_solutions=[], import_notes={})
    query = recover(query)
    result = {'decision': 'abstain', 'code': None, 'source': None,
              'example_passed': False, 'independent_tests_passed': None,
              'public_example_count': len(query.public_tests),
              'dataset_label': 'prior model exposure unknown', 'attempts': []}

    def finish(reason=None):
        if reason:
            result['reason'] = reason
        result['seconds'] = time.perf_counter() - started
        return result

    if not query.public_tests:
        return finish('query_has_no_public_examples')
    exact = context.lookup.exact_problem_key(query) or context.lookup.exact_key(query.query_text())
    if exact is not None:
        candidates = [{'key': exact, 'score': 1., 'exact': True}]
    else:
        # Qualified recognition ignores method-name hints; a renamed caller
        # interface must not change which problem the statement describes.
        retrieval_text = query.statement if approved_library is not None else query.query_text()
        vector = context.embedder.encode([retrieval_text], query=True)[0]
        candidates = context.lookup.scored_candidates(retrieval_text, vector)
    if not candidates:
        return finish('empty_index')
    thresholds = (context.statement_thresholds if approved_library is not None
                  and hasattr(context, 'statement_thresholds') else context.thresholds)
    if reranker is not None and exact is None:
        if rerank_thresholds is None:
            raise ValueError('Reranker needs its own development-fitted thresholds')
        entries = [context.entries[context.lookup.by_key[c['key']]] for c in candidates]
        scores = reranker(query.query_text(), [entry.query_text() for entry in entries])
        if len(scores) != len(candidates) or not all(math.isfinite(float(s)) for s in scores):
            raise ValueError('Reranker returned invalid scores')
        candidates = sorted([dict(c, score=float(score)) for c, score in zip(candidates, scores)],
                            key=lambda c: (-c['score'], c['key']))
        thresholds = rerank_thresholds
    match = (MatchResult('match', exact, 1., None, 0., candidates) if exact is not None
             else decide(candidates, thresholds))
    result['match'] = {'decision': match.decision, 'key': match.key,
                       'candidates': candidates, 'reranked': reranker is not None and exact is None,
                       'exact_statement_and_interface': exact is not None}
    entry = context.entries[context.lookup.by_key[candidates[0]['key']]]
    reference = next((r for r in entry.references if r.get('validated')), None)
    reference = reference or next(iter(entry.references), None)
    result['source'] = {'key': entry.key, 'license': entry.license, 'attribution': entry.attribution,
                        'stored_reference_validated': bool(reference and reference.get('validated'))}
    result['answer_interface'] = query.entry if query.entry.get('method') else entry.entry
    if approved_library is not None:
        if query.slug and query.slug != entry.slug:
            return finish('query_identity_conflict')
        identity = approved_library.identity_check(entry, candidates, context.lookup, exact=exact is not None,
                                                  minimum_margin=thresholds['min_margin'])
        result['match']['identity_check'] = identity
        if not identity['accepted']:
            return finish(identity['reason'])
        if match.decision != 'match':
            return finish('identity_not_confident')
        qualification = approved_library.check(entry)
        result['source']['qualification'] = qualification
        if not qualification['approved']:
            return finish('stored_answer_not_approved')
    if match.decision == 'match' and reference:
        remaining = context.budget.route_wall_seconds - (time.perf_counter() - started)
        if remaining <= 0:
            return finish('budget_exhausted')
        code, verdict = check_stored(query, entry, min(remaining, context.budget.judge_wall_seconds))
        result['attempts'].append({'stage': 'stored', 'public': verdict.to_dict()})
        if verdict.passed:
            result.update(decision='answered', code=code, example_passed=True, route='stored')
            return finish()
        if verdict.reason == judge.SANDBOX_ERROR:
            return finish('sandbox_unavailable')
    if not allow_generation:
        return finish('no_verified_stored_answer')
    if context.generator is None:
        return finish('generator_not_configured')
    remaining = context.budget.route_wall_seconds - (time.perf_counter() - started)
    if remaining <= context.budget.judge_reserve_seconds:
        return finish('budget_exhausted')
    fallback_context = copy.copy(context)
    fallback_context.budget = replace(context.budget, route_wall_seconds=remaining)
    extra = ('### Retrieved candidate (may solve a different variant; verify the query constraints)\n'
             + entry.statement + '\n```python\n' + reference['code'] + '\n```') if reference else ''
    generated: RouteResult = run_generative(fallback_context, query, 'retrieval',
                                           retrieved_context=(extra, [entry.key]))
    result['attempts'].extend(generated.attempts)
    if any((a.get('meta') or {}).get('tool_items', 0) for a in generated.attempts):
        return finish('generator_used_tools')
    last = generated.attempts[-1] if generated.attempts else {}
    if generated.code and (last.get('public') or {}).get('passed'):
        result.update(decision='answered', code=generated.code, example_passed=True, route='adapted')
        return finish()
    return finish('generation_not_verified')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('query', type=Path, help='JSON Problem with parsed public examples; see editor-protocol.md')
    parser.add_argument('--index', choices=('research', 'corpus'), default='research')
    parser.add_argument('--fallback', choices=('none', 'codex'), default='none')
    parser.add_argument('--device', choices=('cpu', 'cuda'), default='cpu', help='Explicit embedding device; no automatic fallback')
    parser.add_argument('--rerank-run', type=Path, help='Frozen development calibration directory (corpus index only)')
    parser.add_argument('--doppler-cli', type=Path)
    parser.add_argument('--reranker-model', type=Path)
    parser.add_argument('--approved-library', type=Path,
                        help='Require source-bound independent qualification; no generated fallback')
    args = parser.parse_args()
    if args.approved_library and (args.index != 'corpus' or args.fallback != 'none'):
        parser.error('--approved-library requires --index corpus and --fallback none')
    reranker, rerank_thresholds = None, None
    if args.rerank_run:
        if args.index != 'corpus' or args.device != 'cpu' or not args.doppler_cli or not args.reranker_model:
            parser.error('--rerank-run requires --index corpus, --device cpu, --doppler-cli and --reranker-model')
        from .calibrated_reranker import load
        reranker, rerank_thresholds = load(args.rerank_run, args.doppler_cli, args.reranker_model)
    elif args.doppler_cli or args.reranker_model:
        parser.error('Reranker paths require an explicit --rerank-run')
    if args.approved_library:
        if args.device != 'cpu' or args.rerank_run:
            parser.error('Qualified lookup currently requires CPU and no reranker')
        from .approved_library import load_context
        context, approved = load_context(args.approved_library)
        query = Problem.from_dict(json.loads(args.query.read_text()))
        print(json.dumps(answer(context, query, approved_library=approved), ensure_ascii=False))
        return
    import numpy as np
    from . import corpus, splits
    from .embed import Embedder
    from .lookup import LookupIndex, load_thresholds
    import torch
    torch.set_num_threads(4)
    contract = json.loads((LANE_ROOT / 'contracts/run_contract.json').read_text())
    print(f'[run-contract] run_name=editor-answer pairs_input_spec={args.query} resume_from=none '
          f'resume_stage=none decode=harness-default eval_dataset_paths=public_examples device={args.device} '
          f'schedule=serial runtime_mode={args.device} sweep_mode=live index={args.index}', file=sys.stderr)
    if args.index == 'corpus':
        entries = corpus.read_entries()
        if json.loads(corpus.KEYS_PATH.read_text()) != [entry.key for entry in entries]:
            raise ValueError('Corpus key order differs from embeddings; rebuild')
        index = LookupIndex(entries, np.load(corpus.EMBEDDINGS_PATH))
    else:
        entries = splits.read_index_entries()
        index = LookupIndex.load(entries)
    generator = None
    if args.fallback == 'codex':
        from .cli_solvers import SOLVERS
        config = contract['solvers']['codex']
        generator = SOLVERS['codex'](config['repo'], config['effort'])
    context = Context(generator=generator, embedder=Embedder(device=args.device), lookup=index,
                      thresholds=load_thresholds(), classifier=None, entries=entries,
                      budget=Budget.from_contract(contract))
    query = Problem.from_dict(json.loads(args.query.read_text()))
    print(json.dumps(answer(context, query, reranker=reranker, rerank_thresholds=rerank_thresholds,
                            allow_generation=args.fallback != 'none'), ensure_ascii=False))


if __name__ == '__main__':
    main()
