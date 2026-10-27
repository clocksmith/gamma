"""446. Arithmetic Slices II - Subsequence. Count length-at-least-two subsequences by endpoint and exact difference."""

def solve(nums: list[int]) -> int:
    ending = [{} for _ in nums]
    answer = 0
    for i, value in enumerate(nums):
        for j in range(i):
            difference = value - nums[j]
            count = ending[j].get(difference, 0)
            answer += count
            ending[i][difference] = ending[i].get(difference, 0) + count + 1
    return answer


class Solution:
    def numberOfArithmeticSlices(self, nums: list[int]) -> int:
        return solve(nums)
