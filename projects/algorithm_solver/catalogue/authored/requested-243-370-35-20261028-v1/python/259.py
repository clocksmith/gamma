"""Original frontend 259 variant; qualification unknown."""


def solve(nums, target: int) -> int:
    arr = sorted(nums)
    n = len(arr)
    ans = 0
    for i in range(n - 2):
        lo, hi = i + 1, n - 1
        while lo < hi:
            if arr[i] + arr[lo] + arr[hi] < target:
                ans += hi - lo
                lo += 1
            else:
                hi -= 1
    return ans


threeSumSmaller = solve


class Solution:
    def threeSumSmaller(self, nums, target: int) -> int:
        return solve(nums, target)
