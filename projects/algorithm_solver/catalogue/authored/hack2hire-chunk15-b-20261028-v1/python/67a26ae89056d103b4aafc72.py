"""Hack2Hire 67a26ae89056d103b4aafc72 (Get Total Requests) over an INFERRED spec; qualification unknown."""


def solve(server, replaced, newId):
    count = {}
    total = 0
    for s in server:
        count[s] = count.get(s, 0) + 1
        total += s
    result = []
    for old, new in zip(replaced, newId):
        c = count.get(old, 0)
        if c and old != new:
            del count[old]
            count[new] = count.get(new, 0) + c
            total += c * (new - old)
        result.append(total)
    return result


class Solution:
    def getTotalRequests(self, server, replaced, newId):
        return solve(server, replaced, newId)
