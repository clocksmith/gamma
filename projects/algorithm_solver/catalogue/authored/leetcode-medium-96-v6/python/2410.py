"""2410. Maximum Matching of Players With Trainers: give each sorted player the first remaining trainer with sufficient capacity."""


def solve(players: list[int], trainers: list[int]) -> int:
    """O(p log p + t log t) time and O(p + t) auxiliary space; inputs are read-only."""
    abilities = sorted(players)
    capacities = sorted(trainers)
    player = 0
    for capacity in capacities:
        if player < len(abilities) and abilities[player] <= capacity:
            player += 1
    return player


class Solution:
    def matchPlayersAndTrainers(self, players: list[int], trainers: list[int]) -> int:
        return solve(players, trainers)
