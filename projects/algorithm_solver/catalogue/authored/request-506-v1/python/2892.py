# Original candidate implementation. Contract: https://leetcode.com/problems/minimizing-array-after-replacing-pairs-with-their-product/
def solve(nums,k):
    if 0 in nums:return 1
    groups=0;product=1
    for v in nums:
        if groups==0 or product>k//v:groups+=1;product=v
        else:product*=v
    return groups
