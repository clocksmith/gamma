"""922. Sort Array By Parity II (Easy).

Specification: https://leetcode.com/problems/sort-array-by-parity-ii/description/
"""


def solve(nums: list[int]) -> list[int]:
    """O(n) time and space; fill even and odd result indices in original encounter order."""
    result = [0] * len(nums)
    even_index, odd_index = 0, 1
    for value in nums:
        if value % 2 == 0:
            result[even_index] = value
            even_index += 2
        else:
            result[odd_index] = value
            odd_index += 2
    return result


class Solution:
    def sortArrayByParityII(self, nums: list[int]) -> list[int]:
        return solve(nums)
