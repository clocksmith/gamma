"""503. Next Greater Element II."""

def solve(nums: list[int]) -> list[int]:
    n = len(nums)
    answer = [-1] * n
    stack = []
    for i in range(2 * n):
        index = i % n
        while stack and nums[stack[-1]] < nums[index]:
            answer[stack.pop()] = nums[index]
        if i < n:
            stack.append(index)
    return answer


class Solution:
    def nextGreaterElements(self, nums: list[int]) -> list[int]:
        return solve(nums)
