"""Original frontend 3819 variant; qualification unknown."""

def solve(nums, k):
    values = [value for value in nums if value >= 0]
    if not values:
        return nums[:]
    shift = k % len(values)
    answer = nums[:]
    index = 0
    for i, value in enumerate(nums):
        if value >= 0:
            answer[i] = values[(index + shift) % len(values)]
            index += 1
    return answer


class Solution:
    def rotateElements(self, nums, k):
        return solve(nums, k)
