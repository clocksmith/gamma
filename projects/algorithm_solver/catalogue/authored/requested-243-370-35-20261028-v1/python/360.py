"""Original frontend 360 variant; qualification unknown."""


def solve(nums, a: int, b: int, c: int):
    n = len(nums)
    res = [0] * n
    l, r = 0, n - 1
    idx = n - 1 if a >= 0 else 0
    while l <= r:
        vl = a * nums[l] * nums[l] + b * nums[l] + c
        vr = a * nums[r] * nums[r] + b * nums[r] + c
        if a >= 0:
            if vl > vr:
                res[idx] = vl
                l += 1
            else:
                res[idx] = vr
                r -= 1
            idx -= 1
        else:
            if vl < vr:
                res[idx] = vl
                l += 1
            else:
                res[idx] = vr
                r -= 1
            idx += 1
    return res


sortTransformedArray = solve


class Solution:
    def sortTransformedArray(self, nums, a: int, b: int, c: int):
        return solve(nums, a, b, c)
