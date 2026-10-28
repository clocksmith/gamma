"""Original frontend 3834 variant; qualification unknown."""

def solve(nums):
    stack = []
    for value in nums:
        while stack and stack[-1] == value:
            value += stack.pop()
        stack.append(value)
    return stack


class Solution:
    def mergeAdjacent(self, nums):
        return solve(nums)
