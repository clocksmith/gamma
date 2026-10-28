"""1576. Replace All ?'s to Avoid Consecutive Repeating Characters (Medium).

Specification: https://leetcode.com/problems/replace-all-s-to-avoid-consecutive-repeating-characters/description/
"""


def solve(s: str) -> str:
    chars = list(s)
    for i in range(len(chars)):
        if chars[i] != '?':
            continue
        for candidate in ('a', 'b', 'c'):
            left = chars[i - 1] if i > 0 else ''
            right = chars[i + 1] if i + 1 < len(chars) else ''
            if candidate != left and candidate != right:
                chars[i] = candidate
                break
    return "".join(chars)


class Solution:
    def modifyString(self, s: str) -> str:
        return solve(s)
