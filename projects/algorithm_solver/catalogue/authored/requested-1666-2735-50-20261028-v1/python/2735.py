"""Original candidate; no qualification or admission."""

def solve(nums,x):
    best=list(nums);answer=sum(best)
    for rotations in range(1,len(nums)):
        for i in range(len(nums)):best[i]=min(best[i],nums[(i+rotations)%len(nums)])
        answer=min(answer,sum(best)+rotations*x)
    return answer


class Solution:
    def minCost(self, nums, x):
        return solve(nums, x)
