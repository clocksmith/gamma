"""Original frontend 254 variant; qualification unknown."""


def solve(n: int):
    res = []
    path = []

    def dfs(rem: int, start: int):
        d = start
        while d * d <= rem:
            if rem % d == 0:
                res.append(path + [d, rem // d])
                path.append(d)
                dfs(rem // d, d)
                path.pop()
            d += 1

    dfs(n, 2)
    return res


getFactors = solve


class Solution:
    def getFactors(self, n: int):
        return solve(n)
