"""2225. Find Players With Zero or One Losses: record every participating player and sort the zero-loss and one-loss groups."""


def solve(matches: list[list[int]]) -> list[list[int]]:
    """O(m + p log p) expected time and O(p) auxiliary space for m matches and p players; inputs are read-only."""
    losses = {}
    for winner, loser in matches:
        losses.setdefault(winner, 0)
        losses[loser] = losses.get(loser, 0) + 1
    undefeated = sorted(player for player, count in losses.items() if count == 0)
    one_loss = sorted(player for player, count in losses.items() if count == 1)
    return [undefeated, one_loss]


class Solution:
    def findWinners(self, matches: list[list[int]]) -> list[list[int]]:
        return solve(matches)
