"""Original hack2hire:689bf3a41126a03aace65e63; inferred public-preview contract; qualification unknown."""
def countFullyCoveredClusters(availability, users):
    if not users:
        return 0
    rows, cols = len(users), len(users[0])
    visited = set()
    result = 0
    for r in range(rows):
        for c in range(cols):
            if not users[r][c] or (r, c) in visited:
                continue
            queue = [(r, c)]
            visited.add((r, c))
            covered = True
            head = 0
            while head < len(queue):
                x, y = queue[head]
                head += 1
                covered = covered and bool(availability[x][y])
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    a, b = x + dx, y + dy
                    if 0 <= a < rows and 0 <= b < cols and users[a][b] and (a, b) not in visited:
                        visited.add((a, b))
                        queue.append((a, b))
            result += covered
    return result

solve = countFullyCoveredClusters

class Solution:
    countFullyCoveredClusters = staticmethod(countFullyCoveredClusters)
