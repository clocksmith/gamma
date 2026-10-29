"""Original Hack2Hire 6945ada2e85c245612a97880 variant over an INFERRED specification; qualification unknown."""


def solve(relationships, first, second):
    manager = {}
    for row in relationships:
        for report in row[1:]:
            manager[report] = row[0]

    def depth(name):
        d = 0
        while name in manager:
            name = manager[name]
            d += 1
        return d
    a, b = first, second
    da, db = depth(a), depth(b)
    while da > db:
        a, da = manager[a], da - 1
    while db > da:
        b, db = manager[b], db - 1
    while a != b:
        a, b = manager[a], manager[b]
    return a


class Solution:
    def closestCommonManager(self, relationships, first, second):
        return solve(relationships, first, second)
