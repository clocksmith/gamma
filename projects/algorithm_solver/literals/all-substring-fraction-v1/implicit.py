"""Synthetic prototype: full-substring fraction dual, without explicit strings.

One nonnegative multiplier per source start is shared by all outgoing occurrence
constraints. Compressed suffix intervals represent every possible entry exactly.
No corpus loader, optimizer launcher or publication path is provided.
"""
from __future__ import annotations

import heapq
import importlib.util
from pathlib import Path

_spec = importlib.util.spec_from_file_location(
    'all_substring_suffix_primitives',
    Path(__file__).resolve().parents[1] / 'all-length-fraction-v1/pool.py')
_suffix = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_suffix)


class RangeMinimum:
    def __init__(self, values):
        self.size = 1
        while self.size < len(values):
            self.size *= 2
        self.data = [None] * (2 * self.size)
        for i, value in enumerate(values):
            self.data[self.size + i] = value
        for i in range(self.size - 1, 0, -1):
            self.data[i] = self.minimum(self.data[2*i], self.data[2*i+1])

    @staticmethod
    def minimum(a, b):
        return b if a is None else a if b is None else min(a, b)

    def set(self, i, value):
        i += self.size
        self.data[i] = value
        while i > 1:
            i //= 2
            self.data[i] = self.minimum(self.data[2*i], self.data[2*i+1])

    def query(self, left, right):
        left += self.size
        right += self.size
        value = None
        while left < right:
            if left & 1:
                value = self.minimum(value, self.data[left]); left += 1
            if right & 1:
                right -= 1; value = self.minimum(value, self.data[right])
            left //= 2; right //= 2
        return value


def compare_prefix(text, start, word):
    """Compare a truncated source suffix to a word, treating a match as equal."""
    for offset, character in enumerate(word):
        if start + offset == len(text):
            return -1
        actual = text[start + offset]
        if actual != character:
            return -1 if actual < character else 1
    return 0


def occurrence_interval(texts, positions, word):
    bounds = []
    for after_equal in (False, True):
        lo, hi = 0, len(positions)
        while lo < hi:
            mid = (lo + hi) // 2
            pid, start = positions[mid]
            order = compare_prefix(texts[pid], start, word)
            if order < 0 or (after_equal and order == 0):
                lo = mid + 1
            else:
                hi = mid
        bounds.append(lo)
    return tuple(bounds)


