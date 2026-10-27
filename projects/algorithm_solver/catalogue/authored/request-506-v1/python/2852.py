# Original implementation. Contract: https://leetcode.com/problems/sum-of-remoteness-of-all-cells/
def solve(grid):
    n=len(grid);total=sum(x for row in grid for x in row if x!=-1);seen=set();answer=0
    for r in range(n):
        for c in range(n):
            if grid[r][c]==-1 or (r,c) in seen:continue
            q=[(r,c)];seen.add((r,c));amount=0
            for x,y in q:
                amount+=grid[x][y]
                for a,b in ((x-1,y),(x+1,y),(x,y-1),(x,y+1)):
                    if 0<=a<n and 0<=b<n and grid[a][b]!=-1 and (a,b) not in seen:seen.add((a,b));q.append((a,b))
            answer+=len(q)*(total-amount)
    return answer
