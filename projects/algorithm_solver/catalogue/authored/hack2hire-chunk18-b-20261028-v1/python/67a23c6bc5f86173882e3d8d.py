"""Hack2Hire 67a23c6bc5f86173882e3d8d (Regex Pattern Matching) over an INFERRED spec; qualification unknown."""


def _units(pattern):
    units = []
    i = 0
    n = len(pattern)
    while i < n:
        if pattern[i] == '(':
            j = pattern.index(')', i)
            body = pattern[i + 1:j]
            i = j + 1
        else:
            body = pattern[i]
            i += 1
        star = i < n and pattern[i] == '*'
        if star:
            i += 1
        units.append((body, star))
    return units


def solve(text, pattern):
    units = _units(pattern)
    n = len(text)
    u = len(units)
    dp = [None] * (n + 1)  # dp[i][j]: text[i:] matches units[j:]
    for i in range(n, -1, -1):
        row = [False] * (u + 1)
        row[u] = i == n
        for j in range(u - 1, -1, -1):
            body, star = units[j]
            g = len(body)
            if g == 1:
                fits = i < n and (body == '.' or body == text[i])
            else:
                fits = i + g <= n
                if fits:
                    for k in range(g):
                        c = body[k]
                        if c != '.' and c != text[i + k]:
                            fits = False
                            break
            if star:
                row[j] = row[j + 1] or (fits and dp[i + g][j])
            else:
                row[j] = fits and dp[i + g][j + 1]
        dp[i] = row
    return dp[0][0]


class Solution:
    def isMatch(self, text, pattern):
        return solve(text, pattern)
