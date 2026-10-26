"""2369. Check if There is a Valid Partition For The Array: extend valid prefixes by equal pairs or one of the two permitted triples."""


def solve(nums: list[int]) -> bool:
    """O(n) time and O(n) auxiliary space; inputs are read-only."""
    valid = [False] * (len(nums) + 1)
    valid[0] = True
    for end in range(2, len(nums) + 1):
        if nums[end - 1] == nums[end - 2] and valid[end - 2]:
            valid[end] = True
        if end >= 3 and valid[end - 3]:
            equal = nums[end - 3] == nums[end - 2] == nums[end - 1]
            consecutive = nums[end - 3] + 1 == nums[end - 2] and nums[end - 2] + 1 == nums[end - 1]
            if equal or consecutive:
                valid[end] = True
    return valid[-1]


class Solution:
    def validPartition(self, nums: list[int]) -> bool:
        return solve(nums)
