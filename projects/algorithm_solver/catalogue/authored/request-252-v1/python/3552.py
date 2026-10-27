from collections import deque


def solve(matrix):
    rows, cols = len(matrix), len(matrix[0])
    size = rows * cols
    portals = {}
    for r, row in enumerate(matrix):
        for c, char in enumerate(row):
            if 'A' <= char <= 'Z':
                portals.setdefault(char, []).append(r * cols + c)
    distance = [size + 1] * size
    distance[0] = 0
    settled = bytearray(size)
    queue = deque([0])
    while queue:
        cell = queue.popleft()
        if settled[cell]:
            continue
        settled[cell] = 1
        if cell == size - 1:
            return distance[cell]
        r, c = divmod(cell, cols)
        char = matrix[r][c]
        for other in portals.pop(char, []):
            if distance[other] > distance[cell]:
                distance[other] = distance[cell]
                queue.appendleft(other)
        for nr, nc in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
            if 0 <= nr < rows and 0 <= nc < cols and matrix[nr][nc] != '#':
                other = nr * cols + nc
                if distance[other] > distance[cell] + 1:
                    distance[other] = distance[cell] + 1
                    queue.append(other)
    return -1
