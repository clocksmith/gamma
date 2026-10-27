"""3930. Power Update After K-th Largest Insertion II.

Specification: https://leetcode.com/problems/power-update-after-k-th-largest-insertion-ii/description/
"""

from __future__ import annotations


def solve(nums: list[int], p: int, queries: list[list[int]]) -> list[int]:
    """O((n+q) log(n+q) + q log V) time, O(n+q) space; exact modular arithmetic. Inputs are preserved."""
    values = sorted(set(nums) | {query[0] for query in queries})
    rank = {value: index + 1 for index, value in enumerate(values)}
    tree = [0] * (len(values) + 1)
    def insert(value):
        index = rank[value]
        while index < len(tree):
            tree[index] += 1
            index += index & -index
    def select(order):
        index = 0
        step = 1 << (len(values).bit_length() - 1)
        while step:
            next_index = index + step
            if next_index < len(tree) and tree[next_index] < order:
                order -= tree[next_index]
                index = next_index
            step >>= 1
        return values[index]
    for value in nums:
        insert(value)
    count = len(nums)
    answer = []
    for value, order in queries:
        insert(value)
        count += 1
        p = pow(p, select(count - order + 1), 1_000_000_007)
        answer.append(p)
    return answer


class Solution:
    def powerUpdate(self, nums: list[int], p: int, queries: list[list[int]]) -> list[int]:
        return solve(nums, p, queries)
