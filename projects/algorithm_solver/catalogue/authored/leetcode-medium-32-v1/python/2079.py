"""2079. Watering Plants: charge each refill its extra round trip."""


def solve(plants: list[int], capacity: int) -> int:
    """O(n) time and O(1) auxiliary space; inputs are read-only."""
    remaining = capacity
    steps = 0
    for index, amount in enumerate(plants):
        if remaining < amount:
            steps += 2 * index
            remaining = capacity
        remaining -= amount
        steps += 1
    return steps


class Solution:
    def wateringPlants(self, plants: list[int], capacity: int) -> int:
        return solve(plants, capacity)
