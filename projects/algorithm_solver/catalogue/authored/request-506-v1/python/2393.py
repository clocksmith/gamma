# Original candidate. Contract: https://leetcode.com/problems/count-strictly-increasing-subarrays/
def solve(nums):
    run=answer=0
    for i,x in enumerate(nums):run=run+1 if i and nums[i-1]<x else 1;answer+=run
    return answer
