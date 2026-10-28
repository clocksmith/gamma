"""2422. Merge Operations to Turn Array Into a Palindrome (Medium).

Specification: https://leetcode.com/problems/merge-operations-to-turn-array-into-a-palindrome/description/
"""


def solve(nums):
    i, j = 0, len(nums) - 1
    left, right, ops = nums[0], nums[-1], 0
    while i < j:
        if left == right:
            i += 1
            j -= 1
            if i < j:
                left, right = nums[i], nums[j]
        elif left < right:
            i += 1
            left += nums[i]
            ops += 1
        else:
            j -= 1
            right += nums[j]
            ops += 1
    return ops


class Solution:
    def minimumOperations(self, nums):
        return solve(nums)
