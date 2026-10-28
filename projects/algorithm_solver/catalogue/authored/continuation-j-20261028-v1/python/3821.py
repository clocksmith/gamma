"""Original frontend 3821 variant; qualification unknown."""

def solve(n, k):
    from math import comb
    answer = 0
    remaining = k
    for bit in range(49, -1, -1):
        zero_count = comb(bit, remaining) if 0 <= remaining <= bit else 0
        if n > zero_count:
            answer += 2**bit
            n -= zero_count
            remaining -= 1
    return answer


class Solution:
    def nthSmallest(self, n, k):
        return solve(n, k)
