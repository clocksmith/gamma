"""Original frontend 3326 variant; qualification unknown."""


def _spf(x: int) -> int:
    if x % 2 == 0:
        return 2
    d = 3
    while d * d <= x:
        if x % d == 0:
            return d
        d += 2
    return x


def solve(nums) -> int:
    arr = list(nums)
    ops = 0
    for i in range(len(arr) - 2, -1, -1):
        if arr[i] > arr[i + 1]:
            arr[i] = _spf(arr[i])
            ops += 1
            if arr[i] > arr[i + 1]:
                return -1
    return ops


minOperations = solve


class Solution:
    def minOperations(self, nums) -> int:
        return solve(nums)
