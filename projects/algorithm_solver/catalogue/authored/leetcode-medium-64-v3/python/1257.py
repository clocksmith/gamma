"""1257. Smallest Common Region: intersect parent chains in the region tree."""


def solve(regions: list[list[str]], region1: str, region2: str) -> str:
    """O(r) time and O(r) auxiliary space for r region entries; inputs are read-only."""
    parent = {}
    for group in regions:
        for index in range(1, len(group)):
            parent[group[index]] = group[0]
    ancestors = set()
    current = region1
    while current is not None:
        ancestors.add(current)
        current = parent.get(current)
    current = region2
    while current not in ancestors:
        current = parent[current]
    return current


class Solution:
    def findSmallestRegion(self, regions: list[list[str]], region1: str, region2: str) -> str:
        return solve(regions, region1, region2)
