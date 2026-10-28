"""1717. Maximum Score From Removing Substrings (Medium).

Specification: https://leetcode.com/problems/maximum-score-from-removing-substrings/description/
"""


def remove_pair(s: str, first: str, second: str, gain: int) -> tuple[str, int]:
    stack = []
    total = 0
    for ch in s:
        if stack and stack[-1] == first and ch == second:
            stack.pop()
            total += gain
        else:
            stack.append(ch)
    return "".join(stack), total


def solve(s: str, x: int, y: int) -> int:
    if x >= y:
        rest, total = remove_pair(s, 'a', 'b', x)
        _, second = remove_pair(rest, 'b', 'a', y)
    else:
        rest, total = remove_pair(s, 'b', 'a', y)
        _, second = remove_pair(rest, 'a', 'b', x)
    return total + second


class Solution:
    def maximumGain(self, s: str, x: int, y: int) -> int:
        return solve(s, x, y)
