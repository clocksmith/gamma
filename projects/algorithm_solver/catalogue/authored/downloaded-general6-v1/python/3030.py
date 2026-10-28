"""3030. Find the Grid of Region Average (Medium).

Specification: https://leetcode.com/problems/find-the-grid-of-region-average/description/
"""


def is_region(image: list[list[int]], i: int, j: int, threshold: int) -> bool:
    for x in range(i, i + 3):
        for y in range(j, j + 3):
            if x > i and abs(image[x][y] - image[x - 1][y]) > threshold:
                return False
            if y > j and abs(image[x][y] - image[x][y - 1]) > threshold:
                return False
    return True


def solve(image: list[list[int]], threshold: int) -> list[list[int]]:
    m = len(image)
    n = len(image[0])
    sums = [[0] * n for _ in range(m)]
    counts = [[0] * n for _ in range(m)]
    for i in range(m - 2):
        for j in range(n - 2):
            if not is_region(image, i, j, threshold):
                continue
            total = sum(image[x][y] for x in range(i, i + 3) for y in range(j, j + 3))
            average = total // 9
            for x in range(i, i + 3):
                for y in range(j, j + 3):
                    sums[x][y] += average
                    counts[x][y] += 1
    result = [row[:] for row in image]
    for i in range(m):
        for j in range(n):
            if counts[i][j] > 0:
                result[i][j] = sums[i][j] // counts[i][j]
    return result


class Solution:
    def resultGrid(self, image: list[list[int]], threshold: int) -> list[list[int]]:
        return solve(image, threshold)
