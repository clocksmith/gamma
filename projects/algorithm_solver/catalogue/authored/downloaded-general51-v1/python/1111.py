"""1111. Maximum Nesting Depth of Two Valid Parentheses Strings (Medium).

Specification: https://leetcode.com/problems/maximum-nesting-depth-of-two-valid-parentheses-strings/description/
"""


def solve(seq: str) -> list[int]:
    result = []
    depth = 0
    for ch in seq:
        if ch == '(':
            result.append(depth % 2)
            depth += 1
        else:
            depth -= 1
            result.append(depth % 2)
    return result


class Solution:
    def maxDepthAfterSplit(self, seq: str) -> list[int]:
        return solve(seq)
