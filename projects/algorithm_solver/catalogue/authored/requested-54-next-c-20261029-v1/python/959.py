def solve(grid):
    n = len(grid)
    parent = list(range(4*n*n))
    rank = [0]*(4*n*n)
    count = len(parent)
    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x
    def union(a,b):
        nonlocal count
        a,b = find(a),find(b)
        if a == b:
            return
        if rank[a] < rank[b]:
            a,b = b,a
        parent[b] = a
        if rank[a] == rank[b]:
            rank[a] += 1
        count -= 1
    for r in range(n):
        for c in range(n):
            base = 4*(r*n+c)
            if grid[r][c] != '/':
                union(base,base+1)
                union(base+2,base+3)
            if ord(grid[r][c]) != 92:
                union(base,base+3)
                union(base+1,base+2)
            if r+1 < n:
                union(base+2,base+4*n)
            if c+1 < n:
                union(base+1,base+7)
    return count

class Solution:
    def regionsBySlashes(self, grid):
        return solve(grid)
