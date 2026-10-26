"""2731. Movement of Robots: treat collisions as exchanged identities and sum sorted final-position differences."""


def solve(nums: list[int], s: str, d: int) -> int:
    """O(n log n) time and O(n) auxiliary space; inputs are read-only."""
    modulus = 1_000_000_007
    positions = sorted(value + (d if direction == 'R' else -d) for value, direction in zip(nums, s))
    prefix = result = 0
    for index, position in enumerate(positions):
        result = (result + index * position - prefix) % modulus
        prefix += position
    return result


class Solution:
    def sumDistance(self, nums: list[int], s: str, d: int) -> int:
        return solve(nums, s, d)
