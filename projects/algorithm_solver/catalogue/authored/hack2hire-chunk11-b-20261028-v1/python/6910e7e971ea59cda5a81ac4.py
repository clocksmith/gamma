"""Hack2Hire 6910e7e971ea59cda5a81ac4 (Largest K Elements in Sliding Window) over an INFERRED spec; qualification unknown."""

from bisect import bisect_left, insort


def solve(nums, k, w):
    window = sorted(nums[:w])
    out = [window[w - k:][::-1]]
    for i in range(w, len(nums)):
        window.pop(bisect_left(window, nums[i - w]))
        insort(window, nums[i])
        out.append(window[w - k:][::-1])
    return out


class Solution:
    def largestKInWindows(self, nums, k, w):
        return solve(nums, k, w)
