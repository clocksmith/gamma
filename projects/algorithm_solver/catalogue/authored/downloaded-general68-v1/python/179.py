"""179. Largest Number (Medium).

Specification: https://leetcode.com/problems/largest-number/description/
"""


from functools import cmp_to_key


def _compare(a, b):
    if a + b > b + a:
        return -1
    if a + b < b + a:
        return 1
    return 0


def solve(nums: list[int]) -> str:
    texts = sorted((str(v) for v in nums), key=cmp_to_key(_compare))
    result = "".join(texts)
    return "0" if result and result[0] == "0" else result


class Solution:
    def largestNumber(self, nums: list[int]) -> str:
        return solve(nums)
