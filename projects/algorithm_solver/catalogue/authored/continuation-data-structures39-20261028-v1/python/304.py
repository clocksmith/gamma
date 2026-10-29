"""Original frontend 304 variant; qualification unknown."""


class NumMatrix:
    def __init__(self, matrix):
        m = len(matrix)
        n = len(matrix[0]) if m else 0
        pref = [[0] * (n + 1) for _ in range(m + 1)]
        for r in range(m):
            row_sum = 0
            row = matrix[r]
            prev = pref[r]
            curr = pref[r + 1]
            for c in range(n):
                row_sum += row[c]
                curr[c + 1] = prev[c + 1] + row_sum
        self.pref = pref

    def sumRegion(self, row1: int, col1: int, row2: int, col2: int) -> int:
        p = self.pref
        return p[row2 + 1][col2 + 1] - p[row1][col2 + 1] - p[row2 + 1][col1] + p[row1][col1]


def solve(operation_names, argument_lists):
    instance = NumMatrix(argument_lists[0][0])
    out = [None]
    for op, args in zip(operation_names[1:], argument_lists[1:]):
        if op == "sumRegion":
            out.append(instance.sumRegion(args[0], args[1], args[2], args[3]))
        else:
            raise ValueError("unknown operation")
    return out
