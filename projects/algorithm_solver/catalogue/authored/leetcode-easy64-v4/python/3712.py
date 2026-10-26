"""3712. Sum of Elements With Frequency Divisible by K (Easy).

Specification: https://leetcode.com/problems/sum-of-elements-with-frequency-divisible-by-k/description/
"""


def solve(nums: list[int], k: int) -> int:
    """O(n) expected time, O(u) space; count every occurrence of each qualifying value."""
    counts = {}
    for value in nums:
        counts[value] = counts.get(value, 0) + 1
    result = 0
    for value, count in counts.items():
        if count % k == 0:
            result += value * count
    return result


class Solution:
    def sumDivisibleByK(self, nums: list[int], k: int) -> int:
        return solve(nums, k)
