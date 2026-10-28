def solve(nums):
    n = len(nums)
    decreasing = [True]*n
    for i in range(n-2,-1,-1): decreasing[i] = decreasing[i+1] and nums[i] > nums[i+1]
    total = sum(nums)
    prefix = 0
    increasing = True
    best = float('inf')
    for i in range(n-1):
        prefix += nums[i]
        if i: increasing = increasing and nums[i-1] < nums[i]
        if increasing and decreasing[i+1]: best = min(best,abs(2*prefix-total))
    return -1 if best == float('inf') else best

class Solution:
    def splitArray(self, nums):
        return solve(nums)
