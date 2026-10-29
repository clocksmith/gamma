"""Original frontend 370 variant; qualification unknown."""


def solve(length: int, updates):
    diff = [0] * (length + 1)
    for l, r, inc in updates:
        diff[l] += inc
        diff[r + 1] -= inc
    res = [0] * length
    cur = 0
    for i in range(length):
        cur += diff[i]
        res[i] = cur
    return res


getModifiedArray = solve


class Solution:
    def getModifiedArray(self, length: int, updates):
        return solve(length, updates)
