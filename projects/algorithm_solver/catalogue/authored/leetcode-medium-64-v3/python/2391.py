"""2391. Minimum Amount of Time to Collect Garbage: add pickup time and each truck last-needed travel distance."""


def solve(garbage: list[str], travel: list[int]) -> int:
    """O(n + S) time and O(1) auxiliary space for S garbage characters; inputs are read-only."""
    last_distance = {'M': 0, 'P': 0, 'G': 0}
    elapsed = pickup = 0
    for index, house in enumerate(garbage):
        if index:
            elapsed += travel[index - 1]
        pickup += len(house)
        for kind in house:
            last_distance[kind] = elapsed
    return pickup + sum(last_distance.values())


class Solution:
    def garbageCollection(self, garbage: list[str], travel: list[int]) -> int:
        return solve(garbage, travel)
