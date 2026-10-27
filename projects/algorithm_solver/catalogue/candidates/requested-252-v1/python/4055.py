"""4055. Count Shadow Pairs II.

Specification: https://leetcode.com/problems/count-shadow-pairs-ii/description/
"""

from __future__ import annotations


class _CountTree:
    def __init__(self, size):
        self.size = size
        self.tree = [0] * (size + 1)

    def add(self, index):
        while index <= self.size:
            self.tree[index] += 1
            index += index & -index

    def prefix(self, index):
        total = 0
        while index:
            total += self.tree[index]
            index -= index & -index
        return total

    def kth(self, rank):
        index = 0
        bit = 1 << (self.size.bit_length() - 1)
        while bit:
            following = index + bit
            if following <= self.size and self.tree[following] < rank:
                index = following
                rank -= self.tree[following]
            bit >>= 1
        return index + 1


def solve(nums: list[int]) -> int:
    """O(n log^2 n) time and O(n) peak auxiliary space; divide-and-conquer with exact open-value-range blockers. Inputs are preserved."""
    def count(left, right):
        if right - left < 2:
            return 0
        middle = (left + right) // 2
        answer = count(left, middle) + count(middle, right)
        values = sorted(set(nums[left:right]))
        ranks = {value: index + 1 for index, value in enumerate(values)}
        tree = _CountTree(len(values))
        starts = []
        inserted = 0
        for index in range(middle - 1, left - 1, -1):
            rank = ranks[nums[index]]
            not_greater = tree.prefix(rank)
            upper = tree.kth(not_greater + 1) if not_greater < inserted else len(values) + 1
            starts.append((upper, rank))
            tree.add(rank)
            inserted += 1
        tree = _CountTree(len(values))
        ends = []
        for index in range(middle, right):
            rank = ranks[nums[index]]
            lower_count = tree.prefix(rank - 1)
            lower = tree.kth(lower_count) if lower_count else 1
            ends.append((rank, lower))
            tree.add(rank)
        starts.sort(reverse=True)
        ends.sort(reverse=True)
        tree = _CountTree(len(values))
        position = 0
        for rank, lower in ends:
            while position < len(starts) and starts[position][0] >= rank:
                tree.add(starts[position][1])
                position += 1
            answer += tree.prefix(rank - 1) - tree.prefix(lower - 1)
        return answer
    return count(0, len(nums))
