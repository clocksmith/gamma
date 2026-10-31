"""Original frontend 3355 variant; qualification unknown."""


def solve(nums, queries) -> bool:
    n = len(nums)
    diff = [0] * (n + 1)
    for l, r in queries:
        diff[l] += 1
        diff[r + 1] -= 1
    cur = 0
    for i in range(n):
        cur += diff[i]
        if cur < nums[i]:
            return False
    return True


isZeroArray = solve


class Solution:
    def isZeroArray(self, nums, queries) -> bool:
        return solve(nums, queries)
