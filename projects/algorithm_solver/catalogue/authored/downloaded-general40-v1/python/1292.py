"""1292. Maximum Side Length of a Square with Sum Less than or Equal to Threshold (Medium).

Specification: https://leetcode.com/problems/maximum-side-length-of-a-square-with-sum-less-than-or-equal-to-threshold/description/
"""


def solve(mat: list[list[int]], threshold: int) -> int:
    rows, cols = len(mat), len(mat[0])
    prefix = [[0] * (cols + 1) for _ in range(rows + 1)]
    for r in range(rows):
        for c in range(cols):
            prefix[r + 1][c + 1] = mat[r][c] + prefix[r][c + 1] + prefix[r + 1][c] - prefix[r][c]

    def square_sum(r, c, side):
        return prefix[r + side][c + side] - prefix[r][c + side] - prefix[r + side][c] + prefix[r][c]

    best = 0
    for r in range(rows):
        for c in range(cols):
            left, right, found = best + 1, min(rows - r, cols - c), best
            while left <= right:
                mid = (left + right) // 2
                if square_sum(r, c, mid) <= threshold:
                    found = mid
                    left = mid + 1
                else:
                    right = mid - 1
            best = max(best, found)
    return best


class Solution:
    def maxSideLength(self, mat: list[list[int]], threshold: int) -> int:
        return solve(mat, threshold)
