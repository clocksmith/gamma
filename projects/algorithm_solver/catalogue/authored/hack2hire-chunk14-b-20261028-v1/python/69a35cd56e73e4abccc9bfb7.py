"""Hack2Hire 69a35cd56e73e4abccc9bfb7 (Apply Binary Array Operations) over an INFERRED spec; qualification unknown."""

import heapq


def solve(arr, ops):
    a = list(arr)
    zeros = [i for i, v in enumerate(a) if v == 0]
    for op in ops:
        if op == '1':
            while zeros and a[zeros[0]] == 1:
                heapq.heappop(zeros)
            if zeros:
                a[heapq.heappop(zeros)] = 1
        else:
            i = int(op[2:])
            if a[i] == 1:
                a[i] = 0
                heapq.heappush(zeros, i)
    return a


class Solution:
    def applyOperations(self, arr, ops):
        return solve(arr, ops)
