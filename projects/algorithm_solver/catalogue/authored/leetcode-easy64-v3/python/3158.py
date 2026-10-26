"""3158. Find the XOR of Numbers Which Appear Twice (Easy).

Specification: https://leetcode.com/problems/find-the-xor-of-numbers-which-appear-twice/description/
"""


def solve(nums: list[int]) -> int:
    """O(n) expected time, O(n) space; every value occurs at most twice and fits int32."""
    seen = set()
    result = 0
    for value in nums:
        if value in seen:
            result ^= value
        else:
            seen.add(value)
    return result


class Solution:
    def duplicateNumbersXOR(self, nums: list[int]) -> int:
        return solve(nums)
