"""698. Partition to K Equal Sum Subsets (Medium).

Specification: https://leetcode.com/problems/partition-to-k-equal-sum-subsets/description/
"""


def solve(nums: list[int], k: int) -> bool:
    total = sum(nums)
    if total % k != 0:
        return False
    target = total // k
    ordered = sorted(nums, reverse=True)
    if ordered and ordered[0] > target:
        return False
    buckets = [0] * k

    def backtrack(index):
        if index == len(ordered):
            return all(value == target for value in buckets)
        for i in range(k):
            if buckets[i] + ordered[index] > target:
                continue
            if i > 0 and buckets[i] == buckets[i - 1]:
                continue
            buckets[i] += ordered[index]
            if backtrack(index + 1):
                return True
            buckets[i] -= ordered[index]
        return False

    return backtrack(0)


class Solution:
    def canPartitionKSubsets(self, nums: list[int], k: int) -> bool:
        return solve(nums, k)
