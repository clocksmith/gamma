"""Hack2Hire 67888093402dc47b67a14948 (Number of Idle Drives) over an INFERRED spec; qualification unknown."""


def solve(x, y):
    column = {}
    row = {}
    for a, b in zip(x, y):
        c = column.get(a)
        if c is None:
            column[a] = [b, b]
        else:
            if b < c[0]:
                c[0] = b
            if b > c[1]:
                c[1] = b
        r = row.get(b)
        if r is None:
            row[b] = [a, a]
        else:
            if a < r[0]:
                r[0] = a
            if a > r[1]:
                r[1] = a
    count = 0
    for a, b in zip(x, y):
        c = column[a]
        r = row[b]
        if c[0] < b < c[1] and r[0] < a < r[1]:
            count += 1
    return count


class Solution:
    def countIdleDrives(self, x, y):
        return solve(x, y)
