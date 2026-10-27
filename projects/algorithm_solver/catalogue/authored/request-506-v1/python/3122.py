# Original candidate implementation. Contract: https://leetcode.com/problems/minimum-number-of-operations-to-satisfy-conditions/
def solve(grid):
    rows=len(grid);dp=[0]*10
    for col in range(len(grid[0])):
        frequency=[0]*10
        for row in grid:frequency[row[col]]+=1
        dp=[rows-frequency[d]+min(dp[p] for p in range(10) if p!=d) for d in range(10)]
    return min(dp)
