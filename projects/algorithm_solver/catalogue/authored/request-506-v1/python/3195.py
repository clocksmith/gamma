# Original candidate. Contract: https://leetcode.com/problems/find-the-minimum-area-to-cover-all-ones-i/
def solve(grid):
    top,left=len(grid),len(grid[0]);bottom=right=-1
    for i,row in enumerate(grid):
        for j,x in enumerate(row):
            if x:top=min(top,i);bottom=max(bottom,i);left=min(left,j);right=max(right,j)
    return (bottom-top+1)*(right-left+1)
