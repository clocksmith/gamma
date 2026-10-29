"""Hack2Hire 69bd5fda1cbff60a929be96f (Implement Simplified Git Diff, level 1) over an INFERRED spec; qualification unknown."""


def solve(lines1, lines2):
    count1, count2, where = {}, {}, {}
    for line in lines1:
        count1[line] = count1.get(line, 0) + 1
    for j, line in enumerate(lines2):
        count2[line] = count2.get(line, 0) + 1
        where[line] = j
    for i, line in enumerate(lines1):
        if count1[line] == 1 and count2.get(line) == 1:
            return [i, where[line]]
    return [-1, -1]


class Solution:
    def findUniqueCommonLine(self, lines1, lines2):
        return solve(lines1, lines2)
