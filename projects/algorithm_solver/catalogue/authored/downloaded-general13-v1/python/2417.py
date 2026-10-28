"""2417. Closest Fair Integer (Medium).

Specification: https://leetcode.com/problems/closest-fair-integer/description/
"""


def solve(n):
    def is_fair(x):
        s = str(x)
        if len(s) % 2 == 1:
            return False
        odd = sum(1 for ch in s if int(ch) % 2 == 1)
        even = len(s) - odd
        return odd == even
    n0 = n
    while True:
        if is_fair(n0):
            return n0
        k = len(str(n0))
        if k % 2 == 1:
            ones = '1' * (k // 2)
            return 10 ** k + (int(ones) if ones else 0)
        n0 += 1


class Solution:
    def closestFair(self, n):
        return solve(n)
