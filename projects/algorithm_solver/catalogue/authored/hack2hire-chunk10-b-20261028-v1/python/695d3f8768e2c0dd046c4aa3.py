"""Hack2Hire 695d3f8768e2c0dd046c4aa3 (Find Bad GPU Nodes) over an INFERRED spec; qualification unknown."""


def solve(n, badNodes):
    flag = [False] * n
    for b in badNodes:
        flag[b] = True
    calls = 0

    def test(lo, hi):  # simulated TestServer.test over nodes lo..hi-1
        nonlocal calls
        calls += 1
        for i in range(lo, hi):
            if flag[i]:
                return False
        return True

    bad, ranges = [], [(0, n)]
    while ranges:
        lo, hi = ranges.pop()
        if test(lo, hi):
            continue
        if hi - lo == 1:
            bad.append(lo)
            continue
        mid = (lo + hi) // 2
        ranges.append((mid, hi))
        ranges.append((lo, mid))
    return [bad, calls]


class Solution:
    def findBadNodes(self, n, badNodes):
        return solve(n, badNodes)
