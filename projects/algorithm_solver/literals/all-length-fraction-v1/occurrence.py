"""Prelaunch amendment: equivalent occurrence graph and independent AC replay.

The multiplier optimizer, path solver, quantization and backward integer
certificate remain inherited unchanged from fraction-capacity-v1/dual.py.
"""
from collections import deque
import numpy as np
import dual

BaseGraph = dual.Graph


class Graph(BaseGraph):
    """Build exact old pid/start/end edge order by walking prefixes, no slices."""
    def __init__(self, texts, pool, mandatory):
        self.pool = list(pool)
        self.mandatory = set(mandatory)
        self.pids = sorted(texts)
        self.texts = texts
        assert len(set(pool)) == len(pool) and not set(pool) & self.mandatory
        trie = {}
        for entry, word in [(-1, word) for word in self.mandatory] + list(enumerate(pool)):
            assert word
            node = trie
            for character in word:
                node = node.setdefault(character, {})
            node[None] = entry
        self.at, self.lengths, self.order = [], [], []
        entries = []
        for pid in self.pids:
            text = texts[pid]
            rows = []
            self.lengths.append(len(text))
            for start in range(len(text)):
                row = []
                node = trie
                for end in range(start + 1, len(text) + 1):
                    node = node.get(text[end - 1])
                    if node is None:
                        break
                    if None not in node:
                        continue
                    entry = node[None]
                    base = 10 * (end - start == 1) - 1
                    if entry < 0:
                        row.append((end, -1, base))
                    else:
                        occurrence = len(entries)
                        entries.append(entry)
                        row.append((end, occurrence, base))
                        self.order.append((pid, start, end, entry))
                rows.append(row)
            self.at.append(rows)
        self.occ_entry = np.asarray(entries, dtype=np.int64)


class Automaton:
    """Independent Aho-Corasick matcher with output links, not merged lists."""
    def __init__(self, pool, mandatory):
        self.children = [{}]
        self.failure = [0]
        self.output_link = [-1]
        self.terminal = [None]
        self.transitions = {}
        assert len(set(pool)) == len(pool) and not set(pool) & set(mandatory)
        for word, entry in [(word, i) for i, word in enumerate(pool)] + [(word, -1) for word in mandatory]:
            assert word
            state = 0
            for character in word:
                if character not in self.children[state]:
                    self.children[state][character] = len(self.children)
                    self.children.append({})
                    self.failure.append(0)
                    self.output_link.append(-1)
                    self.terminal.append(None)
                state = self.children[state][character]
            assert self.terminal[state] is None
            self.terminal[state] = (len(word), entry)
        queue = deque(self.children[0].values())
        while queue:
            state = queue.popleft()
            for character, child in self.children[state].items():
                target = self.transition(self.failure[state], character)
                self.failure[child] = target
                self.output_link[child] = target if self.terminal[target] is not None else self.output_link[target]
                queue.append(child)

    def transition(self, state, character):
        # Memoized sparse failure transitions: at most states * alphabet keys.
        pending = []
        while True:
            if character in self.children[state]:
                target = self.children[state][character]
                break
            key = (state, character)
            if key in self.transitions:
                target = self.transitions[key]
                break
            pending.append(key)
            if state == 0:
                target = 0
                break
            state = self.failure[state]
        for key in pending:
            self.transitions[key] = target
        return target

    def matches(self, text):
        """Yield start,end,entry in increasing end order; every match once."""
        state = 0
        for end, character in enumerate(text, 1):
            state = self.transition(state, character)
            output = state
            while output >= 0:
                terminal = self.terminal[output]
                if terminal is not None:
                    length, entry = terminal
                    yield end - length, end, entry
                output = self.output_link[output]


def independent_certificate(texts, pool, mandatory, q, capacity, denominator):
    """Forward end-order DAG with exact ints and independently assigned q indices.

    First AC pass counts optional occurrences at every start. Prefix sums give
    their offsets in the old pid/start/end order. The second end-ordered pass
    assigns each start's q values in increasing end order and evaluates shortest
    paths. O(pattern bytes * alphabet size + text bytes + matches), excluding
    sorting entry sums; the frozen source alphabet has at most96 characters;
    no quadratic substring creation or stored list of occurrence tuples.
    """
    assert denominator > 0 and capacity >= 0
    matcher = Automaton(pool, mandatory)
    sums = [0] * len(pool)
    cursor = 0
    total = 0
    for pid, text in sorted(texts.items()):
        counts = [0] * len(text)
        for start, end, entry in matcher.matches(text):
            if entry >= 0:
                counts[start] += 1
        offsets = []
        for count in counts:
            offsets.append(cursor)
            cursor += count
        assert cursor <= len(q)
        used = [0] * len(text)
        distance = [0] + [None] * len(text)
        for start, end, entry in matcher.matches(text):
            if entry < 0:
                penalty = 0
            else:
                penalty = int(q[offsets[start] + used[start]])
                used[start] += 1
                assert penalty >= 0
                sums[entry] += penalty
            if distance[start] is not None:
                value = distance[start] + (10 * (end - start == 1) - 1) * denominator + penalty
                if distance[end] is None or value < distance[end]:
                    distance[end] = value
        assert used == counts and distance[-1] is not None
        total += distance[-1]
    assert cursor == len(q)
    return total - sum(sorted(sums, reverse=True)[:capacity])
