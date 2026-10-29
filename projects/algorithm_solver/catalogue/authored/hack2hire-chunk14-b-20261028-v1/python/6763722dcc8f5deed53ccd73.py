"""Hack2Hire 6763722dcc8f5deed53ccd73 (Bank Service Maximization) over an INFERRED spec; qualification unknown."""


def solve(initialBalance, transactions):
    n = len(transactions)
    prefix = [0] * (n + 1)
    for k, t in enumerate(transactions):
        prefix[k + 1] = prefix[k] + t
    stack = [n]  # prefix values increase from bottom to top
    best = 0
    for s in range(n - 1, -1, -1):
        limit = prefix[s] - initialBalance
        lo, hi = 0, len(stack)
        while lo < hi:
            mid = (lo + hi) // 2
            if prefix[stack[mid]] < limit:
                lo = mid + 1
            else:
                hi = mid
        served = n - s if lo == 0 else stack[lo - 1] - 1 - s
        if served > best:
            best = served
        while stack and prefix[stack[-1]] >= prefix[s]:
            stack.pop()
        stack.append(s)
    return best


class Solution:
    def maxCustomersServed(self, initialBalance, transactions):
        return solve(initialBalance, transactions)
