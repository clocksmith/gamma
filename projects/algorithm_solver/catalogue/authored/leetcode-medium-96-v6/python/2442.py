"""2442. Count Number of Distinct Integers After Reverse Operations: collect every original integer and its reversed decimal value."""


def solve(nums: list[int]) -> int:
    """O(n d) expected time and O(n) auxiliary space for at most d decimal digits; inputs are read-only."""
    values = set(nums)
    for value in nums:
        remaining = value
        reversed_value = 0
        while remaining:
            remaining, digit = divmod(remaining, 10)
            reversed_value = reversed_value * 10 + digit
        values.add(reversed_value)
    return len(values)


class Solution:
    def countDistinctIntegers(self, nums: list[int]) -> int:
        return solve(nums)
