"""Original candidate for LeetCode 2428. Contract: https://leetcode.com/problems/maximum-sum-of-an-hourglass/
Development tests only; not admitted or independently qualified.
Positional arguments match the official function; inputs are not mutated.
Complexity: O(mn) time, O(1) extra space"""
def solve(grid):
    return max(sum(grid[i][j:j+3])+grid[i+1][j+1]+sum(grid[i+2][j:j+3]) for i in range(len(grid)-2) for j in range(len(grid[0])-2))
