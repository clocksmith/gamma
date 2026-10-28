"""2845. Count of Interesting Subarrays (Medium).

Specification: https://leetcode.com/problems/count-of-interesting-subarrays/description/
"""


def solve(nums, modulo, k):
    cnt = {0: 1}
    s = 0
    ans = 0
    for x in nums:
        if x % modulo == k:
            s += 1
        sm = s % modulo
        target = (sm - k) % modulo
        ans += cnt.get(target, 0)
        cnt[sm] = cnt.get(sm, 0) + 1
    return ans


class Solution:
    def countInterestingSubarrays(self, *args):
        return solve(*args)
