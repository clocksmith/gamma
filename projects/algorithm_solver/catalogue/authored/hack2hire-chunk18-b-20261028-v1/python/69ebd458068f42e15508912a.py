"""Hack2Hire 69ebd458068f42e15508912a (Optimize Transition from Elevator to Stairs) over an INFERRED spec; qualification unknown."""


def _stairs(energy, floors, e2, c, limit):
    # stair time from the given energy, stopping early once it reaches limit
    total = 0
    for _ in range(floors):
        total += -(-c // energy)
        if total >= limit:
            return total
        energy -= e2
    return total


def solve(n, e1, t1, e2, c):
    def feasible(k):
        return k == n or k * e1 - (n - k - 1) * e2 > 0
    lo, hi = 0, n
    while lo < hi:
        mid = (lo + hi) // 2
        if feasible(mid):
            hi = mid
        else:
            lo = mid + 1
    best = n * t1
    for k in range(lo, n):
        if k * t1 + (n - k) >= best:
            break
        total = k * t1 + _stairs(k * e1, n - k, e2, c, best - k * t1)
        if total < best:
            best = total
    return best


class Solution:
    def minimumTotalTime(self, n, e1, t1, e2, c):
        return solve(n, e1, t1, e2, c)
