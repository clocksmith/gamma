class NeighborSum:
    def __init__(self, grid):
        self.grid = [row[:] for row in grid]
        self.position = {v: (r, c) for r, row in enumerate(grid) for c, v in enumerate(row)}

    def _sum(self, value, offsets):
        r, c = self.position[value]
        n = len(self.grid)
        return sum(self.grid[r + dr][c + dc] for dr, dc in offsets
                   if 0 <= r + dr < n and 0 <= c + dc < n)

    def adjacentSum(self, value):
        return self._sum(value, ((-1, 0), (1, 0), (0, -1), (0, 1)))

    def diagonalSum(self, value):
        return self._sum(value, ((-1, -1), (-1, 1), (1, -1), (1, 1)))


def solve(operations, arguments):
    service = None
    results = []
    for operation, args in zip(operations, arguments):
        if operation == 'NeighborSum':
            service = NeighborSum(*args)
            results.append(None)
        elif operation == 'adjacentSum':
            results.append(service.adjacentSum(*args))
        elif operation == 'diagonalSum':
            results.append(service.diagonalSum(*args))
        else:
            raise ValueError('Unsupported NeighborSum operation')
    return results
