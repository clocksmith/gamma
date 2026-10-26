"""1313. Decompress Run-Length Encoded List (Easy).

Specification: https://leetcode.com/problems/decompress-run-length-encoded-list/description/
"""


def solve(nums: list[int]) -> list[int]:
    """O(n + output length) time, O(output length) space; preserve nums."""
    result = []
    for index in range(0, len(nums), 2):
        frequency, value = nums[index], nums[index + 1]
        for _ in range(frequency):
            result.append(value)
    return result


class Solution:
    def decompressRLElist(self, nums: list[int]) -> list[int]:
        return solve(nums)
