"""3530. Maximum Profit from Valid Topological Order in DAG.

Subset dynamic programming appends only vertices whose predecessor masks are already selected; O(n*2^n) time and O(2^n+n) space. Inputs are preserved.
"""

from array import array


def solve(n: int, edges: list[list[int]], score: list[int]) -> int:
    if not edges:
        return sum(position * value for position, value in enumerate(sorted(score), 1))
    predecessors = [0] * n
    for first, second in edges:
        predecessors[second] |= 1 << first
    size = 1 << n
    best = array('i', [-1]) * size
    best[0] = 0
    for mask in range(size):
        if best[mask] < 0:
            continue
        position = mask.bit_count() + 1
        remaining = (size - 1) ^ mask
        while remaining:
            bit = remaining & -remaining
            remaining ^= bit
            node = bit.bit_length() - 1
            if predecessors[node] & mask == predecessors[node]:
                following = mask | bit
                best[following] = max(best[following], best[mask] + position * score[node])
    return best[-1]


class Solution:
    def maxProfit(self, n: int, edges: list[list[int]], score: list[int]) -> int:
        return solve(n, edges, score)
