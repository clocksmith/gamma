"""Hack2Hire 6a226625981072682a6f216b (Matrix Transpose with Workers); INFERRED spec, workers simulated deterministically; qualification unknown."""


def solve(matrix, numThreads):
    n = len(matrix)
    workers = min(numThreads, n)
    out = [None] * n
    base, extra = divmod(n, workers)
    start = 0
    for worker in range(workers):  # each simulated worker owns a contiguous block of output rows
        stop = start + base + (1 if worker < extra else 0)
        for j in range(start, stop): out[j] = [row[j] for row in matrix]
        start = stop
    return out


class Solution:
    def transposeWithWorkers(self, matrix, numThreads):
        return solve(matrix, numThreads)
