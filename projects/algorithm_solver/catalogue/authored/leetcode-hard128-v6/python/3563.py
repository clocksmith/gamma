"""3563. Lexicographically Smallest String After Adjacent Removals.

Interval dynamic programming recognizes erasable substrings; suffix choices select the lexicographically smallest remainder; O(n^3) time and O(n^2) space. Input is preserved.
"""

def solve(s: str) -> str:
    n = len(s)
    erased = [bytearray(n + 1) for _ in range(n + 1)]
    for index in range(n + 1):
        erased[index][index] = 1
    for length in range(2, n + 1, 2):
        for start in range(n - length + 1):
            end = start + length
            for partner in range(start + 1, end, 2):
                difference = abs(ord(s[start]) - ord(s[partner]))
                if difference in (1, 25) and erased[start + 1][partner] and erased[partner + 1][end]:
                    erased[start][end] = 1
                    break
    best = [''] * (n + 1)
    for start in range(n - 1, -1, -1):
        candidate = s[start] + best[start + 1]
        for end in range(start + 2, n + 1, 2):
            if erased[start][end] and best[end] < candidate:
                candidate = best[end]
        best[start] = candidate
    return best[0]


class Solution:
    def lexicographicallySmallestString(self, s: str) -> str:
        return solve(s)
