"""1815. Maximum Number of Groups Getting Fresh Donuts.

Remove zero/complement remainders, then memoize remaining remainder counts. O(b^2*S+n) time, O(b*S+n) space; S is the count-state space. Inputs are preserved.
"""

from functools import lru_cache


def solve(batchSize: int, groups: list[int]) -> int:
    counts = [0] * batchSize
    for value in groups:
        counts[value % batchSize] += 1
    answer = counts[0]
    counts[0] = 0
    for remainder in range(1, (batchSize + 1) // 2):
        pairs = min(counts[remainder], counts[batchSize - remainder])
        counts[remainder] -= pairs
        counts[batchSize - remainder] -= pairs
        answer += pairs
    if batchSize % 2 == 0:
        pairs = counts[batchSize // 2] // 2
        answer += pairs
        counts[batchSize // 2] %= 2

    @lru_cache(None)
    def best(state, remainder):
        result = 0
        for value in range(1, batchSize):
            if state[value]:
                following = list(state)
                following[value] -= 1
                result = max(result, (remainder == 0) + best(tuple(following), (remainder + value) % batchSize))
        return result

    return answer + best(tuple(counts), 0)


class Solution:
    def maxHappyGroups(self, batchSize: int, groups: list[int]) -> int:
        return solve(batchSize, groups)
