"""2766. Relocate Marbles: track occupied positions since every move relocates all marbles at its source."""


def solve(nums: list[int], moveFrom: list[int], moveTo: list[int]) -> list[int]:
    """O(n + m + u log u) expected time and O(u) auxiliary space for u distinct occupied positions; inputs are read-only."""
    occupied = set(nums)
    for source, destination in zip(moveFrom, moveTo):
        occupied.remove(source)
        occupied.add(destination)
    return sorted(occupied)


class Solution:
    def relocateMarbles(self, nums: list[int], moveFrom: list[int], moveTo: list[int]) -> list[int]:
        return solve(nums, moveFrom, moveTo)
