"""3666. Minimum Operations to Equalize Binary String
Candidate source; not executed, syntax-checked, tested, or qualified.
Specification: https://leetcode.com/problems/minimum-operations-to-equalize-binary-string/description/
Consulted specification/algorithm reference: https://github.com/doocs/leetcode/blob/f39d6eb98551c8b90713a26a70bf681494803ab9/solution/3600-3699/3666.Minimum%20Operations%20to%20Equalize%20Binary%20String/README_EN.md
Complexity: O(n alpha(n)) amortized time; O(n) space.
Zero-count BFS, with parity-separated successor sets; all flips use exactly k distinct positions.
"""

from __future__ import annotations
from collections import deque

def solve(s, k):
    n, zeros = len(s), s.count('0')
    successor = list(range(n + 3))
    def find(value):
        root = value
        while successor[root] != root:
            root = successor[root]
        while successor[value] != value:
            following = successor[value]
            successor[value] = root
            value = following
        return root
    distances = [-1] * (n + 1)
    distances[zeros] = 0
    successor[zeros] = find(zeros + 2)
    queue = deque([zeros])
    while queue:
        current = queue.popleft()
        if current == 0:
            return distances[current]
        low = abs(current - k)
        high = min(current + k, 2 * n - current - k)
        following = find(low)
        while following <= high:
            distances[following] = distances[current] + 1
            queue.append(following)
            successor[following] = find(following + 2)
            following = find(following)
    return -1


class Solution:
    def minOperations(self, s, k):
        return solve(s, k)
