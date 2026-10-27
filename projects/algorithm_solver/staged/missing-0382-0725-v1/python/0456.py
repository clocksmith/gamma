"""456. 132 Pattern."""

def solve(nums: list[int]) -> bool:
    stack = []
    third = float('-inf')
    for value in reversed(nums):
        if value < third:
            return True
        while stack and value > stack[-1]:
            third = stack.pop()
        stack.append(value)
    return False


class Solution:
    def find132pattern(self, nums: list[int]) -> bool:
        return solve(nums)
