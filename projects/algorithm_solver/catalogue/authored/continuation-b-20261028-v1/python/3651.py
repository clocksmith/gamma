def solve(grid, k):
    m, n = len(grid), len(grid[0])
    cells = sorted(range(m*n), key=lambda i: grid[i//n][i%n], reverse=True)
    dist = [float('inf')]*(m*n)
    dist[0] = 0
    for used in range(k+1):
        if used:
            previous = dist
            dist = previous[:]
            best = float('inf')
            start = 0
            while start < len(cells):
                end = start
                value = grid[cells[start]//n][cells[start]%n]
                while end < len(cells) and grid[cells[end]//n][cells[end]%n] == value:
                    best = min(best, previous[cells[end]])
                    end += 1
                for position in range(start, end): dist[cells[position]] = min(dist[cells[position]], best)
                start = end
        for i in range(m):
            for j in range(n):
                p = i*n+j
                if i: dist[p] = min(dist[p], dist[p-n]+grid[i][j])
                if j: dist[p] = min(dist[p], dist[p-1]+grid[i][j])
    return dist[-1]

class Solution:
    def minCost(self, grid, k):
        return solve(grid, k)
