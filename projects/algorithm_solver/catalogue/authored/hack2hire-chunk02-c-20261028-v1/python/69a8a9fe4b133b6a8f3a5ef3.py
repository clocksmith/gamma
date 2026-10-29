"""Hack2Hire 69a8a9fe4b133b6a8f3a5ef3 (Crypto Block Mining, variant 1) over an INFERRED spec; qualification unknown."""

def solve(transactions, blockSize):
    best = [0] * (blockSize + 1)
    for _, size, fee in transactions:
        for capacity in range(blockSize, size - 1, -1):
            candidate = best[capacity - size] + fee
            if candidate > best[capacity]:
                best[capacity] = candidate
    return best[blockSize]


class Solution:
    def maxFees(self, transactions, blockSize):
        return solve(transactions, blockSize)
