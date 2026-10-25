"""10. Regular Expression Matching (Hard).

Fresh candidate authored in this conversation; no repository solution copied.
Specification: https://leetcode.com/problems/regular-expression-matching/description/
Canonical API: solve(s, p); also exposes Solution.isMatch.
Inputs are preserved. Gamma independent qualification is pending.
"""

def solve(s: str, p: str) -> bool:
    pattern_length = len(p)
    previous = [False] * (pattern_length + 1)
    previous[0] = True
    for column in range(2, pattern_length + 1):
        if p[column - 1] == "*":
            previous[column] = previous[column - 2]

    for row in range(1, len(s) + 1):
        current = [False] * (pattern_length + 1)
        for column in range(1, pattern_length + 1):
            if p[column - 1] == "*":
                atom = p[column - 2]
                matches = atom == "." or atom == s[row - 1]
                current[column] = current[column - 2] or (
                    matches and previous[column]
                )
            else:
                matches = p[column - 1] == "." or p[column - 1] == s[row - 1]
                current[column] = matches and previous[column - 1]
        previous = current
    return previous[pattern_length]

class Solution:
    def isMatch(self, s: str, p: str) -> bool:
        return solve(s, p)
