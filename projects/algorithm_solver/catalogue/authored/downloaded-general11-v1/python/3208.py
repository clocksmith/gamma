"""3208. Alternating Groups II (Medium).

Specification: https://leetcode.com/problems/alternating-groups-ii/description/
"""


def solve(colors: list[int], k: int) -> int:
    n = len(colors)
    ans = 0
    for i in range(n):
        ok = True
        for j in range(k - 1):
            if colors[(i + j) % n] == colors[(i + j + 1) % n]:
                ok = False
                break
        if ok:
            ans += 1
    return ans


class Solution:
    def numberOfAlternatingGroups(self, colors, k):
        return solve(colors, k)
