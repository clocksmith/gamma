"""Original frontend 3909 variant; qualification unknown."""

def solve(nums):
    peak = max(range(len(nums)), key=nums.__getitem__)
    left = right = 0
    for i, value in enumerate(nums):
        if i < peak:
            left += value
        elif i > peak:
            right += value
    return 0 if left > right else 1 if right > left else -1


class Solution:
    def compareBitonicSums(self, nums):
        return solve(nums)
