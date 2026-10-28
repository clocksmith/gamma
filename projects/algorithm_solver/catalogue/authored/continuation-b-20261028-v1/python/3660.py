def solve(nums):
    n = len(nums)
    suffix = [0]*(n+1)
    suffix[n] = float('inf')
    for i in range(n-1, -1, -1): suffix[i] = min(nums[i], suffix[i+1])
    result = [0]*n
    start = 0
    maximum = 0
    for i, value in enumerate(nums):
        maximum = max(maximum, value)
        if maximum <= suffix[i+1]:
            for j in range(start, i+1): result[j] = maximum
            start = i+1
            maximum = 0
    return result

class Solution:
    def maxValue(self, nums):
        return solve(nums)
