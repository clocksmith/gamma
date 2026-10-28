"""898. Bitwise ORs of Subarrays (Medium).

Specification: https://leetcode.com/problems/bitwise-ors-of-subarrays/description/
"""


def solve(arr: list[int]) -> int:
    result = set()
    current = set()
    for value in arr:
        nxt = {value}
        for v in current:
            nxt.add(v | value)
        current = nxt
        result.update(current)
    return len(result)


class Solution:
    def subarrayBitwiseORs(self, arr: list[int]) -> int:
        return solve(arr)
