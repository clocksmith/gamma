"""3225. Maximum Score From Grid Operations.

Track adjacent black-prefix heights and optimize the earlier height with prefix/suffix maxima; O(n^3) time and O(n^2) space. Inputs are preserved.
"""

def solve(grid: list[list[int]]) -> int:
    n = len(grid)
    best = [[float('-inf')] * (n + 1) for _ in range(n + 1)]
    best[0] = [0] * (n + 1)
    for column in range(1, n):
        prefix = [0]
        for row in range(n):
            prefix.append(prefix[-1] + grid[row][column - 1])
        following = [[float('-inf')] * (n + 1) for _ in range(n + 1)]
        for middle in range(n + 1):
            left_maximum = [float('-inf')] * (n + 1)
            right_maximum = [float('-inf')] * (n + 2)
            for earlier in range(n + 1):
                left_maximum[earlier] = max(left_maximum[earlier - 1] if earlier else float('-inf'), best[earlier][middle])
            for earlier in range(n, -1, -1):
                right_maximum[earlier] = max(right_maximum[earlier + 1], best[earlier][middle] + max(0, prefix[earlier] - prefix[middle]))
            for later in range(n + 1):
                following[middle][later] = max(left_maximum[later] + max(0, prefix[later] - prefix[middle]), right_maximum[later + 1])
        best = following
    prefix = [0]
    for row in range(n):
        prefix.append(prefix[-1] + grid[row][n - 1])
    return max(best[earlier][last] + max(0, prefix[earlier] - prefix[last])
               for earlier in range(n + 1) for last in range(n + 1))


class Solution:
    def maximumScore(self, grid: list[list[int]]) -> int:
        return solve(grid)
