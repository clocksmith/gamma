# Original candidate. Contract: https://leetcode.com/problems/minimum-sum-of-mountain-triplets-i/
def solve(nums):
    answer=float('inf')
    for j in range(1,len(nums)-1):
        a,b=min(nums[:j]),min(nums[j+1:])
        if a<nums[j] and b<nums[j]:answer=min(answer,a+nums[j]+b)
    return -1 if answer==float('inf') else answer
