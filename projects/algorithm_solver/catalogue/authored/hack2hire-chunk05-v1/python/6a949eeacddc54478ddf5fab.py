"""Original hack2hire:6a949eeacddc54478ddf5fab; inferred public-preview contract; qualification unknown."""
def countGridSquares(queries):
    result = []
    for rows, cols in queries:
        m = min(rows, cols)
        result.append(m * (rows + 1) * (cols + 1) - (rows + cols + 2) * m * (m + 1) // 2 + m * (m + 1) * (2 * m + 1) // 6)
    return result

solve = countGridSquares

class Solution:
    countGridSquares = staticmethod(countGridSquares)
