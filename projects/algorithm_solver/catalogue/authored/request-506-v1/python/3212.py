# Original implementation. Contract: https://leetcode.com/problems/count-submatrices-with-equal-frequency-of-x-and-y/
def solve(grid):
    n=len(grid[0]);balance=[0]*n;xs=[0]*n;answer=0
    for row in grid:
        b=x=0
        for j,c in enumerate(row):
            b+=(c=='X')-(c=='Y');x+=c=='X';balance[j]+=b;xs[j]+=x
            answer+=balance[j]==0 and xs[j]>0
    return answer
