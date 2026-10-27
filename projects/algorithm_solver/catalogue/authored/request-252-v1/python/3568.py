from collections import deque


def solve(classroom, energy):
    """Level BFS with energy dominance at each (cell, collected-mask)."""
    rows, cols = len(classroom), len(classroom[0])
    size = rows * cols
    cells = ''.join(classroom)
    litter = {}
    for cell, char in enumerate(cells):
        if char == 'S':
            start = cell
        elif char == 'L':
            litter[cell] = 1 << len(litter)
    target = (1 << len(litter)) - 1
    if not target:
        return 0
    neighbors = [[] for _ in range(size)]
    for cell in range(size):
        r, c = divmod(cell, cols)
        for nr, nc in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
            if 0 <= nr < rows and 0 <= nc < cols and cells[nr * cols + nc] != 'X':
                neighbors[cell].append(nr * cols + nc)
    stride = energy + 1
    best = bytearray(size * (target + 1))
    best[start] = energy + 1
    queue = deque([start * stride + energy])
    moves = 0
    while queue:
        for _ in range(len(queue)):
            state = queue.popleft()
            position_mask, remaining = divmod(state, stride)
            mask, cell = divmod(position_mask, size)
            if mask == target:
                return moves
            if remaining == 0:
                continue
            for other in neighbors[cell]:
                new_mask = mask | litter.get(other, 0)
                new_energy = energy if cells[other] == 'R' else remaining - 1
                key = new_mask * size + other
                if best[key] < new_energy + 1:
                    best[key] = new_energy + 1
                    queue.append(key * stride + new_energy)
        moves += 1
    return -1
