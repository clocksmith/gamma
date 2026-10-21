"""Scoped adaptation of Gamma joint-v1: explicit mandatory basis and reachability.

The legacy 96-character default is retained. No candidate program is executed.
"""
from collections import defaultdict
import math
import time

ASCII96 = tuple(chr(i) for i in range(32, 127)) + ('\n',)


def order(vocab, mandatory=ASCII96):
    return list(mandatory) + sorted(set(vocab) - set(mandatory))


def trie(vocab):
    root = {}
    for index, text in enumerate(vocab):
        node = root
        for char in text:
            node = node.setdefault(char, {})
        node[None] = index
    return root


def segment(text, tree):
    # Existing clusters-v1 backward DP/tie rule; explicit None for unreachability.
    n = len(text)
    cost = [n + 1] * (n + 1)
    edge = [None] * n
    cost[n] = 0
    for pos in range(n - 1, -1, -1):
        node = tree
        end = pos
        while end < n and text[end] in node:
            node = node[text[end]]
            end += 1
            if None in node and (cost[end] + 1 < cost[pos] or
                                cost[end] + 1 == cost[pos] and
                                (edge[pos] is None or node[None] < edge[pos][0])):
                cost[pos] = cost[end] + 1
                edge[pos] = (node[None], end)
    if cost[0] > n:
        return None
    result = []
    pos = 0
    while pos < n:
        index, pos = edge[pos]
        result.append(index)
    return result


class Occurrences:
    def __init__(self, sources):
        self.sources = {(pid, variant): text for pid, variants in sources.items()
                        for variant, text in variants.items()}
        self.cache = {}
        self.substring_scans = 0

    def get(self, fragment):
        if fragment not in self.cache:
            hits = {}
            for key, text in self.sources.items():
                self.substring_scans += 1
                positions = []
                start = text.find(fragment)
                while start >= 0:
                    positions.append(start)
                    start = text.find(fragment, start + 1)
                if positions:
                    hits[key] = tuple(positions)
            self.cache[fragment] = hits
        return self.cache[fragment]

    def support(self, fragment):
        return {pid for pid, _ in self.get(fragment)}


def evaluate(sources, vocab, width, parent=None, mandatory=ASCII96, occurrences=None):
    began = time.process_time()
    vocab = tuple(order(vocab, mandatory))
    if len(vocab) > 2 ** width:
        raise ValueError('dictionary exceeds fixed-width budget')
    if not vocab or any(not text for text in vocab):
        raise ValueError('nonempty dictionary literals required')
    if any(text == piece for variants in sources.values() for text in variants.values() for piece in vocab):
        raise ValueError('whole-program literal')
    tree = trie(vocab)
    added = set(vocab) - set(parent['vocab']) if parent else set()
    removed = set(parent['vocab']) - set(vocab) if parent else set()
    changed_keys = set()
    if parent:
        if occurrences is None:
            occurrences = Occurrences(sources)
        for piece in added:
            changed_keys.update(occurrences.get(piece))
    parsed, chosen = {}, {}
    recomputed = reused = dependency_reused = 0
    for pid, variants in sorted(sources.items()):
        options = []
        for variant, text in sorted(variants.items()):
            key = (pid, variant)
            previous = parent['parsed'].get(key) if parent else None
            deletion_used = parent and previous is not None and bool(set(previous) & removed)
            if parent and key in parent['parsed'] and key not in changed_keys and not deletion_used:
                parts = previous
                reused += 1
                if removed and any(piece in text for piece in removed):
                    dependency_reused += 1
            else:
                ids = segment(text, tree)
                parts = None if ids is None else tuple(vocab[index] for index in ids)
                recomputed += 1
            parsed[key] = parts
            if parts is not None:
                assert ''.join(parts) == text
                options.append((len(parts), len(text.encode('utf-8')), variant))
        if options:
            chosen[pid] = min(options)[2]
    counts = [len(parsed[(pid, variant)]) for pid, variant in chosen.items()]
    dictionary = 8 + sum(4 + len(text.encode('utf-8')) for text in vocab)
    packets = sum(41 + (width * count + 7) // 8 for count in counts)
    return {'vocab': vocab, 'parsed': parsed, 'chosen': chosen,
            'coverage': len(chosen), 'denominator': len(sources),
            'uncovered': sorted(set(sources) - set(chosen)),
            'unreachable_variants': sorted(key for key, value in parsed.items() if value is None),
            'selections': sum(counts), 'package_bytes': dictionary + packets,
            'dictionary_bytes': dictionary, 'packet_bytes': packets,
            'stats': {'recomputed': recomputed, 'reused': reused,
                      'deletion_dependency_reused': dependency_reused,
                      'process_cpu_seconds': time.process_time() - began}}


def comparable(state):
    return {k: v for k, v in state.items() if k != 'stats'}


def cost(state):
    return -state['coverage'], state['selections'], state['package_bytes']


def minimum_count(text, vocab):
    # Independent forward recurrence: never let a finite sentinel become coverage.
    by_first = defaultdict(list)
    for piece in vocab:
        by_first[piece[0]].append(piece)
    costs = [math.inf] * (len(text) + 1)
    costs[0] = 0
    for start, char in enumerate(text):
        if costs[start] == math.inf:
            continue
        for piece in by_first[char]:
            if text.startswith(piece, start):
                end = start + len(piece)
                costs[end] = min(costs[end], costs[start] + 1)
    return None if costs[-1] == math.inf else int(costs[-1])


def audit(sources, state, width):
    chosen = {}
    for pid, variants in sorted(sources.items()):
        options = []
        for variant, text in sorted(variants.items()):
            count = minimum_count(text, state['vocab'])
            parts = state['parsed'][(pid, variant)]
            assert (count is None) == (parts is None)
            if count is not None:
                assert count == len(parts)
                options.append((count, len(text.encode()), variant))
        if options:
            chosen[pid] = min(options)[2]
    assert chosen == state['chosen']
    count = sum(len(state['parsed'][(pid, variant)]) for pid, variant in chosen.items())
    assert count == state['selections'] and len(chosen) == state['coverage']
    assert 8 + sum(4 + len(s.encode()) for s in state['vocab']) == state['dictionary_bytes']
    assert sum(41 + (width * len(state['parsed'][(p, v)]) + 7) // 8 for p, v in chosen.items()) == state['packet_bytes']
    return True
