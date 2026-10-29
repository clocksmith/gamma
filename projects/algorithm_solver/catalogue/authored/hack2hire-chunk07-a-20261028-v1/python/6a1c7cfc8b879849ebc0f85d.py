"""Hack2Hire 6a1c7cfc8b879849ebc0f85d (Max Matrix Border Distinct Sum) over an INFERRED spec; qualification unknown."""

def solve(matrix, frameSize):
    k, m, n = frameSize, len(matrix), len(matrix[0])
    best = None
    for r in range(m - k + 1):
        top, bottom = matrix[r], matrix[r + k - 1]
        for c in range(n - k + 1):
            seen = set(top[c:c + k])
            seen.update(bottom[c:c + k])
            for i in range(r + 1, r + k - 1):
                seen.add(matrix[i][c])
                seen.add(matrix[i][c + k - 1])
            score = sum(seen)
            if best is None or score > best:
                best = score
    return best


class Solution:
    def maxFrameDistinctSum(self, matrix, frameSize):
        return solve(matrix, frameSize)
