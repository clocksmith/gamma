"""132. Palindrome Partitioning II."""
def solve(s: str) -> int:
    if not s:
        return 0
    size = len(s)
    palindrome = [[False] * size for _ in range(size)]
    cuts = [0] * size
    for end in range(size):
        best = end
        for start in range(end + 1):
            if s[start] == s[end] and (end - start <= 2 or palindrome[start + 1][end - 1]):
                palindrome[start][end] = True
                best = 0 if start == 0 else min(best, cuts[start - 1] + 1)
        cuts[end] = best
    return cuts[-1]

class Solution:
    def minCut(self, s: str) -> int:
        return solve(s)
