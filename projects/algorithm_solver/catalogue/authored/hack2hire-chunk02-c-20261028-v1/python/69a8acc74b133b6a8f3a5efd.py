"""Hack2Hire 69a8acc74b133b6a8f3a5efd (Crypto Block Mining, variant 2) over an INFERRED spec; qualification unknown."""

SIZE_SCALE = 8192  # key = fee * SIZE_SCALE - size; total size <= blockSize <= 5000 < SIZE_SCALE


def solve(transactions, blockSize):
    n = len(transactions)
    best = [[0] * (blockSize + 1) for _ in range(n + 1)]  # best[i][c]: best key using transactions i.. within c
    for i in range(n - 1, -1, -1):
        _, size, fee = transactions[i]
        key, here, after = fee * SIZE_SCALE - size, best[i], best[i + 1]
        for capacity in range(blockSize + 1):
            value = after[capacity]
            if size <= capacity and after[capacity - size] + key > value:
                value = after[capacity - size] + key
            here[capacity] = value
    chosen, capacity = [], blockSize
    for i in range(n):
        _, size, fee = transactions[i]
        if size <= capacity and best[i + 1][capacity - size] + fee * SIZE_SCALE - size == best[i][capacity]:
            chosen.append(transactions[i][0])
            capacity -= size
    return chosen


class Solution:
    def selectTransactions(self, transactions, blockSize):
        return solve(transactions, blockSize)
