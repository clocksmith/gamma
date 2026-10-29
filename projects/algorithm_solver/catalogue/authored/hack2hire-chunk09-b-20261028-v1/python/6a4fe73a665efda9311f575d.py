"""Hack2Hire 6a4fe73a665efda9311f575d (Count Maximum Borrowing Days) over an INFERRED spec; qualification unknown."""


def solve(lend, payback):
    n = len(lend)
    if n == 0:
        return 0
    order = sorted(range(n), key=lambda i: payback[i])  # bit b is the lender with the b-th smallest payback
    a = [lend[i] for i in order]
    b = [payback[i] for i in order]
    succ = [0] * n
    for i in range(n):
        mask = 0
        for j in range(n):
            if a[j] >= b[i]:
                mask |= 1 << j
        succ[i] = mask
    full = 1 << n
    reach = [0] * full
    for i in range(n):
        reach[1 << i] = 1 << i
    best = 1
    for mask in range(1, full):
        r = reach[mask]
        if not r:
            continue
        size = bin(mask).count('1')
        if size > best:
            best = size
        # the union of successors of every possible last lender is the successors of the one with the smallest payback
        nxt = succ[(r & -r).bit_length() - 1] & ~mask
        while nxt:
            bit = nxt & -nxt
            reach[mask | bit] |= bit
            nxt ^= bit
    return best


class Solution:
    def maxBorrowingDays(self, lend, payback):
        return solve(lend, payback)
