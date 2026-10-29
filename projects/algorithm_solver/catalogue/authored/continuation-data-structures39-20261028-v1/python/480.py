"""Original frontend 480 variant; qualification unknown."""
from bisect import bisect_left, insort


def solve(nums, k: int):
    window = sorted(nums[:k])
    half = k // 2
    odd = (k & 1) == 1
    out = [float(window[half]) if odd else (window[half - 1] + window[half]) / 2.0]
    for i in range(k, len(nums)):
        out_val = nums[i - k]
        idx = bisect_left(window, out_val)
        window.pop(idx)
        insort(window, nums[i])
        out.append(float(window[half]) if odd else (window[half - 1] + window[half]) / 2.0)
    return out


medianSlidingWindow = solve


class Solution:
    def medianSlidingWindow(self, nums, k: int):
        return solve(nums, k)
