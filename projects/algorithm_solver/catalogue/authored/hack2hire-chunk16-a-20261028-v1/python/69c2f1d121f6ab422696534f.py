"""Hack2Hire 69c2f1d121f6ab422696534f (Grep With Context Lines, variant 1 of 2) over an INFERRED spec; qualification unknown."""


def solve(lines, target, linesAround):
    n = len(lines)
    out = []
    next_index = 0
    for j in range(n):
        if target not in lines[j]:
            continue
        start = max(next_index, j - linesAround)
        stop = min(n, j + linesAround + 1)
        for i in range(start, stop):
            out.append(lines[i])
        if stop > next_index:
            next_index = stop
    return out


class Solution:
    def grepWithContext(self, lines, target, linesAround):
        return solve(lines, target, linesAround)
