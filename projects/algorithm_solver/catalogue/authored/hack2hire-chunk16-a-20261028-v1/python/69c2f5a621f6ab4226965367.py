"""Hack2Hire 69c2f5a621f6ab4226965367 (Grep With Context Lines, variant 2 of 2) over an INFERRED spec; qualification unknown."""


def solve(lines, target, before, after):
    n = len(lines)
    blocks = []
    next_index = 0
    for j in range(n):
        if target not in lines[j]:
            continue
        start = j - before
        if start < 0:
            start = 0
        stop = min(n, j + after + 1)
        if stop <= next_index:
            continue
        if start > next_index or not blocks:
            blocks.append([])
        else:
            start = next_index
        block = blocks[-1]
        for i in range(start, stop):
            block.append(lines[i])
        next_index = stop
    return blocks


class Solution:
    def grepWithContextBlocks(self, lines, target, before, after):
        return solve(lines, target, before, after)
