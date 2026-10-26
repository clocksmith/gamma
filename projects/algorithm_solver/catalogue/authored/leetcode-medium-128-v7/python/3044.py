"""3044. Most Frequent Prime: count straight-line decimal numbers and test each distinct candidate for primality once."""
from collections import Counter


def solve(mat: list[list[int]]) -> int:
    """O(r * c * L + u * sqrt(M)) time and O(u) auxiliary space, where L is the maximum ray length; inputs are read-only."""
    rows, columns = len(mat), len(mat[0])
    counts = Counter()
    directions = [(dr, dc) for dr in (-1, 0, 1) for dc in (-1, 0, 1) if dr or dc]
    for row in range(rows):
        for column in range(columns):
            for dr, dc in directions:
                nr, nc = row, column
                value = 0
                while 0 <= nr < rows and 0 <= nc < columns:
                    value = 10 * value + mat[nr][nc]
                    if value > 10:
                        counts[value] += 1
                    nr += dr
                    nc += dc
    best = -1
    frequency = 0
    for value, count in counts.items():
        if count < frequency or (count == frequency and value <= best):
            continue
        if value % 2 == 0:
            continue
        factor = 3
        while factor * factor <= value and value % factor != 0:
            factor += 2
        if factor * factor > value:
            best = value
            frequency = count
    return best


class Solution:
    def mostFrequentPrime(self, mat: list[list[int]]) -> int:
        return solve(mat)
