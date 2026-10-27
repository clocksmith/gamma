"""Original candidate for LeetCode 2972. Contract: https://leetcode.com/problems/count-the-number-of-incremovable-subarrays-ii/
Development tests only; not admitted or independently qualified.
Positional arguments match the official function; inputs are not mutated.
Complexity: O(n) time, O(1) space; counts <= 5,000,050,000"""
def solve(nums):
    n=len(nums);i=0
    while i+1<n and nums[i]<nums[i+1]:i+=1
    if i==n-1:return n*(n+1)//2
    ans=i+2;j=n-1
    while j>=0:
        while i>=0 and nums[i]>=nums[j]:i-=1
        ans+=i+2
        if j==0 or nums[j-1]>=nums[j]:break
        j-=1
    return ans
