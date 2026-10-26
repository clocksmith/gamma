"""3113. Find the Number of Subarrays Where Boundary Elements Are Maximum.

A decreasing stack groups still-visible equal maxima; O(n) time and space. Inputs are preserved.
"""

def solve(nums: list[int]) -> int:
    stack = []
    answer = 0
    for value in nums:
        while stack and stack[-1][0] < value:
            stack.pop()
        if stack and stack[-1][0] == value:
            stack[-1][1] += 1
        else:
            stack.append([value, 1])
        answer += stack[-1][1]
    return answer


class Solution:
    def numberOfSubarrays(self, nums: list[int]) -> int:
        return solve(nums)
