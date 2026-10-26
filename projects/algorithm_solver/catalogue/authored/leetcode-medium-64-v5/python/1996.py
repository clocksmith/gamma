"""1996. The Number of Weak Characters in the Game: scan decreasing attack with increasing defense inside equal-attack groups."""


def solve(properties: list[list[int]]) -> int:
    """O(n * log(n + 1)) time and O(n) auxiliary space; inputs are read-only."""
    ordered = sorted(properties, key=lambda pair: (-pair[0], pair[1]))
    strongest_defense = result = 0
    for _, defense in ordered:
        if defense < strongest_defense:
            result += 1
        strongest_defense = max(strongest_defense, defense)
    return result


class Solution:
    def numberOfWeakCharacters(self, properties: list[list[int]]) -> int:
        return solve(properties)
