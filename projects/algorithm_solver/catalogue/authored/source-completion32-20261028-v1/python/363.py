# 363 — Max Sum of Rectangle No Larger Than K. Original implementation; authored candidate, not independently qualified.
def solve(matrix, k):
    from bisect import bisect_left, insort
    if len(matrix) > len(matrix[0]):
        matrix = list(zip(*matrix))
    rows, cols = len(matrix), len(matrix[0])
    best = float('-inf')
    for top in range(rows):
        sums = [0] * cols
        for bottom in range(top, rows):
            for c in range(cols):
                sums[c] += matrix[bottom][c]
            prefixes, current = [0], 0
            for value in sums:
                current += value
                i = bisect_left(prefixes, current - k)
                if i < len(prefixes):
                    best = max(best, current - prefixes[i])
                    if best == k:
                        return k
                insort(prefixes, current)
    return best

maxSumSubmatrix = solve

class Solution:
    maxSumSubmatrix = staticmethod(solve)
