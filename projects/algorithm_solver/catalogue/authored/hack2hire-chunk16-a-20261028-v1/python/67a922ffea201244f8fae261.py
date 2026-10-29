"""Hack2Hire 67a922ffea201244f8fae261 (Longest Prefix And Suffix) over an INFERRED spec; qualification unknown."""


def solve(s):
    n = len(s)
    pi = [0] * n
    k = 0
    for i in range(1, n):
        while k and s[i] != s[k]:
            k = pi[k - 1]
        if s[i] == s[k]:
            k += 1
        pi[i] = k
    return pi[-1]


class Solution:
    def longestPrefixSuffix(self, s):
        return solve(s)
