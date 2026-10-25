"""Incremental family vocabulary growth/merging; source is data, never executed.

Each accepted operation reselects qualified source alternatives and emits a
hash-linked ledger record. Proposal unions are not decoding vocabularies.
"""
import hashlib
import importlib.util
import json
import math
import statistics
import time
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('incremental_joint', HERE.parent / 'joint-composable-v1/search.py')
joint = importlib.util.module_from_spec(spec)
spec.loader.exec_module(joint)
ALPHABET = joint.ALPHABET


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def metrics(rows, vocabulary):
    counts = sorted(r['selections'] for r in rows.values())
    total = sum(counts)
    characters = sum(r['characters'] for r in rows.values())
    return {'programs': len(rows), 'entries': len(vocabulary), 'selections': total,
            'characters': characters, 'character_fraction': characters / total if total else 0,
            'median': statistics.median(counts) if counts else 0,
            'p95': counts[math.ceil(.95 * len(counts)) - 1] if counts else 0,
            'above32': sum(n > 32 for n in counts), 'above96': sum(n > 96 for n in counts),
            'character_excess': max(0, 10 * characters - total),
            'literal_utf8_bytes': sum(len(s.encode()) for s in vocabulary)}


def objective(m):
    """Fixed gate-oriented ordering, not post-result weight tuning."""
    return (m['above96'], m['above32'], m['character_excess'], m['selections'],
            m['characters'], m['literal_utf8_bytes'])


def dominates(a, b):
    keys = ('entries', 'above96', 'above32', 'character_excess', 'selections',
            'characters', 'literal_utf8_bytes')
    return all(a[k] <= b[k] for k in keys) and any(a[k] < b[k] for k in keys)


