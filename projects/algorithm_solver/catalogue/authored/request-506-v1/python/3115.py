# Original candidate implementation. Contract: https://leetcode.com/problems/maximum-prime-difference/
def solve(nums):
    prime=[True]*101;prime[0]=prime[1]=False
    for p in range(2,11):
        if prime[p]:
            for v in range(p*p,101,p): prime[v]=False
    indices=[i for i,v in enumerate(nums) if prime[v]]
    return indices[-1]-indices[0]
