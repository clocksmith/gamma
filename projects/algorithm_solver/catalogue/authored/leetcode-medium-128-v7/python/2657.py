"""2657. Find the Prefix Common Array of Two Arrays: count each permutation value when its second cross-array occurrence arrives."""


def solve(A: list[int], B: list[int]) -> list[int]:
    """O(n) time and O(n) auxiliary space; inputs are read-only."""
    counts = [0] * (len(A) + 1)
    common = 0
    result = []
    for left, right in zip(A, B):
        counts[left] += 1
        if counts[left] == 2:
            common += 1
        counts[right] += 1
        if counts[right] == 2:
            common += 1
        result.append(common)
    return result


class Solution:
    def findThePrefixCommonArray(self, A: list[int], B: list[int]) -> list[int]:
        return solve(A, B)
