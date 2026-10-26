"""2105. Watering Plants II: advance two watering fronts and use the larger remaining supply at the middle."""


def solve(plants: list[int], capacityA: int, capacityB: int) -> int:
    """O(n) time and O(1) auxiliary space; inputs are read-only."""
    left, right = 0, len(plants) - 1
    water_a, water_b = capacityA, capacityB
    refills = 0
    while left < right:
        if water_a < plants[left]:
            refills += 1
            water_a = capacityA
        water_a -= plants[left]
        if water_b < plants[right]:
            refills += 1
            water_b = capacityB
        water_b -= plants[right]
        left += 1
        right -= 1
    if left == right and max(water_a, water_b) < plants[left]:
        refills += 1
    return refills


class Solution:
    def minimumRefill(self, plants: list[int], capacityA: int, capacityB: int) -> int:
        return solve(plants, capacityA, capacityB)
