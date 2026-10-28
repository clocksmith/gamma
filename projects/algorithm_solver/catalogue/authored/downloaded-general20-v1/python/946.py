"""946. Validate Stack Sequences (Medium).

Specification: https://leetcode.com/problems/validate-stack-sequences/description/
"""


def solve(pushed: list[int], popped: list[int]) -> bool:
    stack = []
    popped_index = 0
    for value in pushed:
        stack.append(value)
        while stack and popped_index < len(popped) and stack[-1] == popped[popped_index]:
            stack.pop()
            popped_index += 1
    return len(stack) == 0


class Solution:
    def validateStackSequences(self, pushed: list[int], popped: list[int]) -> bool:
        return solve(pushed, popped)
