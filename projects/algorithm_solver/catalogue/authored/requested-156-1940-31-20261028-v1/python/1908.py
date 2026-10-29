"""Original frontend 1908 variant; qualification unknown."""


def solve(piles) -> bool:
    xor_sum = 0
    for x in piles:
        xor_sum ^= x
    return xor_sum != 0


nimGame = solve


class Solution:
    def nimGame(self, piles) -> bool:
        return solve(piles)
