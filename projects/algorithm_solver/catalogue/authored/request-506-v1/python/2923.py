# Original candidate. Contract: https://leetcode.com/problems/find-champion-i/
def solve(grid):
    champion=0
    for i in range(1,len(grid)):
        if grid[i][champion]:champion=i
    return champion
