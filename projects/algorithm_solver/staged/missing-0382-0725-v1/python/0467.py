"""467. Unique Substrings in Wraparound String."""

def solve(s: str) -> int:
    best = [0] * 26
    run = 0
    for i, char in enumerate(s):
        index = ord(char) - 97
        if i and (ord(char) - ord(s[i - 1])) % 26 == 1:
            run += 1
        else:
            run = 1
        best[index] = max(best[index], run)
    return sum(best)


class Solution:
    def findSubstringInWraproundString(self, s: str) -> int:
        return solve(s)
