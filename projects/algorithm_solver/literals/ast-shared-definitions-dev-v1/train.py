"""Fit-only candidate mining, common nested-call cover and archive-byte selection."""
from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
from functools import cache
from hashlib import sha256
import json

import archive
import patterns

LIBRARY_BUDGETS = (512, 2048)
POOL_LIMIT = 48
MIN_SUPPORT = 2
MAX_PURCHASES = 16
CHALLENGERS = 6
PRIORS = ('general', 'hole')


def fingerprint(value):
    data = json.dumps(value, separators=(',', ':'), ensure_ascii=False).encode()
    return sha256(data).hexdigest()


def raw_trees(documents):
    return [doc.tree if doc.tree is not None else doc.normalized for doc in documents]


def nodes(tree):
    yield tree
    for child in tree[4]:
        yield from nodes(child)


@cache
def concrete_size(template):
    if template[0] == 'HOLE':
        return 0
    return 1 + sum(map(concrete_size, template[4]))


def mine(documents):
    counts, support = Counter(), Counter()
    for doc in documents:
        if doc.tree is None:
            continue
        local = Counter()
        for root in doc.tree:
            for node in nodes(root):
                local.update(set(patterns.templates(node)))
        counts.update(local)
        support.update(local.keys())  # sampling contract: one document per lineage
    viable = [t for t in counts if support[t] >= MIN_SUPPORT and concrete_size(t) >= 2]
    viable.sort(key=lambda t: (-(concrete_size(t) - 1) * counts[t], -support[t], repr(t)))
    return tuple(viable[:POOL_LIMIT]), len(viable)


class Corpus:
    """Match once per distinct tree; reuse exactly the same matches in either format."""

    def __init__(self, documents, pool):
        self.documents = raw_trees(documents)
        self.pool = pool
        self.counts = Counter(node for doc in self.documents if not isinstance(doc, bytes)
                              for root in doc for node in nodes(root))
        by_root = defaultdict(list)
        for candidate, template in enumerate(pool):
            by_root[template[1:3]].append((candidate, template))
        self.matches = {}
        for node in self.counts:
            hits = []
            for candidate, template in by_root[node[1:3]]:
                binding = patterns.match(template, node)
                if binding is not None:
                    shift, args = binding
                    hits.append((candidate, shift, args))
            if hits:
                self.matches[node] = hits

    def cover(self, selected, blocked=()):
        numbered = {candidate: index for index, candidate in enumerate(selected)
                    if candidate not in blocked}

        @cache
        def best(node):
            children = [best(child) for child in node[4]]
            cost = 1 + sum(x[0] for x in children)
            encoded = (*node[:4], tuple(x[1] for x in children))
            # Stable ties retain the literal, then the earliest candidate in the fit pool.
            for candidate, shift, args in self.matches.get(node, ()):
                if candidate not in numbered:
                    continue
                filled = [best(child) for child in args]
                call_cost = 1 + sum(x[0] for x in filled)
                if call_cost < cost:
                    cost = call_cost
                    encoded = ('CALL', node[1], numbered[candidate], shift, tuple(x[1] for x in filled))
            return cost, encoded

        docs = [doc if isinstance(doc, bytes) else tuple(best(root)[1] for root in doc)
                for doc in self.documents]
        costs = {node: best(node)[0] for node in self.counts}
        best.cache_clear()
        return docs, costs

    def rank_additions(self, selected, costs):
        # This local, overlapping event bound only schedules expensive byte trials.
        scores = Counter()
        for node, hits in self.matches.items():
            for candidate, _, args in hits:
                if candidate not in selected:
                    gain = costs[node] - 1 - sum(costs[arg] for arg in args)
                    if gain > 0:
                        scores[candidate] += self.counts[node] * gain
        return sorted(scores, key=lambda i: (-scores[i], i))


@dataclass
class Fit:
    selected: tuple
    prior: str
    model: object
    size: int
    accounting: dict


def fit_model(calls, definitions, kind, selected):
    trials = []
    for prior in PRIORS:
        model = archive.fit_prior(calls, definitions, prior)
        data, sizes = archive.encode_archive(calls, definitions, kind, model)
        trials.append(Fit(selected, prior, model, len(data), sizes))
    return min(trials, key=lambda fit: fit.size)  # declared prior order resolves ties


def train(corpus, kind, budget):
    pool = corpus.pool
    current = fit_model(corpus.documents, (), kind, ())
    purchases = []
    evaluated = []
    for _ in range(MAX_PURCHASES):
        _, costs = corpus.cover(current.selected)
        best = None
        tried = 0
        for candidate in corpus.rank_additions(current.selected, costs):
            proposed = (*current.selected, candidate)
            definitions = tuple(pool[i] for i in proposed)
            if len(archive.encode_library(definitions, kind)) > budget:
                continue
            evaluated.append(proposed)
            calls, _ = corpus.cover(proposed)
            trial = fit_model(calls, definitions, kind, proposed)
            tried += 1
            if trial.size < current.size and (best is None or trial.size < best.size):
                best = trial
            if tried == CHALLENGERS:
                break
        if best is None:
            break
        purchases.append({'pool_id': best.selected[-1], 'fit_bytes_saved': current.size - best.size,
                          'fit_total_bytes': best.size, 'prior': best.prior,
                          'library_bytes': best.accounting['library_bytes']})
        current = best
    return current, {'measured_candidate_libraries': len(evaluated), 'purchases': purchases,
                     'ordered_proposals': [list(lib) for lib in evaluated]}


def common_slate(corpus, original, budget, cache_by_library):
    """Rescore all exposed libraries with both headers and priors, using only fit bytes."""
    slate = {()}
    for _, search in original.values():
        slate.update(tuple(lib) for lib in search['ordered_proposals'])
    ordered = sorted(slate, key=lambda lib: (len(lib), lib))
    winners = {}
    feasible = Counter()
    for lib in ordered:
        if lib not in cache_by_library:
            calls, _ = corpus.cover(lib)
            defs = tuple(corpus.pool[i] for i in lib)
            cells = {}
            for prior in PRIORS:
                model = archive.fit_prior(calls, defs, prior)
                for kind in ('flat', 'dag'):
                    packet, summary = archive.encode_archive(calls, defs, kind, model)
                    cells[kind, prior] = Fit(lib, prior, model, len(packet), summary)
            cache_by_library[lib] = cells
        for (kind, _), cell in cache_by_library[lib].items():
            if cell.accounting['library_bytes'] > budget:
                continue
            feasible[kind] += 1
            if kind not in winners or cell.size < winners[kind].size:
                winners[kind] = cell
    result = {kind: (fit, {'measured_library_prior_cells': 2 * len(ordered),
                           'admissible_library_prior_cells': feasible[kind]})
              for kind, fit in winners.items()}
    return result, {'ordered_libraries': [list(lib) for lib in ordered],
                    'library_count': len(ordered), 'priors_per_library': len(PRIORS),
                    'tie_order': 'library length, pool-id sequence, then declared prior order'}


def call_counts(doc):
    counts = Counter()
    nested = 0

    def visit(node, inside_call):
        nonlocal nested
        is_call = node[0] == 'CALL'
        if is_call:
            counts[node[2]] += 1
            nested += int(inside_call)
        for child in node[4]:
            visit(child, inside_call or is_call)

    if not isinstance(doc, bytes):
        for root in doc:
            visit(root, False)
    return counts, nested
