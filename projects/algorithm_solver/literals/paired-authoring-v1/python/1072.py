class Solution:
    def maxEqualRowsAfterFlips(self, matrix: list[list[int]]) -> int:
        frequencies = {}
        best = 0
        for row in matrix:
            pattern = []
            for value in row:
                pattern.append("0" if value == row[0] else "1")
            key = "".join(pattern)
            frequencies[key] = frequencies.get(key, 0) + 1
            best = max(best, frequencies[key])
        return best
