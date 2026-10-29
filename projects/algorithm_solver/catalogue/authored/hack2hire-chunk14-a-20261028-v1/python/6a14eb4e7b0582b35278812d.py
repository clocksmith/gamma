"""Hack2Hire 6a14eb4e7b0582b35278812d (String Matches in Matrix) over an INFERRED spec; qualification unknown."""


def solve(matrix, s):
    m, n, k = len(matrix), len(matrix[0]), len(s)
    fail = [0] * k
    j = 0
    for i in range(1, k):
        while j and s[i] != s[j]:
            j = fail[j - 1]
        if s[i] == s[j]:
            j += 1
        fail[i] = j

    def occurrences(line):
        found = state = 0
        for ch in line:
            while state and ch != s[state]:
                state = fail[state - 1]
            if ch == s[state]:
                state += 1
            if state == k:
                found += 1
                state = fail[state - 1]
        return found

    total = 0
    if k <= n:
        for row in matrix:
            total += occurrences(row)
    if k <= m:
        for c in range(n):
            total += occurrences(''.join(row[c] for row in matrix))
    if k <= m and k <= n:
        starts = [(0, c) for c in range(n)] + [(r, 0) for r in range(1, m)]
        for r, c in starts:
            length = min(m - r, n - c)
            if length >= k:
                total += occurrences(''.join(matrix[r + i][c + i] for i in range(length)))
    return total


class Solution:
    def countMatches(self, matrix, s):
        return solve(matrix, s)
