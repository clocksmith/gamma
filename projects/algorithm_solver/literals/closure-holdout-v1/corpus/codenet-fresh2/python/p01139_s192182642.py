import sys
from collections import Counter

sys.setrecursionlimit(2502)


def paint(field, i, j, b, f, moves={(-1, 0), (1, 0), (0, 1), (0, -1)}):
    fij = field[i][j]
    if fij & f:
        return
    if fij & 4 and not fij & b:
        return
    field[i][j] |= b | f
    for di, dj in moves:
        ni = i + di
        nj = j + dj
        if nj < 0 or w <= nj or ni < 0 or h <= ni:
            continue
        paint(field, ni, nj, b, f)


buf = []
chardict = {'.': 0, 'W': 5, 'B': 6}
while True:
    w, h = map(int, input().split())
    if w == 0:
        break
    field = []
    init_w, init_b = 0, 0
    for _ in range(h):
        line = input().strip()
        init_w += line.count('W')
        init_b += line.count('B')
        field.append([chardict[c] for c in line])
    for i in range(h):
        for j in range(w):
            fij = field[i][j]
            if fij & 4 and not fij & 24:
                paint(field, i, j, fij & 3, (fij & 3) << 3)
    result = Counter(b & 3 for row in field for b in row)
    print(result[2] - init_b, result[1] - init_w)