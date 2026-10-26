"""2455. Average Value of Even Numbers That Are Divisible by Three (Easy).

Specification: https://leetcode.com/problems/average-value-of-even-numbers-that-are-divisible-by-three/description/
"""


def solve(nums: list[int]) -> int:
    """O(n) time, O(1) space; average multiples of six and round down; preserve nums."""
    total = 0
    count = 0
    for value in nums:
        if value % 6 == 0:
            total += value
            count += 1
    return 0 if count == 0 else total // count


class Solution:
    def averageValue(self, nums: list[int]) -> int:
        return solve(nums)
