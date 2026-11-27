#!/usr/bin/env python3
"""Run the spent-development comparison and independently replay its receipt."""
import argparse
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path
from statistics import median
from time import perf_counter

import archive
from independent_decode import decode_archive, substitute
from sources import load_documents, verify_documents
from train import (CHALLENGERS, LIBRARY_BUDGETS, MAX_PURCHASES, MIN_SUPPORT, POOL_LIMIT,
                   PRIORS, Corpus, call_counts, common_slate, fingerprint, fit_model, mine, train)

HERE = Path(__file__).resolve().parent
SPLIT = HERE.parent / 'a2-recursive-frames-v1' / 'corpus_split.json'
RECEIPT = HERE / 'dev_receipt.json'
N_LINEAGES = 64
SALT = 'ast-sharing-v1:'
SLICES = {'train': {'codenet-primary', 'codenet-secondary', 'guides-algo'},
          'dev': {'codenet-fresh', 'codenet-fresh2', 'sources-20'}}


def sha(data):
    return hashlib.sha256(data).hexdigest()


def pick(rows, split):
    groups = defaultdict(list)
    for row in rows:
        if row['slice'] in SLICES[split] and row['problem_id'] is not None:
            assert row['split'] == split
            groups[row['lineage']].append(row)
    ranked = sorted(groups, key=lambda lin: (sha((SALT + 'lineage:' + lin).encode()), lin))
    assert len(ranked) >= N_LINEAGES
    selected = []
    for lineage in ranked[:N_LINEAGES]:
        row = min(groups[lineage], key=lambda r: (sha((SALT + 'id:' + r['id']).encode()), r['id']))
        assert sha((HERE.parent / row['rel_path']).read_bytes()) == row['raw_sha256'], row['id']
        selected.append(row)
    return selected


def document_stats(docs):
    return {'files': len(docs), 'slices': dict(Counter(d.row['slice'] for d in docs)),
            'supported': sum(d.tree is not None for d in docs),
            'refusals': [d.id for d in docs if d.tree is None],
            'normalized_bytes': sum(len(d.normalized) for d in docs),
            'rows': [{'id': d.id, 'lineage': d.lineage, 'raw_sha256': d.row['raw_sha256'],
                      'normalized_sha256': sha(d.normalized)} for d in docs]}


def checked(calls, defs, kind, model, originals, docs):
    data, accounting = archive.encode_archive(calls, defs, kind, model)
    decoded = decode_archive(data)
    for key, expected in [('documents', originals), ('calls', calls), ('definitions', defs)]:
        assert list(decoded[key]) == list(expected), f'independent {key} mismatch'
    assert verify_documents(docs, decoded['documents']) == [d.normalized for d in docs]
    assert len(data) == accounting['complete_bytes']
    size = accounting['payload_bytes']
    return {**accounting, 'archive_sha256': sha(data), 'payload_sha256': sha(data[-4-size:-4]),
            'definition_events': archive.library_stats(defs, kind)}


def matrix(fit, dev, trained, docs):
    selected = trained.selected
    defs = tuple(fit.pool[i] for i in selected)
    train_stream, _ = fit.cover(selected)
    test_stream, _ = dev.cover(selected)
    cells = {}
    for prior in PRIORS:
        model = trained.model if prior == trained.prior else archive.fit_prior(train_stream, defs, prior)
        payload = archive.encode_payload(test_stream, defs, model)
        for kind in ('flat', 'dag'):
            result = checked(test_stream, defs, kind, model, dev.documents, docs)
            assert len(payload) == result['payload_bytes'] and sha(payload) == result['payload_sha256']
            cells[f'{kind}/{prior}'] = result
    return cells


def per_lineage(calls, defs, model):
    return [len(archive.encode_payload([doc], defs, model)) * 8 for doc in calls]


def inline_calls(documents, definitions, retained):
    """Preserve each fixed caller/argument; inline omitted IDs and compact surviving IDs."""
    ids = {old: new for new, old in enumerate(retained)}

    def visit(node):
        children = tuple(visit(c) for c in node[4])
        if node[0] == 'NODE':
            return (*node[:4], children)
        _, group, fid, shift, _ = node
        if fid in ids:
            return ('CALL', group, ids[fid], shift, children)
        return substitute(definitions[fid], children, shift)

    return [doc if isinstance(doc, bytes) else tuple(visit(root) for root in doc)
            for doc in documents]


