# Original candidate. Contract: https://leetcode.com/problems/maximum-of-minimum-values-in-all-subarrays/
def solve(nums):
    n=len(nums);stack=[];ans=[0]*n
    for i in range(n+1):
        while stack and (i==n or nums[stack[-1]]>=nums[i]):
            j=stack.pop();length=i-(stack[-1] if stack else -1)-1;ans[length-1]=max(ans[length-1],nums[j])
        stack.append(i)
    for i in range(n-2,-1,-1):ans[i]=max(ans[i],ans[i+1])
    return ans
