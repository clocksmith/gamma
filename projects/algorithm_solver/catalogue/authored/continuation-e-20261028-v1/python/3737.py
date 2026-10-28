def solve(nums, target):
    answer = 0
    for i in range(len(nums)):
        count = 0
        for j in range(i, len(nums)):
            count += nums[j] == target
            answer += 2 * count > j - i + 1
    return answer


class Solution:
    def countMajoritySubarrays(self, nums, target):
        return solve(nums, target)
