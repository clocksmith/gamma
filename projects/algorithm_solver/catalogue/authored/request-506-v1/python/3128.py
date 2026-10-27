"""Original candidate for LeetCode 3128. Contract: https://leetcode.com/problems/right-triangles/
Development tests only; not admitted or independently qualified.
Positional arguments match the official function; inputs are not mutated.
Complexity: O(mn) time, O(m+n) space; answer < 10^12"""
def solve(grid):
    rows=list(map(sum,grid));cols=list(map(sum,zip(*grid)))
    return sum((rows[i]-1)*(cols[j]-1) for i,row in enumerate(grid) for j,x in enumerate(row) if x)
