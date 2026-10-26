"""2216. Minimum Deletions to Make Array Beautiful: greedily complete unequal pairs and remove any unmatched final element."""


def solve(nums: list[int]) -> int:
    """O(n) time and O(1) auxiliary space; inputs are read-only."""
    kept = deleted = 0
    previous = 0
    for value in nums:
        if kept % 2 and value == previous:
            deleted += 1
        else:
            kept += 1
            previous = value
    return deleted + kept % 2


class Solution:
    def minDeletion(self, nums: list[int]) -> int:
        return solve(nums)
