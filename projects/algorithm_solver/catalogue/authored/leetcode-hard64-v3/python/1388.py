"""1388. Pizza With 3n Slices: two linear exact-cardinality independent-set DPs; O(n^2) time and O(n) space."""


def solve(slices: list[int]) -> int:
    required = len(slices) // 3

    def linear(values: list[int]) -> int:
        previous = [0] + [float('-inf')] * required
        before_previous = previous[:]
        for value in values:
            current = previous[:]
            for count in range(1, required + 1):
                current[count] = max(previous[count], before_previous[count - 1] + value)
            before_previous, previous = previous, current
        return previous[required]

    return max(linear(slices[:-1]), linear(slices[1:]))


class Solution:
    def maxSizeSlices(self, slices: list[int]) -> int:
        return solve(slices)
