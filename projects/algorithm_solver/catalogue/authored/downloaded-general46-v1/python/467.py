"""467. Unique Substrings in Wraparound String (Medium).

Specification: https://leetcode.com/problems/unique-substrings-in-wraparound-string/description/
"""


def solve(s: str) -> int:
    best = {}
    run = 0
    for i, ch in enumerate(s):
        if i > 0 and (ord(ch) - ord(s[i - 1]) == 1 or (s[i - 1] == 'z' and ch == 'a')):
            run += 1
        else:
            run = 1
        best[ch] = max(best.get(ch, 0), run)
    return sum(best.values())


class Solution:
    def findSubstringInWraproundString(self, s: str) -> int:
        return solve(s)
