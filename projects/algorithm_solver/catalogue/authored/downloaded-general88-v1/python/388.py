"""388. Longest Absolute File Path (Medium).

Specification: https://leetcode.com/problems/longest-absolute-file-path/description/
"""


def solve(input: str) -> int:
    stack = []
    best = 0
    for line in input.split('\n'):
        depth = 0
        while depth < len(line) and line[depth] == '\t':
            depth += 1
        name = line[depth:]
        while len(stack) > depth:
            stack.pop()
        stack.append(name)
        if '.' in name:
            length = sum(len(part) for part in stack) + len(stack) - 1
            best = max(best, length)
    return best


class Solution:
    def lengthLongestPath(self, input: str) -> int:
        return solve(input)
