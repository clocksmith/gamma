"""3864. Minimum Cost to Partition a Binary String."""
from __future__ import annotations


def solve(s: str, encCost: int, flatCost: int) -> int:
    """O(n) time and O(n) space; only equal even-length splits, with recursion depth at most log2(n)."""
    prefix = [0]
    for char in s:
        prefix.append(prefix[-1] + (char == '1'))
    def partition(left, right):
        sensitive = prefix[right] - prefix[left]
        if sensitive == 0:
            return flatCost
        length = right - left
        cost = length * sensitive * encCost
        if length % 2 == 0:
            middle = (left + right) // 2
            cost = min(cost, partition(left, middle) + partition(middle, right))
        return cost
    return partition(0, len(s))


class Solution:
    def minCost(self, s: str, encCost: int, flatCost: int) -> int:
        return solve(s, encCost, flatCost)
