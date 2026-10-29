"""Hack2Hire 68672293a2d59460201f2cae (Delete k Elements to Balance) over an INFERRED spec; qualification unknown."""


def solve(nums, k):
    n = len(nums)
    even, odd = [0] * (n + 1), [0] * (n + 1)
    for i, value in enumerate(nums):
        even[i + 1] = even[i] + (value if i % 2 == 0 else 0)
        odd[i + 1] = odd[i] + (value if i % 2 else 0)
    for i in range(n - k + 1):
        tail_even, tail_odd = even[n] - even[i + k], odd[n] - odd[i + k]
        if k % 2:
            tail_even, tail_odd = tail_odd, tail_even
        if even[i] + tail_even == odd[i] + tail_odd:
            return i
    return -1


class Solution:
    def balanceStart(self, nums, k):
        return solve(nums, k)
