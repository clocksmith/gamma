"""2342. Max Sum of a Pair With Equal Sum of Digits: retain the largest earlier number for every decimal digit sum."""


def solve(nums: list[int]) -> int:
    """O(n d) time and O(d) auxiliary entries for at most d decimal digits; inputs are read-only."""
    largest = {}
    answer = -1
    for value in nums:
        remaining = value
        digit_sum = 0
        while remaining:
            remaining, digit = divmod(remaining, 10)
            digit_sum += digit
        if digit_sum in largest:
            answer = max(answer, value + largest[digit_sum])
        largest[digit_sum] = max(value, largest.get(digit_sum, value))
    return answer


class Solution:
    def maximumSum(self, nums: list[int]) -> int:
        return solve(nums)
