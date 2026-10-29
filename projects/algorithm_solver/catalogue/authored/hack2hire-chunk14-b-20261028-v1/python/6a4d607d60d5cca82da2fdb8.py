"""Hack2Hire 6a4d607d60d5cca82da2fdb8 (Beam Search Decoding, variant 1 of 2) over an INFERRED spec; qualification unknown."""


def solve(scores):
    out = []
    for row in scores:
        best = 0
        for j in range(1, len(row)):
            if row[j] > row[best]:
                best = j
        out.append(best)
    return out


class Solution:
    def greedyDecode(self, scores):
        return solve(scores)
