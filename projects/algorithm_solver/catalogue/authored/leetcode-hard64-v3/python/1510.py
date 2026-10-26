"""1510. Stone Game IV: winning-state dynamic programming; O(n*sqrt(n)) time and O(n) space."""


def solve(n: int) -> bool:
    winning = [False] * (n + 1)
    for stones in range(1, n + 1):
        root = 1
        while root * root <= stones:
            if not winning[stones - root * root]:
                winning[stones] = True
                break
            root += 1
    return winning[n]


class Solution:
    def winnerSquareGame(self, n: int) -> bool:
        return solve(n)
