# Original candidate. Contract: https://leetcode.com/problems/find-triangular-sum-of-an-array/
def solve(nums):
    a=list(nums)
    for n in range(len(a)-1,0,-1):
        for i in range(n):a[i]=(a[i]+a[i+1])%10
    return a[0]
