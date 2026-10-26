"""1250. Check If It Is a Good Array.

Bezout identity reduces the question to the array gcd; O(n log M) time, O(1) auxiliary space. Inputs are preserved.
"""

from math import gcd


def solve(nums: list[int]) -> bool:
    common = 0
    for value in nums:
        common = gcd(common, value)
        if common == 1:
            return True
    return False


class Solution:
    def isGoodArray(self, nums: list[int]) -> bool:
        return solve(nums)