class Builder:
    def __init__(self, texts, owners, references, families, *, capacity, record=None, resume=(), cpu_seconds=None):
        if capacity not in (128, 256):
            raise ValueError('supported final capacities are 128 and 256')
        if set(texts) != set(owners) or set(references) != set(owners.values()) or set(families) != set(references):
            raise ValueError('complete fixed source/problem/family population required')
        if any(references[p] not in texts or owners[references[p]] != p for p in references):
            raise ValueError('invalid reference source choice')
        joint.compare.validate_texts(texts)
        self.texts, self.owners, self.references, self.families = texts, owners, references, families
        self.capacity = capacity
        self.graph = joint.compact.Graph(texts)
        self.graphs = {}
        self.legal_cache = {}
        self.banned = joint.banned_strings(texts)
        # No complete helper is automatically a reusable primitive. Conservatively
        # ban every named function definition/body pending a separate audit.
        for text in texts.values():
            tokens = joint.compact.lexical_tokens(text)
            for at, token in enumerate(tokens):
                if token[0] != 'function':
                    continue
                cursor = at + 1
                while cursor < len(tokens) and tokens[cursor][0] != '(':
                    cursor += 1
                depth = 0
                while cursor < len(tokens):
                    depth += (tokens[cursor][0] == '(') - (tokens[cursor][0] == ')')
                    cursor += 1
                    if depth == 0:
                        break
                if cursor == len(tokens) or tokens[cursor][0] != '{':
                    raise ValueError('unsupported helper function syntax')
                opening = tokens[cursor][1]
                depth = 0
                while cursor < len(tokens):
                    depth += (tokens[cursor][0] == '{') - (tokens[cursor][0] == '}')
                    closing = tokens[cursor][2]
                    cursor += 1
                    if depth == 0:
                        break
                body = text[opening:closing]
                self.banned.update((text[token[1]:closing], body, body[1:-1], body[1:-1].strip()))
        self.groups = defaultdict(list)
        for key, pid in sorted(owners.items()):
            self.groups[pid].append(key)
        self.record = record or (lambda row: None)
        self.chain = '0' * 64
        self.events = []
        self.frontiers = defaultdict(list)
        self.evaluations = 0
        self.deadline = None if cpu_seconds is None else time.process_time() + cpu_seconds
        self.resumed = {}
        for row in resume:
            saved = dict(row)
            expected = saved.pop('sha256')
            if saved['previous_sha256'] != self.chain or digest(saved) != expected:
                raise ValueError('growth ledger chain mismatch')
            self.chain = expected
            self.evaluations = row['evaluations']
            op = row['operation']
            for suffix in ('-start', '-add', '-exhausted'):
                if op.endswith(suffix):
                    self.resumed[(op[:-len(suffix)], tuple(row['ids']))] = row
                    break
            self.frontiers[tuple(row['ids'])] = row['frontier']

    def legal(self, piece):
        if piece in self.legal_cache:
            return self.legal_cache[piece]
        # A wrapper around an entire frozen solve body is also forbidden.
        allowed = len(piece) >= 2 and not any(body and body in piece for body in self.banned)
        allowed = allowed and len({self.owners[k] for k in self.graph.occurrence(piece)}) >= 2
        self.legal_cache[piece] = allowed
        return allowed

    def score(self, ids, learned, previous=None, changed=()):
        if self.deadline is not None and time.process_time() >= self.deadline:
            raise TimeoutError('bounded growth slice exhausted; resume hash-bound ledger')
        vocabulary = ALPHABET + sorted(set(learned))
        if len(vocabulary) > self.capacity or any(not self.legal(p) for p in vocabulary[96:]):
            raise ValueError('illegal decoding vocabulary')
        key = tuple(sorted(ids))
        if key not in self.graphs:
            wanted = {k: self.texts[k] for p in ids for k in self.groups[p]}
            self.graphs[key] = joint.compact.Graph(wanted)
        rows = self.graphs[key].score(vocabulary, previous, changed)
        choices, selected = joint.select_sources(rows, {p: self.groups[p] for p in ids}, self.references)
        self.evaluations += 1
        return {'ids': sorted(ids), 'learned': vocabulary[96:], 'choices': choices,
                'selected': selected, 'all_rows': rows, 'metrics': metrics(selected, vocabulary)}

    def emit(self, operation, state, **detail):
        key = tuple(state['ids'])
        compact = {'metrics': state['metrics'], 'dictionary_sha256': digest(ALPHABET + state['learned']),
                   'choices_sha256': digest(state['choices'])}
        frontier = self.frontiers[key]
        if not any(dominates(x['metrics'], compact['metrics']) for x in frontier):
            frontier[:] = [x for x in frontier if not dominates(compact['metrics'], x['metrics'])]
            if compact not in frontier:
                frontier.append(compact)
        row = {'operation': operation, 'previous_sha256': self.chain, 'ids': state['ids'],
               'learned_literals': state['learned'], 'source_choices': state['choices'],
               'metrics': state['metrics'], 'evaluations': self.evaluations,
               'frontier': list(frontier), **detail}
        row['sha256'] = digest(row)
        self.chain = row['sha256']
        self.events.append(row)
        self.record(row)

    def proposals(self, state):
        support = defaultdict(set)
        occurrences = Counter()
        # Include all qualified alternatives, not only the currently cheapest one.
        for pid in state['ids']:
            for key in self.groups[pid]:
                stream = state['all_rows'][key]['used']
                for a, b in zip(stream, stream[1:]):
                    piece = a + b
                    support[piece].add(pid)
                    occurrences[piece] += 1
        return sorted((p for p in support if len(support[p]) >= 2 and p not in state['learned'] and self.legal(p)),
                      key=lambda p: (-len(support[p]), -occurrences[p], len(p), p))

    def grow(self, ids, initial=(), *, slots=None, proposal_pool=None, label='growth'):
        target = self.capacity - 96 if slots is None else min(slots, self.capacity - 96)
        resumed = self.resumed.get((label, tuple(sorted(ids))))
        if resumed:
            initial = resumed['learned_literals']
        state = self.score(ids, initial)
        if resumed and (resumed['operation'].endswith('-exhausted') or len(state['learned']) >= target):
            return state
        self.emit(label + '-start', state)
        while len(state['learned']) < target:
            candidates = self.proposals(state) if proposal_pool is None else sorted(set(proposal_pool) - set(state['learned']))
            best = None
            # Exhaust this deterministic worklist; no arbitrary top-k slice.
            for piece in candidates:
                if not self.legal(piece):
                    continue
                candidate = self.score(ids, state['learned'] + [piece], state['all_rows'], [piece])
                if objective(candidate['metrics']) >= objective(state['metrics']):
                    continue
                rank = (objective(candidate['metrics']), len(piece), piece)
                if best is None or rank < best[0]:
                    best = (rank, piece, candidate)
            if best is None:
                self.emit(label + '-exhausted', state, candidates_considered=len(candidates))
                break
            before = state
            _, piece, state = best
            self.emit(label + '-add', state, added=piece, previous_metrics=before['metrics'],
                      candidates_considered=len(candidates),
                      changed_source_problems=[p for p in ids if before['choices'][p] != state['choices'][p]])
        return state

    def prune(self, state):
        # Exact resegmentation/reselection establishes redundancy, not token counts alone.
        for piece in sorted(state['learned'], key=lambda p: (-len(p), p)):
            candidate = self.score(state['ids'], [p for p in state['learned'] if p != piece], state['all_rows'], [piece])
            if all(candidate['selected'][p]['selections'] <= state['selected'][p]['selections'] for p in state['ids']) and candidate['metrics']['characters'] <= state['metrics']['characters']:
                before = state
                state = candidate
                self.emit('redundancy-remove', state, removed=piece, previous_metrics=before['metrics'])
        return state

    def run(self):
        families = defaultdict(list)
        for pid, family in sorted(self.families.items()):
            families[family].append(pid)
        # Local vocabularies use up to32 learned pieces; each fits128 on its own.
        nodes = {family: self.grow(ids, slots=32, label='family-' + family) for family, ids in families.items()}
        while len(nodes) > 1:
            pairs = []
            names = sorted(nodes)
            for i, a in enumerate(names):
                for b in names[i+1:]:
                    overlap = set(nodes[a]['learned']) & set(nodes[b]['learned'])
                    pairs.append((-sum(len(p.encode()) for p in overlap), -len(overlap), a, b))
            _, _, a, b = min(pairs)
            left, right = nodes.pop(a), nodes.pop(b)
            ids = sorted(left['ids'] + right['ids'])
            union = set(left['learned']) | set(right['learned'])
            shared = set(left['learned']) & set(right['learned'])
            # A union is only a candidate pool. Never instantiate an over-capacity language.
            merged = self.grow(ids, shared, proposal_pool=union, label='merge-allocate')
            merged = self.prune(merged)
            merged = self.grow(ids, merged['learned'], label='merge-expand')
            self.emit('families-merged', merged, parents=[a, b], proposal_union_entries=96 + len(union),
                      deduplicated_entries=len(shared), parent_metrics=[left['metrics'], right['metrics']])
            nodes[a + '+' + b] = merged
        return next(iter(nodes.values()))
