"""392. Is Subsequence. Advance through the candidate subsequence once."""

def solve(s: str, t: str) -> bool:
    index = 0
    for char in t:
        if index < len(s) and s[index] == char:
            index += 1
    return index == len(s)


class Solution:
    def isSubsequence(self, s: str, t: str) -> bool:
        return solve(s, t)
