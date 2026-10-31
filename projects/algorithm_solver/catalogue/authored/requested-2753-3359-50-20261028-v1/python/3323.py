"""Original frontend 3323 variant; qualification unknown."""


def solve(intervals, k: int) -> int:
    arr = sorted(intervals)
    merged = []
    for s, e in arr:
        if not merged or s > merged[-1][1]:
            merged.append([s, e])
        elif e > merged[-1][1]:
            merged[-1][1] = e
    m = len(merged)
    max_bridge = 0
    r = 0
    for l in range(m):
        while r < m and merged[r][0] <= merged[l][1] + k:
            r += 1
        if r - 1 - l > max_bridge:
            max_bridge = r - 1 - l
    return m - max_bridge


minConnectedGroups = solve


class Solution:
    def minConnectedGroups(self, intervals, k: int) -> int:
        return solve(intervals, k)
