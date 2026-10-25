class Solution:
    def uniquePaths(self, m: int, n: int) -> int:
        path_counts = [1] * n
        for row in range(1, m):
            for column in range(1, n):
                # Read the previous row above and the updated current row left.
                path_counts[column] += path_counts[column - 1]
        return path_counts[-1]
