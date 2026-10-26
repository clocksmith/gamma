"""1366. Rank Teams by Votes: compare complete position-count vectors before alphabetical order."""


def solve(votes: list[str]) -> str:
    """O(v * t + t^2 log t) time and O(t^2) auxiliary space for v votes and t teams; inputs are read-only."""
    teams = list(votes[0])
    width = len(teams)
    counts = {team: [0] * width for team in teams}
    for vote in votes:
        for position, team in enumerate(vote):
            counts[team][position] += 1
    teams.sort(key=lambda team: (tuple(-count for count in counts[team]), team))
    return ''.join(teams)


class Solution:
    def rankTeams(self, votes: list[str]) -> str:
        return solve(votes)
