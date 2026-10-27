"""Original candidate for LeetCode 3148. Contract: https://leetcode.com/problems/maximum-difference-score-in-a-grid/
Development tests only; not admitted or independently qualified.
Positional arguments match the official function; inputs are not mutated.
Complexity: O(mn) time, O(n) space; at least one move required"""
def solve(grid):
    mins=[float('inf')]*len(grid[0]);ans=-float('inf')
    for row in grid:
        left=float('inf')
        for j,x in enumerate(row):
            before=min(left,mins[j]);ans=max(ans,x-before)
            mins[j]=left=min(before,x)
    return ans
