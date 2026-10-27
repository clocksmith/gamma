# Original implementation. Contract: https://leetcode.com/problems/minimum-number-of-operations-to-make-all-array-elements-equal-to-1/
from math import gcd
def solve(nums):
    n=len(nums);ones=nums.count(1)
    if ones:return n-ones
    best=n+1
    for i in range(n):
        g=0
        for j in range(i,n):
            g=gcd(g,nums[j])
            if g==1:best=min(best,j-i+1);break
    return -1 if best==n+1 else best+n-2
