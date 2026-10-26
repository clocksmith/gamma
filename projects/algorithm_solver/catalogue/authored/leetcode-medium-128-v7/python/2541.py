"""2541. Minimum Operations to Make Array Equal II: require divisible differences and balanced transfers between indices."""


def solve(nums1: list[int], nums2: list[int], k: int) -> int:
    """O(n) time and O(1) auxiliary space; inputs are read-only."""
    if k == 0:
        return 0 if nums1 == nums2 else -1
    balance = operations = 0
    for left, right in zip(nums1, nums2):
        difference = left - right
        if difference % k:
            return -1
        balance += difference
        if difference > 0:
            operations += difference // k
    return operations if balance == 0 else -1


class Solution:
    def minOperations(self, nums1: list[int], nums2: list[int], k: int) -> int:
        return solve(nums1, nums2, k)
