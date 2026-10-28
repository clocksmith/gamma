def solve(nums):
    answer = 0
    for l in range(len(nums)):
        seen = set()
        total = 0
        for r in range(l, len(nums)):
            total += nums[r]
            seen.add(nums[r])
            answer += total in seen
    return answer


class Solution:
    def centeredSubarrays(self, nums):
        return solve(nums)
