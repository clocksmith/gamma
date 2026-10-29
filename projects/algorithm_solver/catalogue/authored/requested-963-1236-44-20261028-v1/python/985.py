"""Original candidate; no qualification or admission."""

def solve(nums,queries):
    values=list(nums);total=sum(v for v in values if v%2==0);out=[]
    for delta,index in queries:
        if values[index]%2==0:total-=values[index]
        values[index]+=delta
        if values[index]%2==0:total+=values[index]
        out.append(total)
    return out


class Solution:
    def sumEvenAfterQueries(self, nums, queries):
        return solve(nums, queries)
