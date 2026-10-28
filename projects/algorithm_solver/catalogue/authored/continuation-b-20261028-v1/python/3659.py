from collections import Counter

def solve(nums, k):
    if len(nums) % k: return False
    return max(Counter(nums).values()) <= len(nums)//k

class Solution:
    def partitionArray(self, nums, k):
        return solve(nums, k)
