"""Hack2Hire 67df6ae706b62d81733ab893 (Merge Two Interval Lists) over an INFERRED spec; qualification unknown."""


def solve(list1, list2):
    out = []
    i = j = 0
    while i < len(list1) or j < len(list2):
        if j >= len(list2) or (i < len(list1) and list1[i][0] <= list2[j][0]):
            start, end = list1[i]
            i += 1
        else:
            start, end = list2[j]
            j += 1
        if out and start <= out[-1][1]:
            if end > out[-1][1]:
                out[-1][1] = end
        else:
            out.append([start, end])
    return out


class Solution:
    def mergeIntervalLists(self, list1, list2):
        return solve(list1, list2)
