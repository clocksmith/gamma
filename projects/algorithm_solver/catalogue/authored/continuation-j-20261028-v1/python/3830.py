"""Original frontend 3830 variant; qualification unknown."""

def solve(nums):
    n = len(nums)
    def sign(a, b):
        return (b > a) - (b < a)
    left = [1] * n
    right = [1] * n
    for i in range(1, n):
        direction = sign(nums[i - 1], nums[i])
        if direction:
            left[i] = left[i - 1] + 1 if i >= 2 and direction == -sign(nums[i - 2], nums[i - 1]) else 2
    for i in range(n - 2, -1, -1):
        direction = sign(nums[i], nums[i + 1])
        if direction:
            right[i] = right[i + 1] + 1 if i + 2 < n and direction == -sign(nums[i + 1], nums[i + 2]) else 2
    answer = max(left)
    for removed in range(1, n - 1):
        bridge = sign(nums[removed - 1], nums[removed + 1])
        if not bridge:
            continue
        a, b = left[removed - 1], right[removed + 1]
        if a >= 2 and sign(nums[removed - 2], nums[removed - 1]) == bridge:
            a = 1
        if b >= 2 and sign(nums[removed + 1], nums[removed + 2]) == bridge:
            b = 1
        answer = max(answer, a + b)
    return answer


class Solution:
    def longestAlternating(self, nums):
        return solve(nums)
