"""1590. Make Sum Divisible by P: match prefix remainders using the latest index for the shortest removable interval."""


def solve(nums: list[int], p: int) -> int:
    """O(n) expected time and O(min(n, p)) auxiliary space; inputs are read-only."""
    required = sum(nums) % p
    if required == 0:
        return 0
    latest = {0: -1}
    prefix = 0
    best = len(nums)
    for index, value in enumerate(nums):
        prefix = (prefix + value) % p
        wanted = (prefix - required) % p
        if wanted in latest:
            best = min(best, index - latest[wanted])
        latest[prefix] = index
    return best if best < len(nums) else -1


class Solution:
    def minSubarray(self, nums: list[int], p: int) -> int:
        return solve(nums, p)
