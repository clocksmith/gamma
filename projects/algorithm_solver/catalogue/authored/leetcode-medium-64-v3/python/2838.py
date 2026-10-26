"""2838. Maximum Coins Heroes Can Collect: sort monsters by power and query cumulative rewards."""
from bisect import bisect_right


def solve(heroes: list[int], monsters: list[int], coins: list[int]) -> list[int]:
    """O(m log m + h log(m + 1)) time and O(m + h) space for m monsters and h heroes; inputs are read-only."""
    ordered = sorted(zip(monsters, coins))
    strengths = []
    rewards = [0]
    for strength, reward in ordered:
        strengths.append(strength)
        rewards.append(rewards[-1] + reward)
    return [rewards[bisect_right(strengths, hero)] for hero in heroes]


class Solution:
    def maximumCoins(self, heroes: list[int], monsters: list[int], coins: list[int]) -> list[int]:
        return solve(heroes, monsters, coins)
