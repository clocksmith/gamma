"""3346. Maximum Frequency of an Element After Performing Operations I (Medium).

Specification: https://leetcode.com/problems/maximum-frequency-of-an-element-after-performing-operations-i/description/
"""


def solve(nums: list[int], k: int, numOperations: int) -> int:
    cnt = {}
    diff = {}
    for x in nums:
        cnt[x] = cnt.get(x, 0) + 1
        diff[x - k] = diff.get(x - k, 0) + 1
        diff[x + k + 1] = diff.get(x + k + 1, 0) - 1
    ans = 0
    s = 0
    for key in sorted(set(diff) | set(cnt)):
        s += diff.get(key, 0)
        ans = max(ans, min(s, cnt.get(key, 0) + numOperations))
    return ans


class Solution:
    def maxFrequency(self, nums: list[int], k: int, numOperations: int) -> int:
        return solve(nums, k, numOperations)
