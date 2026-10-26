"""1852. Distinct Numbers in Each Subarray: maintain frequencies for a fixed-width sliding window."""


def solve(nums: list[int], k: int) -> list[int]:
    """O(n) expected time and O(k) auxiliary space excluding output; inputs are read-only."""
    counts = {}
    result = []
    for index, value in enumerate(nums):
        counts[value] = counts.get(value, 0) + 1
        if index >= k:
            outgoing = nums[index - k]
            counts[outgoing] -= 1
            if counts[outgoing] == 0:
                del counts[outgoing]
        if index + 1 >= k:
            result.append(len(counts))
    return result


class Solution:
    def distinctNumbers(self, nums: list[int], k: int) -> list[int]:
        return solve(nums, k)
