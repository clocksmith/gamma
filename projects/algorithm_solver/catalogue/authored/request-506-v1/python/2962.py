# Original implementation. Contract: https://leetcode.com/problems/count-subarrays-where-max-element-appears-at-least-k-times/
def solve(nums,k):
    maximum=max(nums);left=count=answer=0
    for x in nums:
        count+=x==maximum
        while count>=k:
            count-=nums[left]==maximum;left+=1
        answer+=left
    return answer
