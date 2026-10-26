"""2164. Sort Even and Odd Indices Independently (Easy).

Specification: https://leetcode.com/problems/sort-even-and-odd-indices-independently/description/
"""


def solve(nums: list[int]) -> list[int]:
    """O(n log n) time, O(n) space; sort independent copies and preserve nums."""
    even = sorted(nums[::2])
    odd = sorted(nums[1::2], reverse=True)
    result = [0] * len(nums)
    for index in range(len(nums)):
        offset = index // 2
        result[index] = even[offset] if index % 2 == 0 else odd[offset]
    return result


class Solution:
    def sortEvenOdd(self, nums: list[int]) -> list[int]:
        return solve(nums)
