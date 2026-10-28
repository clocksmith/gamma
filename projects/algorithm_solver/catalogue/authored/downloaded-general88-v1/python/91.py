"""91. Decode Ways (Medium).

Specification: https://leetcode.com/problems/decode-ways/description/
"""


def solve(s: str) -> int:
    if s[0] == '0':
        return 0
    previous = 1
    current = 1
    for i in range(1, len(s)):
        nxt = 0
        if s[i] != '0':
            nxt += current
        two = int(s[i - 1:i + 1])
        if 10 <= two <= 26:
            nxt += previous
        previous, current = current, nxt
    return current


class Solution:
    def numDecodings(self, s: str) -> int:
        return solve(s)
