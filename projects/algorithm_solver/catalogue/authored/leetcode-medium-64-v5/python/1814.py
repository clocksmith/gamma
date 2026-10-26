"""1814. Count Nice Pairs in an Array: group values by their difference from their digit reversal."""


def solve(nums: list[int]) -> int:
    """O(n * log(M + 1)) expected time and O(n) space, with M the largest value; inputs are read-only."""
    modulus = 1_000_000_007
    counts = {}
    result = 0
    for value in nums:
        remaining = value
        reversed_value = 0
        while remaining:
            reversed_value = reversed_value * 10 + remaining % 10
            remaining //= 10
        key = value - reversed_value
        previous = counts.get(key, 0)
        result = (result + previous) % modulus
        counts[key] = previous + 1
    return result


class Solution:
    def countNicePairs(self, nums: list[int]) -> int:
        return solve(nums)
