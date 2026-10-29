"""Original candidate; no qualification or admission."""

def solve(nums):
    counts=[0]*65536
    for a in nums:
        for b in nums:counts[a&b]+=1
    for bit in range(16):
        for mask in range(65536):
            if mask>>bit&1:counts[mask]+=counts[mask^(1<<bit)]
    return sum(counts[65535^value] for value in nums)


class Solution:
    def countTriplets(self, nums):
        return solve(nums)
