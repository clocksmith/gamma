"""Original candidate for LeetCode 2017. Contract: https://leetcode.com/problems/grid-game/
Development tests only; not admitted or independently qualified.
Positional arguments match the official function; inputs are not mutated.
Complexity: O(n) time, O(1) space"""
def solve(grid):
    top=sum(grid[0]); bottom=0; best=float('inf')
    for a,b in zip(*grid):
        top-=a; best=min(best,max(top,bottom)); bottom+=b
    return best
