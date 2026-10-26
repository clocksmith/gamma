"""2835. Minimum Operations to Form Subsequence With Target Sum. Fulfill low target bits by splitting the nearest available larger power."""


def solve(nums: list[int], target: int) -> int:
    """O(n+31^2) time and O(31) space. Inputs are preserved."""
    if sum(nums) < target:
        return -1
    counts = [0] * 33
    for value in nums:
        counts[value.bit_length() - 1] += 1
    answer = 0
    for bit in range(31):
        if target >> bit & 1:
            higher = bit
            while counts[higher] == 0:
                higher += 1
            while higher > bit:
                counts[higher] -= 1
                counts[higher - 1] += 2
                answer += 1
                higher -= 1
            counts[bit] -= 1
        counts[bit + 1] += counts[bit] // 2
    return answer


class Solution:
    def minOperations(self, nums: list[int], target: int) -> int:
        return solve(nums, target)
