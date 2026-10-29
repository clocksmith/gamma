"""Original frontend 267 variant; qualification unknown."""

from collections import Counter


def solve(s: str):
    cnt = Counter(s)
    odds = [ch for ch, c in cnt.items() if c & 1]
    if len(odds) > 1:
        return []
    mid = odds[0] if odds else ""
    half = sorted(ch for ch, c in cnt.items() for _ in range(c // 2))
    m = len(half)
    used = [False] * m
    res = []
    cur = []

    def backtrack():
        if len(cur) == m:
            left = "".join(cur)
            res.append(left + mid + left[::-1])
            return
        for i in range(m):
            if used[i]:
                continue
            if i > 0 and half[i] == half[i - 1] and not used[i - 1]:
                continue
            used[i] = True
            cur.append(half[i])
            backtrack()
            cur.pop()
            used[i] = False

    backtrack()
    return res


generatePalindromes = solve


class Solution:
    def generatePalindromes(self, s: str):
        return solve(s)
