"""347. Top K Frequent Elements (Medium).

Specification: https://leetcode.com/problems/top-k-frequent-elements/description/
"""


def solve(nums: list[int], k: int) -> list[int]:
    counts = {}
    for value in nums:
        counts[value] = counts.get(value, 0) + 1
    entries = sorted(counts.items(), key=lambda item: (-item[1], item[0]))
    return [value for value, _count in entries[:k]]


class Solution:
    def topKFrequent(self, nums: list[int], k: int) -> list[int]:
        return solve(nums, k)
