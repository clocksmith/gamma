"""Original frontend 1428 variant; qualification unknown."""


def solve(binaryMatrix) -> int:
    if hasattr(binaryMatrix, "dimensions"):
        rows, cols = binaryMatrix.dimensions()
        get = binaryMatrix.get
    else:
        rows, cols = len(binaryMatrix), len(binaryMatrix[0])
        get = lambda r, c: binaryMatrix[r][c]
    r, c = 0, cols - 1
    ans = -1
    while r < rows and c >= 0:
        if get(r, c) == 1:
            ans = c
            c -= 1
        else:
            r += 1
    return ans


leftMostColumnWithOne = solve


class Solution:
    def leftMostColumnWithOne(self, binaryMatrix) -> int:
        return solve(binaryMatrix)
