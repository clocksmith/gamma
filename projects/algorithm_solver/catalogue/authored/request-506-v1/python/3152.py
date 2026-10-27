# Original implementation. Contract: https://leetcode.com/problems/special-array-ii/
def solve(nums,queries):
    bad=[0]*len(nums)
    for i in range(1,len(nums)):bad[i]=bad[i-1]+(nums[i]%2==nums[i-1]%2)
    return [bad[l]==bad[r] for l,r in queries]
