"""31. Next Permutation (Medium).

Specification: https://leetcode.com/problems/next-permutation/description/
"""


def solve(nums: list[int]) -> list[int]:
    result = nums[:]
    pivot = -1
    for i in range(len(result) - 2, -1, -1):
        if result[i] < result[i + 1]:
            pivot = i
            break
    if pivot == -1:
        return result[::-1]
    for i in range(len(result) - 1, pivot, -1):
        if result[i] > result[pivot]:
            result[i], result[pivot] = result[pivot], result[i]
            break
    left, right = pivot + 1, len(result) - 1
    while left < right:
        result[left], result[right] = result[right], result[left]
        left += 1
        right -= 1
    return result


class Solution:
    def nextPermutation(self, nums: list[int]) -> list[int]:
        return solve(nums)
