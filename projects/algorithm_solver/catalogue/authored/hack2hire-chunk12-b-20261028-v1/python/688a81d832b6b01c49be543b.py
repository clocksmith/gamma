"""Hack2Hire 688a81d832b6b01c49be543b (Minimal Difference in Two Arrays) over an INFERRED spec; qualification unknown."""


def solve(A, B):
    i = j = 0
    best = abs(A[0] - B[0])
    while i < len(A) and j < len(B) and best > 0:
        d = A[i] - B[j]
        if abs(d) < best:
            best = abs(d)
        if d < 0:
            i += 1
        else:
            j += 1
    low = high = 0
    for a in A:
        while low < len(B) and B[low] < a - best:
            low += 1
        if low < len(B) and B[low] == a - best:
            return [a, a - best]
        while high < len(B) and B[high] < a + best:
            high += 1
        if high < len(B) and B[high] == a + best:
            return [a, a + best]
    raise AssertionError('minimum difference not found')


class Solution:
    def findMinAbsDiffPair(self, A, B):
        return solve(A, B)
