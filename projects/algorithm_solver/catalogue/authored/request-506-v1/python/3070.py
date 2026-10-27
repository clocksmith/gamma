"""Original candidate for LeetCode 3070. Contract: https://leetcode.com/problems/count-submatrices-with-top-left-element-and-sum-less-than-k/
Development tests only; not admitted or independently qualified.
Positional arguments match the official function; inputs are not mutated.
Complexity: O(mn) time, O(n) space; inclusive <= k despite title"""
def solve(grid,k):
    sums=[0]*len(grid[0]);ans=0
    for row in grid:
        prefix=0
        for j,x in enumerate(row):
            prefix+=x;sums[j]+=prefix;ans+=sums[j]<=k
    return ans
