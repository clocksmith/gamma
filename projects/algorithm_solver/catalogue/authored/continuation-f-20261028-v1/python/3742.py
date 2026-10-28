"""Original frontend 3742 development candidate; qualification unknown."""

def solve(grid, k):
    width = len(grid[0])
    budget = min(k, len(grid) + width - 2)
    previous = [[-1] * (budget + 1) for _ in range(width)]
    for i, row in enumerate(grid):
        current = [[-1] * (budget + 1) for _ in range(width)]
        for j, value in enumerate(row):
            cost = int(value != 0)
            if i == 0 and j == 0:
                current[j][0] = 0
                continue
            for spent in range(cost, budget + 1):
                best = max(previous[j][spent - cost] if i else -1,
                           current[j - 1][spent - cost] if j else -1)
                if best >= 0:
                    current[j][spent] = best + value
        previous = current
    return max(previous[-1])


class Solution:
    def maxPathScore(self, grid, k):
        return solve(grid, k)
