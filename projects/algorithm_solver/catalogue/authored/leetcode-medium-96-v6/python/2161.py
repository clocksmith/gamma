"""2161. Partition Array According to Given Pivot: collect the three stable partitions without modifying the original order."""


def solve(nums: list[int], pivot: int) -> list[int]:
    """O(n) time and O(n) auxiliary and result space; inputs are read-only."""
    smaller, equal, larger = [], [], []
    for value in nums:
        if value < pivot:
            smaller.append(value)
        elif value == pivot:
            equal.append(value)
        else:
            larger.append(value)
    return smaller + equal + larger


class Solution:
    def pivotArray(self, nums: list[int], pivot: int) -> list[int]:
        return solve(nums, pivot)
