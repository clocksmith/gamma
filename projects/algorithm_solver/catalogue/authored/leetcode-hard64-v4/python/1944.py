"""1944. Number of Visible People in a Queue."""


def solve(heights: list[int]) -> list[int]:
    """Decreasing stack for the problem's distinct heights; O(n) time and O(n) space. Inputs are preserved."""
    answer = [0] * len(heights)
    stack = []
    for index in range(len(heights) - 1, -1, -1):
        while stack and stack[-1] < heights[index]:
            stack.pop()
            answer[index] += 1
        if stack:
            answer[index] += 1
        stack.append(heights[index])
    return answer


class Solution:
    def canSeePersonsCount(self, heights: list[int]) -> list[int]:
        return solve(heights)
