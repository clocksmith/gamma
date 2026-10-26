"""3264. Final Array State After K Multiplication Operations I (Easy).

Specification: https://leetcode.com/problems/final-array-state-after-k-multiplication-operations-i/description/
"""


def solve(nums: list[int], k: int, multiplier: int) -> list[int]:
    """O(n * k) time, O(n) space; preserve nums; first minimum wins ties; values remain below 10^9."""
    result = nums.copy()
    for _ in range(k):
        minimum_index = 0
        for index in range(1, len(result)):
            if result[index] < result[minimum_index]:
                minimum_index = index
        result[minimum_index] *= multiplier
    return result


class Solution:
    def getFinalState(self, nums: list[int], k: int, multiplier: int) -> list[int]:
        return solve(nums, k, multiplier)