class Index:
    """O(N) compressed-trie interval/length groups for ALL nonempty substrings."""
    def __init__(self, texts, banned):
        self.texts = dict(texts)
        self.banned = {word for word in banned if word}
        items = sorted(texts.items())
        codes, positions = [], []
        for owner, (pid, text) in enumerate(items):
            for start, character in enumerate(text):
                codes.append(ord(character) + len(items))
                positions.append((pid, start))
            codes.append(owner)
            positions.append(None)
        sa = _suffix.suffix_array(codes)
        full_lcp = _suffix.lcp_array(codes, sa)
        self.positions, self.lcp = [], []
        minimum = None
        for rank, position in enumerate(sa):
            minimum = full_lcp[rank] if minimum is None else min(minimum, full_lcp[rank])
            if positions[position] is not None:
                self.positions.append(positions[position])
                self.lcp.append(0 if len(self.positions) == 1 else minimum)
                minimum = None
        self.remaining = [len(texts[pid]) - start for pid, start in self.positions]
        # Nodes store depth, parent, children, own terminal ranks. A terminal may
        # also have children when one truncated suffix prefixes another.
        nodes = [{'depth': 0, 'parent': None, 'children': [], 'terminals': []}]
        stack = [0]
        for rank, length in enumerate(self.remaining):
            common = self.lcp[rank]
            while nodes[stack[-1]]['depth'] > common:
                stack.pop()
            if nodes[stack[-1]]['depth'] < common:
                parent = stack[-1]
                old = nodes[parent]['children'].pop()
                middle = len(nodes)
                nodes.append({'depth': common, 'parent': parent, 'children': [old], 'terminals': []})
                nodes[old]['parent'] = middle
                nodes[parent]['children'].append(middle)
                stack.append(middle)
            parent = stack[-1]
            if nodes[parent]['depth'] == length:
                nodes[parent]['terminals'].append(rank)
            else:
                leaf = len(nodes)
                nodes.append({'depth': length, 'parent': parent, 'children': [], 'terminals': [rank]})
                nodes[parent]['children'].append(leaf)
                stack.append(leaf)
        traversal = [0]
        for node in traversal:
            traversal.extend(nodes[node]['children'])
        intervals = {}
        for node in reversed(traversal):
            terminals = nodes[node]['terminals']
            chunks = [(rank, rank + 1) for rank in terminals] + [intervals[child] for child in nodes[node]['children']]
            if not chunks:
                intervals[node] = (0, 0)
            else:
                lo = min(a for a, b in chunks); hi = max(b for a, b in chunks)
                assert sum(b-a for a, b in chunks) == hi-lo
                intervals[node] = (lo, hi)
        self.groups = []
        for node in traversal[1:]:
            parent = nodes[node]['parent']
            lo, hi = intervals[node]
            self.groups.append({'lo': lo, 'hi': hi, 'first': nodes[parent]['depth']+1,
                                'last': nodes[node]['depth'], 'excluded_lengths': []})
        self.groups.sort(key=lambda group: (group['lo'], group['hi'], group['first']))
        by_interval = {(g['lo'], g['hi']): g for g in self.groups}
        assert len(by_interval) == len(self.groups)
        self.banned_ends = {pid: [set() for _ in text] for pid, text in texts.items()}
        for word in sorted(self.banned):
            lo, hi = occurrence_interval(texts, self.positions, word)
            if lo == hi:
                continue
            group = by_interval[lo, hi]
            assert group['first'] <= len(word) <= group['last']
            group['excluded_lengths'].append(len(word))
            for pid, start in self.positions[lo:hi]:
                self.banned_ends[pid][start].add(start + len(word))
        for group in self.groups:
            group['excluded_lengths'].sort()
            group['multiplicity'] = group['last'] - group['first'] + 1 - len(group['excluded_lengths'])
        self.distinct_allowed_entries = sum(g['multiplicity'] for g in self.groups)

    def weighted_selection(self, q, capacity):
        prefix = [0]
        for pid, start in self.positions:
            prefix.append(prefix[-1] + q[pid][start])
        weights = [prefix[g['hi']] - prefix[g['lo']] for g in self.groups]
        remaining = capacity
        selected, total = [], 0
        for gid in sorted(range(len(self.groups)), key=lambda i: (-weights[i], i)):
            count = min(remaining, self.groups[gid]['multiplicity'])
            if count:
                selected.append((gid, count)); total += count * weights[gid]; remaining -= count
            if not remaining:
                break
        return total, selected

    def selected_occurrences(self, selected):
        """Each selected length in a group has the same occurrence interval."""
        difference = [0] * (len(self.positions) + 1)
        for gid, count in selected:
            group = self.groups[gid]
            difference[group['lo']] += count; difference[group['hi']] -= count
        result = {pid: [0] * len(text) for pid, text in self.texts.items()}
        active = 0
        for rank, (pid, start) in enumerate(self.positions):
            active += difference[rank]
            result[pid][start] = active
        return result

    def selected_vocabulary(self, selected, longest_first=False):
        """Materialize at most capacity entries only for feasible-witness attempts."""
        result = []
        for gid, count in selected:
            group = self.groups[gid]
            pid, start = self.positions[group['lo']]
            excluded = set(group['excluded_lengths'])
            lengths = (range(group['last'], group['first']-1, -1) if longest_first
                       else range(group['first'], group['last'] + 1))
            for length in lengths:
                if length in excluded:
                    continue
                result.append(self.texts[pid][start:start+length]); count -= 1
                if not count:
                    break
            assert count == 0
        return result

    def certificate(self, q, capacity=256, denominator=1000000):
        assert type(denominator) is int and denominator > 0
        assert type(capacity) is int and capacity >= 0
        assert set(q) == set(self.texts)
        assert all(len(q[pid]) == len(text) and all(type(v) is int and v >= 0 for v in q[pid])
                   for pid, text in self.texts.items())
        paths, used = {}, {}
        for pid, text in sorted(self.texts.items()):
            cost = [None] * len(text) + [0]
            back = [None] * len(text)
            heap = []
            for start in range(len(text)-1, -1, -1):
                if start+2 <= len(text) and cost[start+2] is not None:
                    heapq.heappush(heap, (cost[start+2], start+2))
                removed = []
                banned = self.banned_ends[pid][start]
                while heap and heap[0][1] in banned:
                    removed.append(heapq.heappop(heap))
                candidates = []
                if heap:
                    candidates.append((heap[0][0]-denominator, heap[0][1]))
                for value in removed:
                    heapq.heappush(heap, value)
                if start+1 not in banned and cost[start+1] is not None:
                    candidates.append((cost[start+1]+9*denominator, start+1))
                if candidates:
                    value, end = min(candidates)
                    cost[start] = q[pid][start] + value; back[start] = end
            if cost[0] is None:
                raise ValueError('full allowed pool cannot cover a source')
            paths[pid] = cost[0]
            used[pid] = [0] * len(text)
            position = 0
            while position < len(text):
                used[pid][position] = 1; position = back[position]
        top, selected = self.weighted_selection(q, capacity)
        numerator = sum(paths.values()) - top
        return {'numerator': numerator, 'denominator': denominator,
                'integer_lower_bound': -(-numerator // denominator),
                'path_numerators': paths, 'top_capacity_numerator': top,
                'selected_groups': selected, 'path_starts': used}


def verify(index, q, capacity, denominator):
    """Independent interval-partition validation and segment-tree integer replay."""
    texts, positions = index.texts, index.positions
    assert type(capacity) is int and capacity >= 0
    assert type(denominator) is int and denominator > 0
    assert set(q) == set(texts) and all(len(q[pid]) == len(text) for pid, text in texts.items())
    assert set(positions) == {(pid, i) for pid, text in texts.items() for i in range(len(text))}
    assert len(set(positions)) == len(positions)
    ranks = {position: rank for rank, position in enumerate(positions)}
    # Independently validate suffix order using one-character/tail-rank keys.
    # An inverted suffix pair would yield an inverted tail pair until its first
    # unequal character or an empty tail, contradicting these sorted keys.
    previous_key = None
    for pid, start in positions:
        key = (texts[pid][start], ranks.get((pid, start+1), -1))
        assert previous_key is None or previous_key <= key
        previous_key = key
    lcp = [0] * len(positions)
    remaining = [len(texts[pid])-start for pid, start in positions]
    # Generalized Kasai replay, independently implemented on truncated source
    # suffixes. Carry decreases by one per source position, so comparisons are
    # linear even for highly repetitive texts and duplicate owners.
    for pid, text in texts.items():
        length = 0
        for start in range(len(text)):
            rank = ranks[pid, start]
            if rank == 0:
                length = 0
                continue
            other, at = positions[rank-1]
            while start+length < len(text) and at+length < len(texts[other]) and text[start+length] == texts[other][at+length]:
                length += 1
            lcp[rank] = length
            length = max(0, length-1)
    assert lcp == index.lcp and remaining == index.remaining
    lcp_min, remaining_min = RangeMinimum(lcp), RangeMinimum(remaining)
    coverage = 0
    previous = {}
    for group in index.groups:
        lo, hi, first, last = (group[k] for k in ('lo','hi','first','last'))
        assert 0 <= lo < hi <= len(positions) and 1 <= first <= last
        assert remaining_min.query(lo, hi) >= last
        assert hi-lo == 1 or lcp_min.query(lo+1, hi) >= last
        assert lo == 0 or lcp[lo] < first
        assert hi == len(positions) or lcp[hi] < first
        assert first > previous.get((lo,hi), 0)
        previous[lo,hi] = last
        coverage += last-first+1
    assert coverage == sum(length-common for length,common in zip(remaining,lcp))
    # Independently locate bans by ordered comparisons; no cached banned endpoint
    # sets or production-trie nodes are trusted by this verifier.
    excluded = {i: set() for i in range(len(index.groups))}
    banned_ends = {pid: [[] for _ in text] for pid,text in texts.items()}
    by_interval = {(g['lo'],g['hi']): i for i,g in enumerate(index.groups)}
    assert len(by_interval) == len(index.groups)
    for word in index.banned:
        # Separate implementation from production prefix comparison. Slices are
        # bounded by the supplied ban length, never by the all-substring pool.
        bounds = []
        for upper in (False, True):
            left, right = 0, len(positions)
            while left < right:
                middle = (left+right)//2
                pid, start = positions[middle]
                prefix_word = texts[pid][start:start+len(word)]
                if prefix_word < word or (upper and prefix_word == word):
                    left = middle+1
                else:
                    right = middle
            bounds.append(left)
        lo,hi = bounds
        if lo == hi:
            continue
        gid = by_interval[lo,hi]
        assert index.groups[gid]['first'] <= len(word) <= index.groups[gid]['last']
        excluded[gid].add(len(word))
        for rank in range(lo,hi):
            pid,start=positions[rank];banned_ends[pid][start].append(start+len(word))
    prefix = [0]
    for pid,start in positions:
        assert type(q[pid][start]) is int and q[pid][start] >= 0
        prefix.append(prefix[-1]+q[pid][start])
    weighted = []
    for gid,g in enumerate(index.groups):
        assert sorted(excluded[gid]) == g['excluded_lengths']
        multiplicity=g['last']-g['first']+1-len(excluded[gid])
        assert multiplicity == g['multiplicity']
        weighted.append((prefix[g['hi']]-prefix[g['lo']],multiplicity))
    assert index.distinct_allowed_entries == sum(count for weight, count in weighted)
    top=0;left=capacity
    for weight,count in sorted(weighted,reverse=True):
        take=min(left,count);top+=take*weight;left-=take
        if not left:break
    paths={}
    for pid,text in sorted(texts.items()):
        distance=[None]*len(text)+[0];tree=RangeMinimum(distance)
        for start in range(len(text)-1,-1,-1):
            blocked=sorted(set(banned_ends[pid][start]));multicost=None;left=start+2
            for end in blocked+[len(text)+1]:
                if end >= left:
                    multicost=RangeMinimum.minimum(multicost,tree.query(left,end))
                    left=end+1
            candidates=[]
            if multicost is not None:candidates.append(multicost-denominator)
            if start+1 not in blocked and distance[start+1] is not None:candidates.append(distance[start+1]+9*denominator)
            if candidates:distance[start]=q[pid][start]+min(candidates)
            tree.set(start,distance[start])
        if distance[0] is None:raise ValueError('full allowed pool cannot cover a source')
        paths[pid]=distance[0]
    return sum(paths.values())-top
