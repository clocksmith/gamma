"""2147. Number of Ways to Divide a Long Corridor."""


def solve(corridor: str) -> int:
    """Multiply the divider gaps between consecutive seat pairs; O(n) time and O(1) space. Inputs are preserved."""
    modulus = 1_000_000_007
    seats = 0
    previous = -1
    ways = 1
    for index, character in enumerate(corridor):
        if character != 'S':
            continue
        seats += 1
        if seats > 2 and seats % 2:
            ways = ways * (index - previous) % modulus
        if seats % 2 == 0:
            previous = index
    return ways if seats > 0 and seats % 2 == 0 else 0


class Solution:
    def numberOfWays(self, corridor: str) -> int:
        return solve(corridor)
