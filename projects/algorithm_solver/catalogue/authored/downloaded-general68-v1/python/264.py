"""264. Ugly Number II (Medium).

Specification: https://leetcode.com/problems/ugly-number-ii/description/
"""


def solve(n: int) -> int:
    ugly = [1]
    i2 = i3 = i5 = 0
    while len(ugly) < n:
        nxt = min(ugly[i2] * 2, ugly[i3] * 3, ugly[i5] * 5)
        ugly.append(nxt)
        if nxt == ugly[i2] * 2:
            i2 += 1
        if nxt == ugly[i3] * 3:
            i3 += 1
        if nxt == ugly[i5] * 5:
            i5 += 1
    return ugly[n - 1]


class Solution:
    def nthUglyNumber(self, n: int) -> int:
        return solve(n)
