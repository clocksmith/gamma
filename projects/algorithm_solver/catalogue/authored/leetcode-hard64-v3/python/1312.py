"""1312. Minimum Insertion Steps to Make a String Palindrome: rolling interval dynamic programming; O(n^2) time and O(n) space."""


def solve(s: str) -> int:
    best = [0] * len(s)
    for left in range(len(s) - 2, -1, -1):
        diagonal = 0
        for right in range(left + 1, len(s)):
            previous = best[right]
            if s[left] == s[right]:
                best[right] = diagonal
            else:
                best[right] = 1 + min(best[right], best[right - 1])
            diagonal = previous
    return best[-1] if best else 0


class Solution:
    def minInsertions(self, s: str) -> int:
        return solve(s)