def compare_inlined(fit, dev, docs, result, full, extra):
    """Charge the counterfactual complete archive after physically removing definitions."""
    ids = result.selected
    original_library = tuple(fit.pool[i] for i in ids)
    fit_stream, _ = fit.cover(ids)
    dev_stream, _ = dev.cover(ids)
    comparisons = {}
    groups = [('joint', set(extra)), *((str(i), {i}) for i in extra)]
    for label, omitted in groups:
        retained = [j for j, candidate in enumerate(ids) if candidate not in omitted]
        kept_ids = tuple(ids[j] for j in retained)
        defs = tuple(original_library[j] for j in retained)
        fit_calls = inline_calls(fit_stream, original_library, retained)
        dev_calls = inline_calls(dev_stream, original_library, retained)
        counter = fit_model(fit_calls, defs, 'dag', kept_ids)
        packet = checked(dev_calls, defs, 'dag', counter.model, dev.documents, docs)
        comparisons[label] = {'removed_pool_ids': sorted(omitted), 'fit_prior': counter.prior,
            'complete_bytes': packet['complete_bytes'], 'library_bytes': packet['library_bytes'],
            'model_bytes': packet['model_bytes'], 'payload_bytes': packet['payload_bytes'],
            'full_archive_savings_vs_inline_bytes': packet['complete_bytes'] - full['complete_bytes']}
    return comparisons


def compare_budget(fit, dev, docs, budget, plain, fits):
    arms, fitted, streams, per_file = {}, {}, {}, {}
    for kind in ('flat', 'dag'):
        result, search = fits[kind]
        selected = result.selected
        defs = tuple(fit.pool[i] for i in selected)
        calls, _ = dev.cover(selected)
        grid = matrix(fit, dev, result, docs)
        primary = grid[f'{kind}/{result.prior}']
        assert primary['library_bytes'] <= budget
        uses = [call_counts(doc) for doc in calls]
        totals = sum((count for count, _ in uses), Counter())
        arms[kind] = {
            'selected_pool_ids': list(selected), 'fit_prior': result.prior,
            'fit_complete_bytes': result.size, 'search': search, 'dev': primary,
            'header_prior_controls': grid, 'dev_nested_calls': sum(n for _, n in uses),
            'dev_calls_by_pool_id': {str(c): totals[i] for i, c in enumerate(selected)},
        }
        fitted[kind], streams[kind] = result, calls
        per_file[kind] = per_lineage(calls, defs, result.model)
    hier = fitted['dag']
    distinct = tuple(x for x in hier.selected if x not in fitted['flat'].selected)
    defs = tuple(fit.pool[i] for i in hier.selected)
    no_extras, _ = dev.cover(hier.selected, distinct)
    actual = arms['dag']['dev']
    ablated = checked(no_extras, defs, 'dag', hier.model, dev.documents, docs)
    assert actual['header_bytes'] == ablated['header_bytes']
    saved = ablated['payload_bytes'] - actual['payload_bytes']
    no_extras_bits = per_lineage(no_extras, defs, hier.model)
    single_ablation = {}
    for candidate in distinct:
        without, _ = dev.cover(hier.selected, (candidate,))
        disabled = checked(without, defs, 'dag', hier.model, dev.documents, docs)
        assert disabled['header_bytes'] == actual['header_bytes']
        single_ablation[str(candidate)] = disabled['payload_bytes'] - actual['payload_bytes']
    rows = []
    for i, doc in enumerate(docs):
        counts, _ = call_counts(streams['dag'][i])
        used = {str(c): counts[k] for k, c in enumerate(hier.selected) if c in distinct and counts[k]}
        rows.append({'lineage': doc.lineage, 'flat_payload_bits': per_file['flat'][i],
                     'hier_payload_bits': per_file['dag'][i], 'incremental_calls': used,
                     'incremental_savings_bits': no_extras_bits[i] - per_file['dag'][i]})
    delta = [r['hier_payload_bits'] - r['flat_payload_bits'] for r in rows]
    gap = actual['complete_bytes'] - arms['flat']['dev']['complete_bytes']
    gap_plain = actual['complete_bytes'] - plain['complete_bytes']
    return {'arms': arms, 'hier_only_pool_ids': list(distinct), 'hier_minus_flat_complete_bytes': gap,
            'hier_minus_plain_complete_bytes': gap_plain,
            'hier_only_ablation': {'header_bytes_held_fixed': actual['header_bytes'],
                                   'ablated_payload_bytes': ablated['payload_bytes'],
                                   'pooled_payload_bytes_saved': saved,
                                   'fixed_calls_inline_repriced': compare_inlined(fit, dev, docs, hier, actual, distinct) if distinct else {},
                                   'individual_pooled_payload_bytes_saved': single_ablation,
                                   'using_lineages': sum(bool(r['incremental_calls']) for r in rows)},
            'lineage_payload_diagnostic': {'median_hier_minus_flat_bits': median(delta),
                'improved_tied_worse': [sum(x < 0 for x in delta), delta.count(0), sum(x > 0 for x in delta)],
                'unit': 'one independently framed payload per problem lineage', 'rows': rows},
            'purchase_mechanism_pass': bool(gap < 0 and gap_plain < 0 and distinct and saved > 0)}


