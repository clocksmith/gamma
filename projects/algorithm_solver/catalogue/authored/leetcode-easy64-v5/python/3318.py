"""3318. Find X-Sum of All K-Long Subarrays I (Easy).

Specification: https://leetcode.com/problems/find-x-sum-of-all-k-long-subarrays-i/description/
"""


def solve(nums: list[int], k: int, x: int) -> list[int]:
    """O(n * k log(k + 1)) time, O(n + k) space; rank by descending frequency, then value."""
    result = []
    for start in range(len(nums) - k + 1):
        counts = {}
        for index in range(start, start + k):
            counts[nums[index]] = counts.get(nums[index], 0) + 1
        ranked = sorted(counts.items(), key=lambda item: (-item[1], -item[0]))
        total = 0
        for index in range(min(x, len(ranked))):
            total += ranked[index][0] * ranked[index][1]
        result.append(total)
    return result


class Solution:
    def findXSum(self, nums: list[int], k: int, x: int) -> list[int]:
        return solve(nums, k, x)
