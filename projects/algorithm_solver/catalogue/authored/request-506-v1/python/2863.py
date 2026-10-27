# Original candidate. Contract: https://leetcode.com/problems/maximum-length-of-semi-decreasing-subarrays/
def solve(nums):
    stack=[]
    for i,x in enumerate(nums):
        if not stack or x>nums[stack[-1]]:stack.append(i)
    answer=0
    for j in range(len(nums)-1,-1,-1):
        while stack and nums[stack[-1]]>nums[j]:answer=max(answer,j-stack.pop()+1)
    return answer
