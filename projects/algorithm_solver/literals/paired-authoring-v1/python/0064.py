class Solution:
    def minPathSum(self, grid: list[list[int]]) -> int:
        rows = len(grid)
        columns = len(grid[0])
        path_costs = [0] * columns
        path_costs[0] = grid[0][0]
        for column in range(1, columns):
            path_costs[column] = path_costs[column - 1] + grid[0][column]
        for row in range(1, rows):
            path_costs[0] += grid[row][0]
            for column in range(1, columns):
                # Read the previous row above and the updated current row left.
                path_costs[column] = min(
                    path_costs[column], path_costs[column - 1]
                ) + grid[row][column]
        return path_costs[-1]
