from math import isqrt

def solve(n, k):
    best = [1]*(k-1)+[n]
    best_gap = n-1
    path = []
    def visit(remaining, slots, lower):
        nonlocal best, best_gap
        if slots == 1:
            if remaining >= lower:
                row = path+[remaining]
                gap = row[-1]-row[0]
                if gap < best_gap: best, best_gap = row, gap
            return
        limit = isqrt(remaining)
        for factor in range(lower, limit+1):
            if factor**slots > remaining: break
            if remaining % factor == 0:
                path.append(factor)
                visit(remaining//factor, slots-1, factor)
                path.pop()
    visit(n, k, 1)
    return best

class Solution:
    def minDifference(self, n, k):
        return solve(n, k)
