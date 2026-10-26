"""2178. Maximum Split of Positive Even Integers: take the smallest unused even values and add the final remainder to the largest."""


def solve(finalSum: int) -> list[int]:
    """O(sqrt(S)) time and result space for S = finalSum; inputs are read-only."""
    if finalSum % 2:
        return []
    remaining = finalSum
    result = []
    value = 2
    while remaining >= value:
        result.append(value)
        remaining -= value
        value += 2
    if remaining:
        result[-1] += remaining
    return result


class Solution:
    def maximumEvenSplit(self, finalSum: int) -> list[int]:
        return solve(finalSum)
