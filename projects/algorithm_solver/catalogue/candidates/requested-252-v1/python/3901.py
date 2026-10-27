"""3901. Good Subsequence Queries.

Specification: https://leetcode.com/problems/good-subsequence-queries/description/
"""

from __future__ import annotations

from math import gcd


def solve(nums: list[int], p: int, queries: list[list[int]]) -> int:
    """Segment tree of whole GCD and exact-one-deletion GCD sets; O((n+q log n)*D log V) time, O(n*D) space, D=O(log V). Inputs are preserved."""
    width = 1
    while width < len(nums):
        width *= 2
    whole = [0] * (2 * width)
    deleted = [[] for _ in range(2 * width)]
    def pull(node):
        left, right = node * 2, node * 2 + 1
        whole[node] = gcd(whole[left], whole[right])
        possibilities = {gcd(value, whole[right]) for value in deleted[left]}
        possibilities.update(gcd(whole[left], value) for value in deleted[right])
        deleted[node] = list(possibilities)
    for index, value in enumerate(nums):
        whole[width + index] = value if value % p == 0 else 0
        deleted[width + index] = [0]
    for node in range(width - 1, 0, -1):
        pull(node)
    answer = 0
    for index, value in queries:
        node = width + index
        whole[node] = value if value % p == 0 else 0
        while node > 1:
            node //= 2
            pull(node)
        answer += p in deleted[1]
    return answer
