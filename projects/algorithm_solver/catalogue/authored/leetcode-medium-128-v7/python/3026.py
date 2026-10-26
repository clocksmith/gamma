"""3026. Maximum Good Subarray Sum: keep the smallest preceding prefix sum for each possible endpoint value."""


def solve(nums: list[int], k: int) -> int:
    """O(n) expected time and O(n) auxiliary space; inputs are read-only."""
    minimum_prefix = {}
    prefix = 0
    best = None
    for value in nums:
        prefix += value
        for endpoint in (value - k, value + k):
            if endpoint in minimum_prefix:
                candidate = prefix - minimum_prefix[endpoint]
                best = candidate if best is None else max(best, candidate)
        before = prefix - value
        if value not in minimum_prefix or before < minimum_prefix[value]:
            minimum_prefix[value] = before
    return 0 if best is None else best


class Solution:
    def maximumSubarraySum(self, nums: list[int], k: int) -> int:
        return solve(nums, k)
