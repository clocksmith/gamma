"""2212. Maximum Points in an Archery Competition: enumerate winning scoring regions and place unused arrows in region zero."""


def solve(numArrows: int, aliceArrows: list[int]) -> list[int]:
    """O(b * 2^b) time and O(b) space for the fixed b = 11 scoring regions; inputs are read-only."""
    best_score = -1
    best_mask = 0
    for mask in range(1 << 11):
        used = score = 0
        for region in range(1, 12):
            if mask & (1 << (region - 1)):
                used += aliceArrows[region] + 1
                score += region
        if used <= numArrows and score > best_score:
            best_score, best_mask = score, mask
    result = [0] * 12
    remaining = numArrows
    for region in range(1, 12):
        if best_mask & (1 << (region - 1)):
            result[region] = aliceArrows[region] + 1
            remaining -= result[region]
    result[0] = remaining
    return result


class Solution:
    def maximumBobPoints(self, numArrows: int, aliceArrows: list[int]) -> list[int]:
        return solve(numArrows, aliceArrows)
