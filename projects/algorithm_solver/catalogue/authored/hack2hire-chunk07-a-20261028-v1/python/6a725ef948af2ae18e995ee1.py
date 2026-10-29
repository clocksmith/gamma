"""Hack2Hire 6a725ef948af2ae18e995ee1 (Maximum Bounded XOR) over an INFERRED spec; qualification unknown."""

def solve(lo, hi, k):
    memo = {}

    def best(bit, alo, ahi, blo, bhi, kt, lt):
        if bit < 0:
            return 0 if lt else -1
        key = (bit, alo, ahi, blo, bhi, kt, lt)
        if key in memo:
            return memo[key]
        lb, hb, kb = lo >> bit & 1, hi >> bit & 1, k >> bit & 1
        result = -1
        for x in (1, 0):
            if kt and x > kb:
                continue
            for abit in (0, 1):
                bbit = abit ^ x
                if (not lt and abit > bbit) or (alo and abit < lb) or (ahi and abit > hb) or (blo and bbit < lb) or (bhi and bbit > hb):
                    continue
                sub = best(bit - 1, alo and abit == lb, ahi and abit == hb, blo and bbit == lb, bhi and bbit == hb,
                           kt and x == kb, lt or abit < bbit)
                if sub >= 0 and (x << bit) + sub > result:
                    result = (x << bit) + sub
            if result >= 0:
                break  # an XOR bit of 1 beats every completion with 0 here
        memo[key] = result
        return result

    return best(30, True, True, True, True, True, False)


class Solution:
    def maxBoundedXor(self, lo, hi, k):
        return solve(lo, hi, k)
