def solve(nums):
    n = len(nums)
    left = [1] * n
    right = [1] * n
    for i in range(1, n):
        if nums[i - 1] <= nums[i]:
            left[i] = left[i - 1] + 1
    for i in range(n - 2, -1, -1):
        if nums[i] <= nums[i + 1]:
            right[i] = right[i + 1] + 1
    answer = max(left)
    for i in range(n):
        if i:
            answer = max(answer, left[i - 1] + 1)
        if i + 1 < n:
            answer = max(answer, right[i + 1] + 1)
        if 0 < i < n - 1 and nums[i - 1] <= nums[i + 1]:
            answer = max(answer, left[i - 1] + 1 + right[i + 1])
    return min(answer, n)


class Solution:
    def longestSubarray(self, nums):
        return solve(nums)
