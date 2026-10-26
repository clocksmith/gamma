"""2966. Divide Array Into Arrays With Max Difference: group consecutive sorted values and reject any triple exceeding the spread limit."""


def solve(nums: list[int], k: int) -> list[list[int]]:
    """O(n log n) time and O(n) auxiliary space; inputs are read-only."""
    ordered = sorted(nums)
    groups = []
    for index in range(0, len(nums), 3):
        if ordered[index + 2] - ordered[index] > k:
            return []
        groups.append(ordered[index:index + 3])
    return groups


class Solution:
    def divideArray(self, nums: list[int], k: int) -> list[list[int]]:
        return solve(nums, k)
