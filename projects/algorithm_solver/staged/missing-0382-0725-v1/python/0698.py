"""698. Partition to K Equal Sum Subsets. Subset-mask DP records the unfinished bucket sum; O(n*2^n) time."""

def solve(nums: list[int], k: int) -> bool:
    total = sum(nums)
    if k > len(nums) or total % k:
        return False
    target = total // k
    if target == 0:
        return True
    ordered = sorted(nums)
    if ordered[-1] > target:
        return False
    size = 1 << len(nums)
    remainder = [-1] * size
    remainder[0] = 0
    for mask in range(size):
        if remainder[mask] < 0:
            continue
        for i, value in enumerate(ordered):
            if mask & (1 << i):
                continue
            if remainder[mask] + value > target:
                break
            remainder[mask | (1 << i)] = (remainder[mask] + value) % target
    return remainder[-1] == 0


class Solution:
    def canPartitionKSubsets(self, nums: list[int], k: int) -> bool:
        return solve(nums, k)
