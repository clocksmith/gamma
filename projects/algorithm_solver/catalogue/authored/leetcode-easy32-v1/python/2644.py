"""2644. Find the Maximum Divisibility Score (Easy).

Specification: https://leetcode.com/problems/find-the-maximum-divisibility-score/description/
"""


def solve(nums: list[int], divisors: list[int]) -> int:
    """O(len(nums)*len(divisors)) time, O(1) space; preserve both arrays."""
    best_divisor = divisors[0]
    best_score = -1
    for divisor in divisors:
        score = 0
        for value in nums:
            if value % divisor == 0:
                score += 1
        if score > best_score or (score == best_score and divisor < best_divisor):
            best_score = score
            best_divisor = divisor
    return best_divisor


class Solution:
    def maxDivScore(self, nums: list[int], divisors: list[int]) -> int:
        return solve(nums, divisors)
