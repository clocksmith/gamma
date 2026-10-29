"""Original candidate; no qualification or admission."""

from collections import Counter

def solve(nums,k):
    total=sum(nums);prefix=0;diffs=[]
    for value in nums[:-1]:prefix+=value;diffs.append(2*prefix-total)
    right=Counter(diffs);left=Counter();answer=right[0]
    for i,value in enumerate(nums):
        delta=k-value;answer=max(answer,left[delta]+right[-delta])
        if i<len(diffs):right[diffs[i]]-=1;left[diffs[i]]+=1
    return answer


class Solution:
    def waysToPartition(self, nums, k):
        return solve(nums, k)
