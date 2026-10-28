"""835. Image Overlap (Medium).

Specification: https://leetcode.com/problems/image-overlap/description/
"""


def solve(img1: list[list[int]], img2: list[list[int]]) -> int:
    n = len(img1)
    ones1 = [(r, c) for r in range(n) for c in range(n) if img1[r][c] == 1]
    ones2 = [(r, c) for r in range(n) for c in range(n) if img2[r][c] == 1]
    counts = {}
    best = 0
    for r1, c1 in ones1:
        for r2, c2 in ones2:
            key = (r1 - r2, c1 - c2)
            counts[key] = counts.get(key, 0) + 1
            best = max(best, counts[key])
    return best


class Solution:
    def largestOverlap(self, img1: list[list[int]], img2: list[list[int]]) -> int:
        return solve(img1, img2)
