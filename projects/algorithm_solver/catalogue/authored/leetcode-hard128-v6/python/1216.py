"""1216. Valid Palindrome III.

Minimum-deletion interval DP with a rolling row; O(n^2) time, O(n) space. Inputs are preserved.
"""

def solve(s: str, k: int) -> bool:
    n = len(s)
    deletions = [0] * n
    for left in range(n - 2, -1, -1):
        diagonal = 0
        for right in range(left + 1, n):
            old = deletions[right]
            if s[left] == s[right]:
                deletions[right] = diagonal
            else:
                deletions[right] = 1 + min(deletions[right], deletions[right - 1])
            diagonal = old
    return not s or deletions[-1] <= k


class Solution:
    def isValidPalindrome(self, s: str, k: int) -> bool:
        return solve(s, k)
