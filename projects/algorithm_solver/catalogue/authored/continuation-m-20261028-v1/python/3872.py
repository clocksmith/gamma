def solve(nums):
    n = len(nums)
    left = [1] * n
    right = [1] * n
    left[1] = right[n - 2] = 2
    for i in range(2, n):
        left[i] = left[i - 1] + 1 if nums[i] - nums[i - 1] == nums[i - 1] - nums[i - 2] else 2
    for i in range(n - 3, -1, -1):
        right[i] = right[i + 1] + 1 if nums[i + 1] - nums[i] == nums[i + 2] - nums[i + 1] else 2
    answer = min(n, max(left) + 1)
    for i in range(1, n - 1):
        gap = nums[i + 1] - nums[i - 1]
        if gap % 2:
            continue
        d = gap // 2
        l = left[i - 1] if i >= 2 and nums[i - 1] - nums[i - 2] == d else 1
        r = right[i + 1] if i + 2 < n and nums[i + 2] - nums[i + 1] == d else 1
        answer = max(answer, l + 1 + r)
    return answer


class Solution:
    def longestArithmetic(self, nums):
        return solve(nums)
