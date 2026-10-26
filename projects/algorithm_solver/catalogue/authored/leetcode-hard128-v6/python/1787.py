"""1787. Make the XOR of All Segments Equal to Zero.

DP over 1024 XOR states and residue-class value counts; O(1024*(n+k)) time, O(n+1024) space. Inputs are preserved.
"""

from collections import Counter


def solve(nums: list[int], k: int) -> int:
    costs = [0] + [len(nums)] * 1023
    for residue in range(k):
        counts = Counter(nums[residue::k])
        size = sum(counts.values())
        following = [min(costs) + size] * 1024
        for value, count in counts.items():
            price = size - count
            for target in range(1024):
                following[target] = min(following[target], costs[target ^ value] + price)
        costs = following
    return costs[0]


class Solution:
    def minChanges(self, nums: list[int], k: int) -> int:
        return solve(nums, k)
