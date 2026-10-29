"""Hack2Hire 6800861ac48db1937ce88f5d (Merge Common Substring) over an INFERRED spec; qualification unknown."""


def solve(str1, str2):
    m = min(len(str1), len(str2))
    text = str2 + '#' + str1[len(str1) - m:]
    pi = [0] * len(text)
    k = 0
    for i in range(1, len(text)):
        while k and text[i] != text[k]:
            k = pi[k - 1]
        if text[i] == text[k]:
            k += 1
        pi[i] = k
    return str1 + str2[pi[-1]:]


class Solution:
    def mergeCommonSubstring(self, str1, str2):
        return solve(str1, str2)
