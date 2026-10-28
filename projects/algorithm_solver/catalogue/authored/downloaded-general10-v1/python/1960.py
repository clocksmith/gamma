"""1960. Maximum Product of the Length of Two Palindromic Substrings (Hard).

Specification: https://leetcode.com/problems/maximum-product-of-the-length-of-two-palindromic-substrings/description/
"""


def solve(s: str) -> int:
    n = len(s)
    pref = [0] * n
    suff = [0] * n
    for c in range(n):
        for step in (0, 1):
            left, right = c, c + step
            while left >= 0 and right < n and s[left] == s[right]:
                length = right - left + 1
                pref[right] = max(pref[right], length)
                suff[left] = max(suff[left], length)
                left -= 1
                right += 1
    for i in range(1, n):
        pref[i] = max(pref[i], pref[i - 1])
    for i in range(n - 2, -1, -1):
        suff[i] = max(suff[i], suff[i + 1])
    best = 0
    for i in range(n - 1):
        best = max(best, pref[i] * suff[i + 1])
    return best


class Solution:
    def maxProduct(self, s: str) -> int:
        return solve(s)
