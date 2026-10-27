"""416. Partition Equal Subset Sum. Descending 0/1 subset-sum dynamic programming."""

def solve(nums: list[int]) -> bool:
    total = sum(nums)
    if total % 2:
        return False
    target = total // 2
    possible = bytearray(target + 1)
    possible[0] = 1
    for value in nums:
        for subtotal in range(target, value - 1, -1):
            if possible[subtotal - value]:
                possible[subtotal] = 1
    return bool(possible[target])


class Solution:
    def canPartition(self, nums: list[int]) -> bool:
        return solve(nums)
