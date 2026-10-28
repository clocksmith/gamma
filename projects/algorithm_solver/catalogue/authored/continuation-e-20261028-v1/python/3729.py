from math import gcd


def solve(nums, k):
    counts = {0: 1}
    remainder = answer = 0
    for x in nums:
        remainder = (remainder + x) % k
        answer += counts.get(remainder, 0)
        counts[remainder] = counts.get(remainder, 0) + 1
    i = 0
    while i < len(nums):
        j = i + 1
        while j < len(nums) and nums[j] == nums[i]:
            j += 1
        length = j - i
        period = k // gcd(nums[i], k)
        q = length // period
        answer -= q * length - period * q * (q + 1) // 2
        i = j
    return answer


class Solution:
    def numGoodSubarrays(self, nums, k):
        return solve(nums, k)
