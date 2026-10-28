"""71. Simplify Path (Medium).

Specification: https://leetcode.com/problems/simplify-path/description/
"""


def solve(path: str) -> str:
    stack = []
    for part in path.split('/'):
        if part == '' or part == '.':
            continue
        if part == '..':
            if stack:
                stack.pop()
        else:
            stack.append(part)
    return '/' + '/'.join(stack)


class Solution:
    def simplifyPath(self, path: str) -> str:
        return solve(path)
