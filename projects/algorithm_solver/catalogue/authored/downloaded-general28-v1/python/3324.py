"""3324. Find the Sequence of Strings Appeared on the Screen (Medium).

Specification: https://leetcode.com/problems/find-the-sequence-of-strings-appeared-on-the-screen/description/
"""


def solve(target: str) -> list[str]:
    out = []
    s = ''
    for c in target:
        for code in range(97, ord(c) + 1):
            out.append(s + chr(code))
        s = s + c
    return out


class Solution:
    def stringSequence(self, target: str) -> list[str]:
        return solve(target)
