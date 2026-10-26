"""1691. Maximum Height by Stacking Cuboids: canonical orientations and dominance DP; O(n^2) time and O(n) space. Inputs are preserved."""


def solve(cuboids: list[list[int]]) -> int:
    ordered = sorted(sorted(cuboid) for cuboid in cuboids)
    height = [cuboid[2] for cuboid in ordered]
    for bottom, dimensions in enumerate(ordered):
        for top in range(bottom):
            if all(ordered[top][axis] <= dimensions[axis] for axis in range(3)):
                height[bottom] = max(height[bottom], height[top] + dimensions[2])
    return max(height, default=0)


class Solution:
    def maxHeight(self, cuboids: list[list[int]]) -> int:
        return solve(cuboids)
