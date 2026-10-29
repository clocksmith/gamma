"""Hack2Hire 699926ca6e73e4abccc9a376 (Warehouse Package Allocation) over an INFERRED spec; qualification unknown."""


def solve(centerCapacity, dailyLog):
    n = len(centerCapacity)
    nxt = [(i + 1) % n for i in range(n)]
    prv = [(i - 1) % n for i in range(n)]
    got = [0] * n
    cur = 0
    used = 0
    for entry in dailyLog:
        if entry == 'PACKAGE':
            got[cur] += 1
            used += 1
            if used == centerCapacity[cur]:
                cur = nxt[cur]
                used = 0
        else:
            i = int(entry[8:])
            p, q = prv[i], nxt[i]
            nxt[p] = q
            prv[q] = p
            if i == cur:
                cur = q
                used = 0
    best = 0
    for i in range(1, n):
        if got[i] >= got[best]:
            best = i
    return best


class Solution:
    def busiestCenter(self, centerCapacity, dailyLog):
        return solve(centerCapacity, dailyLog)
