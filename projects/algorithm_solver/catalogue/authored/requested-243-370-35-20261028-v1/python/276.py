"""Original frontend 276 variant; qualification unknown."""


def solve(n: int, k: int) -> int:
    if n == 1:
        return k
    same = k
    diff = k * (k - 1)
    for _ in range(3, n + 1):
        same, diff = diff, (same + diff) * (k - 1)
    return same + diff


numWays = solve


class Solution:
    def numWays(self, n: int, k: int) -> int:
        return solve(n, k)
