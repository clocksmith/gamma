"""Original frontend 3356 variant; qualification unknown."""


def solve(nums, queries) -> int:
    n = len(nums)
    diff = [0] * (n + 1)
    cur = 0
    k = 0
    for i in range(n):
        while cur + diff[i] < nums[i]:
            if k == len(queries):
                return -1
            l, r, val = queries[k]
            k += 1
            if r >= i:
                diff[max(l, i)] += val
                diff[r + 1] -= val
        cur += diff[i]
    return k


minZeroArray = solve


class Solution:
    def minZeroArray(self, nums, queries) -> int:
        return solve(nums, queries)
