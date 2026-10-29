"""Original candidate; no qualification or admission."""

def solve(nums):
    prefix=[0]
    for value in nums:prefix.append(prefix[-1]+value)
    n=len(nums);lower=upper=2;answer=0
    for first in range(1,n-1):
        lower=max(lower,first+1)
        while lower<n and prefix[lower]<2*prefix[first]:lower+=1
        upper=max(upper,lower)
        while upper<n and 2*prefix[upper]<=prefix[n]+prefix[first]:upper+=1
        answer=(answer+upper-lower)%1000000007
    return answer


class Solution:
    def waysToSplit(self, nums):
        return solve(nums)
