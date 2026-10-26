"""3285. Find Indices of Stable Mountains (Easy).

Specification: https://leetcode.com/problems/find-indices-of-stable-mountains/description/
"""


def solve(height: list[int], threshold: int) -> list[int]:
    """O(n) time and output space; a mountain depends on its predecessor, not itself."""
    result = []
    for index in range(1, len(height)):
        if height[index - 1] > threshold:
            result.append(index)
    return result


class Solution:
    def stableMountains(self, height: list[int], threshold: int) -> list[int]:
        return solve(height, threshold)
