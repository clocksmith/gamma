"""3949. Subtree Inversion Sum II
Candidate source; not executed, syntax-checked, tested, or qualified.
Specification: https://leetcode.com/problems/subtree-inversion-sum-ii/description/
Consulted specification/algorithm reference: https://github.com/doocs/leetcode/blob/f39d6eb98551c8b90713a26a70bf681494803ab9/solution/3900-3999/3949.Subtree%20Inversion%20Sum%20II/README_EN.md
Complexity: O(n*k) time and O(n*k) worst-case space; iterative tree order.
All selected pairs, including different child branches, must be at distance at least k. Nearest-selected-distance states and suffix maxima enforce this. Inputs preserved; native judge method pending.
"""

from __future__ import annotations

def solve(edges, nums, k):
    if k == 1:
        return sum(abs(value) for value in nums)
    n = len(nums)
    graph = [[] for _ in range(n)]
    for left, right in edges:
        graph[left].append(right)
        graph[right].append(left)
    parent = [-1] * n
    order = [0]
    for node in order:
        for child in graph[node]:
            if child != parent[node]:
                parent[child] = node
                order.append(child)
    tables = [None] * n
    negative = float('-inf')
    for node in reversed(order):
        states = [[negative] * (k + 1) for _ in range(2)]
        selected = [-nums[node], nums[node]]
        states[0][k] = nums[node]
        states[1][k] = -nums[node]
        for child in graph[node]:
            if child == parent[node]:
                continue
            child_states = tables[child]
            for parity in range(2):
                opposite = child_states[1 - parity]
                selected[parity] += max(opposite[k - 1], opposite[k])
                other = [negative] * (k + 1)
                for distance in range(1, k):
                    other[distance] = child_states[parity][distance - 1]
                other[k] = max(child_states[parity][k - 1], child_states[parity][k])
                current = states[parity]
                suffix_current = current.copy()
                suffix_other = other.copy()
                for distance in range(k - 1, -1, -1):
                    suffix_current[distance] = max(suffix_current[distance], suffix_current[distance + 1])
                    suffix_other[distance] = max(suffix_other[distance], suffix_other[distance + 1])
                merged = [negative] * (k + 1)
                for distance in range(k + 1):
                    lower = max(distance, k - distance)
                    merged[distance] = max(current[distance] + suffix_other[lower],
                                           other[distance] + suffix_current[lower])
                states[parity] = merged
            tables[child] = None
        for parity in range(2):
            states[parity][0] = selected[parity]
        tables[node] = states
    return max(tables[0][0])
