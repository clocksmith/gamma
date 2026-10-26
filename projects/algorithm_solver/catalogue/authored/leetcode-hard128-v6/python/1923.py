"""1923. Longest Common Subpath.

Exact suffix automaton of the shortest path, intersected with every path; O(T + m log m) expected time, O(m) auxiliary space. Inputs are preserved.
"""

def solve(n: int, paths: list[list[int]]) -> int:
    shortest = min(paths, key=len)
    transitions = [{}]
    lengths = [0]
    links = [-1]
    last = 0
    for value in shortest:
        current = len(lengths)
        lengths.append(lengths[last] + 1)
        links.append(0)
        transitions.append({})
        previous = last
        while previous != -1 and value not in transitions[previous]:
            transitions[previous][value] = current
            previous = links[previous]
        if previous != -1:
            target = transitions[previous][value]
            if lengths[previous] + 1 == lengths[target]:
                links[current] = target
            else:
                clone = len(lengths)
                lengths.append(lengths[previous] + 1)
                links.append(links[target])
                transitions.append(dict(transitions[target]))
                while previous != -1 and transitions[previous].get(value) == target:
                    transitions[previous][value] = clone
                    previous = links[previous]
                links[target] = links[current] = clone
        last = current
    order = sorted(range(1, len(lengths)), key=lambda state: -lengths[state])
    common = lengths[:]
    for path in paths:
        best = [0] * len(lengths)
        state = matched = 0
        for value in path:
            while state and value not in transitions[state]:
                state = links[state]
                matched = min(matched, lengths[state])
            if value in transitions[state]:
                state = transitions[state][value]
                matched += 1
                best[state] = max(best[state], matched)
            else:
                state = matched = 0
        for state in order:
            parent = links[state]
            best[parent] = max(best[parent], min(best[state], lengths[parent]))
        common = [min(a, b) for a, b in zip(common, best)]
    return max(common)


class Solution:
    def longestCommonSubpath(self, n: int, paths: list[list[int]]) -> int:
        return solve(n, paths)