def run():
    start = perf_counter()
    partition = json.loads(SPLIT.read_text())
    fit_rows = pick(partition['train'], 'train')
    fit_docs = load_documents(fit_rows)
    pool, eligible = mine(fit_docs)
    fit = Corpus(fit_docs, pool)
    plain_fit = fit_model(fit.documents, (), 'flat', ())
    indexed = perf_counter()
    trained, train_times = {}, {}
    for budget in LIBRARY_BUDGETS:
        trained[budget] = {}
        for kind in ('flat', 'dag'):
            clock = perf_counter()
            trained[budget][kind] = train(fit, kind, budget)
            train_times[f'{budget}/{kind}'] = round(perf_counter() - clock, 3)
    # The libraries and probability models above are immutable during development scoring.
    # Post-hoc sensitivity to unequal early stopping. Score exactly the same
    # candidate libraries in both formats, before the first dev byte is loaded.
    common, slates, common_times, cache_by_library = {}, {}, {}, {}
    for budget in LIBRARY_BUDGETS:
        clock = perf_counter()
        common[budget], slates[budget] = common_slate(fit, trained[budget], budget, cache_by_library)
        common_times[str(budget)] = round(perf_counter() - clock, 3)
    eval_start = perf_counter()
    dev_rows = pick(partition['dev'], 'dev')
    for field in ('lineage', 'problem_id', 'raw_sha256', 'squeezed_sha256'):
        assert not ({r[field] for r in fit_rows} & {r[field] for r in dev_rows}), field
    dev_docs = load_documents(dev_rows)
    dev = Corpus(dev_docs, pool)
    plain = checked(dev.documents, (), 'flat', plain_fit.model, dev.documents, dev_docs)
    results, times = {}, {}
    for budget in LIBRARY_BUDGETS:
        clock = perf_counter()
        results[str(budget)] = compare_budget(fit, dev, dev_docs, budget, plain, trained[budget])
        equal = compare_budget(fit, dev, dev_docs, budget, plain, common[budget])
        results[str(budget)]['common_search_sensitivity'] = {**slates[budget], 'result': equal}
        times[str(budget)] = round(perf_counter() - clock, 3)
        print(f'Completed {budget}-byte budget', flush=True)
    payload = {'schema': 'gamma.bits.ast-shared-definitions.dev.v1',
        'manifest_sha256': sha(SPLIT.read_bytes()),
        'scope': 'Spent problem-lineage-disjoint development; standalone normalized-tree archives.',
        'design': {'salt': SALT, 'rows_per_split': N_LINEAGES, 'library_budgets_bytes': list(LIBRARY_BUDGETS),
                   'max_purchases': MAX_PURCHASES, 'measured_challengers_per_round': CHALLENGERS,
                   'candidate_pool_limit': POOL_LIMIT, 'min_fit_lineage_support': MIN_SUPPORT,
                   'allowed_priors': list(PRIORS)},
        'fit': document_stats(fit_docs), 'dev': document_stats(dev_docs),
        'eligible_fit_templates': eligible, 'ordered_candidate_pool': [
            {'pool_id': i, 'sha256': fingerprint(t), 'flat_template': json.loads(json.dumps(t))}
            for i, t in enumerate(pool)],
        'plain': {**plain, 'fit_prior': plain_fit.prior, 'fit_complete_bytes': plain_fit.size},
        'budgets': results, 'exact_ast_coverage_gate': all(d.tree is not None for d in (*fit_docs, *dev_docs))}
    payload['greedy_positive_dev_budgets'] = [k for k, exp in results.items()
            if payload['exact_ast_coverage_gate'] and exp['purchase_mechanism_pass']]
    payload['common_slate_positive_dev_budgets'] = [k for k, exp in results.items()
            if payload['exact_ast_coverage_gate'] and exp['common_search_sensitivity']['result']['purchase_mechanism_pass']]
    payload['positive_dev_budgets'] = [k for k in payload['greedy_positive_dev_budgets']
                                      if k in payload['common_slate_positive_dev_budgets']]
    elapsed = {'fit_normalize_mine_match_seconds': round(indexed - start, 3),
               'train_seconds_by_budget_and_format': train_times, 'common_slate_fit_seconds': common_times,
               'evaluation_seconds_by_budget': times,
               'total_evaluation_seconds': round(perf_counter() - eval_start, 3),
               'total_elapsed_seconds': round(perf_counter() - start, 3)}
    return payload, elapsed


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=('run', 'check'))
    args = parser.parse_args()
    result, elapsed = run()
    if args.command == 'run':
        RECEIPT.write_text(json.dumps({**result, 'measured_work': elapsed}, indent=2) + '\n')
    else:
        stored = json.loads(RECEIPT.read_bytes())
        stored.pop('measured_work')
        if result != stored:
            raise SystemExit('development replay differs from recorded receipt')
    print(json.dumps({'positive_dev_budgets': result['positive_dev_budgets'],
                      'exact_ast_coverage_gate': result['exact_ast_coverage_gate'], 'measured_work': elapsed}))


if __name__ == '__main__':
    main()
