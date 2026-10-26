"""1905. Count Sub Islands: visit every second-grid island completely while checking first-grid coverage."""


def solve(grid1: list[list[int]], grid2: list[list[int]]) -> int:
    """O(rows * columns) time and O(rows * columns) auxiliary space; inputs are read-only."""
    rows, columns = len(grid2), len(grid2[0])
    seen = [bytearray(columns) for _ in range(rows)]
    directions = ((1, 0), (-1, 0), (0, 1), (0, -1))
    answer = 0
    for row in range(rows):
        for column in range(columns):
            if not grid2[row][column] or seen[row][column]:
                continue
            stack = [(row, column)]
            seen[row][column] = 1
            covered = True
            while stack:
                current_row, current_column = stack.pop()
                if not grid1[current_row][current_column]:
                    covered = False
                for dr, dc in directions:
                    nr, nc = current_row + dr, current_column + dc
                    if 0 <= nr < rows and 0 <= nc < columns and grid2[nr][nc] and not seen[nr][nc]:
                        seen[nr][nc] = 1
                        stack.append((nr, nc))
            if covered:
                answer += 1
    return answer


class Solution:
    def countSubIslands(self, grid1: list[list[int]], grid2: list[list[int]]) -> int:
        return solve(grid1, grid2)
