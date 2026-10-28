"""739. Daily Temperatures (Medium).

Specification: https://leetcode.com/problems/daily-temperatures/description/
"""


def solve(temperatures: list[int]) -> list[int]:
    answer = [0] * len(temperatures)
    stack = []
    for index, value in enumerate(temperatures):
        while stack and temperatures[stack[-1]] < value:
            previous = stack.pop()
            answer[previous] = index - previous
        stack.append(index)
    return answer


class Solution:
    def dailyTemperatures(self, temperatures: list[int]) -> list[int]:
        return solve(temperatures)
