"""Original frontend 3835 variant; qualification unknown."""

def solve(nums, k):
    from collections import deque
    maximum, minimum = deque(), deque()
    left = answer = 0
    for right, value in enumerate(nums):
        while maximum and nums[maximum[-1]] <= value:
            maximum.pop()
        while minimum and nums[minimum[-1]] >= value:
            minimum.pop()
        maximum.append(right)
        minimum.append(right)
        if (nums[maximum[0]] - nums[minimum[0]]) * (right - left + 1) > k:
            if maximum[0] == left:
                maximum.popleft()
            if minimum[0] == left:
                minimum.popleft()
            left += 1
        answer += right - left + 1
    return answer


class Solution:
    def countSubarrays(self, nums, k):
        return solve(nums, k)
