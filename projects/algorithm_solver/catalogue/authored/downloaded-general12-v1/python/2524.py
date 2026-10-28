"""2524. Maximum Frequency Score of a Subarray (Hard).

Specification: https://leetcode.com/problems/maximum-frequency-score-of-a-subarray/description/
"""


def solve(nums, k):
    MOD = 1000000007
    freq = {}
    score = 0
    for i in range(k):
        v = nums[i]
        f = freq.get(v, 0)
        if f > 0:
            score -= pow(v, f, MOD)
        freq[v] = f + 1
        score += pow(v, f + 1, MOD)
    ans = score % MOD
    for i in range(k, len(nums)):
        out, inn = nums[i - k], nums[i]
        if out != inn:
            f = freq[out]
            score -= pow(out, f, MOD)
            freq[out] = f - 1
            if f - 1 > 0:
                score += pow(out, f - 1, MOD)
            f = freq.get(inn, 0)
            if f > 0:
                score -= pow(inn, f, MOD)
            freq[inn] = f + 1
            score += pow(inn, f + 1, MOD)
        ans = max(ans, score % MOD)
    return ans


class Solution:
    def maxFrequencyScore(self, nums, k):
        return solve(nums, k)
