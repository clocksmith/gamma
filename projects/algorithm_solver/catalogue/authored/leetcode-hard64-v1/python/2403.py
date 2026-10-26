"""2403. Minimum Time to Kill All Monsters: subset dynamic programming with kill-count energy gain."""


def solve(power: list[int]) -> int:
    """O(n * 2^n) time and O(2^n) auxiliary space. Inputs are preserved."""
    length = len(power)
    size = 1 << length
    unreachable = sum(power) + 1
    best = [unreachable] * size
    best[0] = 0
    for mask in range(size):
        gain = mask.bit_count() + 1
        for monster, strength in enumerate(power):
            bit = 1 << monster
            if mask & bit:
                continue
            days = (strength + gain - 1) // gain
            following = mask | bit
            best[following] = min(best[following], best[mask] + days)
    return best[-1]


class Solution:
    def minimumTime(self, power: list[int]) -> int:
        return solve(power)
