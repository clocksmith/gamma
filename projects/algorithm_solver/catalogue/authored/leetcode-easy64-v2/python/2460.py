"""2460. Apply Operations to an Array (Easy).

Specification: https://leetcode.com/problems/apply-operations-to-an-array/description/
"""


def solve(nums: list[int]) -> list[int]:
    """O(n) time, O(n) space; apply operations left to right on a copy of nums."""
    result = nums.copy()
    for index in range(len(result) - 1):
        if result[index] == result[index + 1]:
            result[index] *= 2
            result[index + 1] = 0
    write = 0
    for index in range(len(result)):
        if result[index] != 0:
            result[write] = result[index]
            write += 1
    while write < len(result):
        result[write] = 0
        write += 1
    return result


class Solution:
    def applyOperations(self, nums: list[int]) -> list[int]:
        return solve(nums)
