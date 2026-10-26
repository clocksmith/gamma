"""2948. Make Lexicographically Smallest Array by Swapping Elements: assign each connected value group in sorted order to its sorted original positions."""


def solve(nums: list[int], limit: int) -> list[int]:
    """O(n log n) time and O(n) auxiliary space; inputs are read-only."""
    ordered = sorted((value, index) for index, value in enumerate(nums))
    result = [0] * len(nums)
    left = 0
    while left < len(nums):
        right = left + 1
        while right < len(nums) and ordered[right][0] - ordered[right - 1][0] <= limit:
            right += 1
        indices = sorted(ordered[index][1] for index in range(left, right))
        for offset, index in enumerate(indices):
            result[index] = ordered[left + offset][0]
        left = right
    return result


class Solution:
    def lexicographicallySmallestArray(self, nums: list[int], limit: int) -> list[int]:
        return solve(nums, limit)
