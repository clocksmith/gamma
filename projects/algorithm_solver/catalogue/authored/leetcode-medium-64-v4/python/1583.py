"""1583. Count Unhappy Friends: use preference ranks to detect mutually preferable alternative partners."""


def solve(n: int, preferences: list[list[int]], pairs: list[list[int]]) -> int:
    """O(n^2) time and O(n^2) auxiliary space; inputs are read-only."""
    rank = [[0] * n for _ in range(n)]
    for person, ordered in enumerate(preferences):
        for position, other in enumerate(ordered):
            rank[person][other] = position
    partner = [-1] * n
    for first, second in pairs:
        partner[first] = second
        partner[second] = first
    unhappy = 0
    for person in range(n):
        for other in preferences[person]:
            if other == partner[person]:
                break
            if rank[other][person] < rank[other][partner[other]]:
                unhappy += 1
                break
    return unhappy


class Solution:
    def unhappyFriends(self, n: int, preferences: list[list[int]], pairs: list[list[int]]) -> int:
        return solve(n, preferences, pairs)
