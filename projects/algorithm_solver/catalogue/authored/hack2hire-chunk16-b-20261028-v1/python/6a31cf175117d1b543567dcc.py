"""Hack2Hire 6a31cf175117d1b543567dcc (Merge Values into Blocks) over an INFERRED spec; qualification unknown."""


def solve(arr):
    last = {}
    for i, v in enumerate(arr):
        last[v] = i
    pieces = 0
    reach = -1
    for i, v in enumerate(arr):
        if last[v] > reach:
            reach = last[v]
        if reach == i:
            pieces += 1
    return len(last) - pieces


class Solution:
    def minOperations(self, arr):
        return solve(arr)
