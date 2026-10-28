"""1089. Duplicate Zeros (Easy).

Specification: https://leetcode.com/problems/duplicate-zeros/description/
"""


def solve(arr: list[int]) -> list[int]:
    result = []
    for value in arr:
        if len(result) >= len(arr):
            break
        result.append(value)
        if value == 0 and len(result) < len(arr):
            result.append(0)
    return result


class Solution:
    def duplicateZeros(self, arr: list[int]) -> list[int]:
        return solve(arr)
