"""521. Longest Uncommon Subsequence I."""

def solve(a: str, b: str) -> int:
    return -1 if a == b else max(len(a), len(b))


class Solution:
    def findLUSlength(self, a: str, b: str) -> int:
        return solve(a, b)
