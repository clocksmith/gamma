"""2748. Number of Beautiful Pairs (Easy).

Specification: https://leetcode.com/problems/number-of-beautiful-pairs/description/
"""


def solve(nums: list[int]) -> int:
    """O(n * d) time, O(1) auxiliary space; d is maximum decimal digit count; preserve nums."""
    def gcd(left: int, right: int) -> int:
        while right:
            left, right = right, left % right
        return left

    first_digits = [0] * 10
    pairs = 0
    for value in nums:
        last_digit = value % 10
        for digit in range(1, 10):
            if gcd(digit, last_digit) == 1:
                pairs += first_digits[digit]
        first_digit = value
        while first_digit >= 10:
            first_digit //= 10
        first_digits[first_digit] += 1
    return pairs


class Solution:
    def countBeautifulPairs(self, nums: list[int]) -> int:
        return solve(nums)
