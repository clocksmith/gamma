"""Original candidate for LeetCode 2941. Contract: https://leetcode.com/problems/maximum-gcd-sum-of-a-subarray/
Definition additionally checked against public doocs/leetcode documentation (CC-BY-SA-4.0); original implementation.
Development tests only; not admitted or independently qualified.
Positional nums,k. JS returns Number when safe, otherwise exact BigInt; transport BigInt as decimal integer string, never rounded Number.
Complexity: O(n log V log V) conservative time, O(n+log V) space"""
from math import gcd
def solve(nums,k):
    prefix=[0];states=[];ans=0
    for i,a in enumerate(nums):
        prefix.append(prefix[-1]+a);nd=[]
        for g,start in states+[(a,i)]:
            ng=gcd(g,a)
            if nd and nd[-1][0]==ng:continue
            nd.append((ng,start))
        states=nd
        for g,start in states:
            if i-start+1>=k:ans=max(ans,(prefix[i+1]-prefix[start])*g)
    return ans
