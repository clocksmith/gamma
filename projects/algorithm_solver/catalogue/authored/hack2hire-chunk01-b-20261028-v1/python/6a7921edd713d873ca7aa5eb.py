"""Hack2Hire 6a7921edd713d873ca7aa5eb (Find Missing Subsequence Words). Spec inferred by claude-opus-5-5 subagent 2026-10-28; qualification unknown."""


def solve(s, t):
    words = s.split(' ')
    wanted = t.split(' ') if t else []
    missing, j = [], 0
    for word in words:
        if j < len(wanted) and word == wanted[j]:
            j += 1
        else:
            missing.append(word)
    return missing


class Solution:
    def findMissingWords(self, s, t):
        return solve(s, t)
