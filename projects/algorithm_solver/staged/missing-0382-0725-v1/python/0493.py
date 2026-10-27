"""493. Reverse Pairs. Count previous values strictly greater than twice the current value; do not sort inputs in place."""

from bisect import bisect_left, bisect_right


class _Fenwick:
    def __init__(self, n):
        self.tree = [0] * (n + 1)

    def add(self, i, delta):
        while i < len(self.tree):
            self.tree[i] += delta
            i += i & -i

    def prefix(self, i):
        total = 0
        while i:
            total += self.tree[i]
            i -= i & -i
        return total

def solve(nums: list[int]) -> int:
    values = sorted(set(nums))
    tree = _Fenwick(len(values))
    answer = 0
    for i, value in enumerate(nums):
        answer += i - tree.prefix(bisect_right(values, 2 * value))
        tree.add(bisect_left(values, value) + 1, 1)
    return answer


class Solution:
    def reversePairs(self, nums: list[int]) -> int:
        return solve(nums)
