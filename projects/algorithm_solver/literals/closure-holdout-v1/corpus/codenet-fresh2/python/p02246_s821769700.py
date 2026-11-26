distance = (
    (),
    (0, 1, 2, 3, 1, 2, 3, 4, 2, 3, 4, 5, 3, 4, 5, 6),
    (1, 0, 1, 2, 2, 1, 2, 3, 3, 2, 3, 4, 4, 3, 4, 5),
    (2, 1, 0, 1, 3, 2, 1, 2, 4, 3, 2, 3, 5, 4, 3, 4),
    (3, 2, 1, 0, 4, 3, 2, 1, 5, 4, 3, 2, 6, 5, 4, 3),
    (1, 2, 3, 4, 0, 1, 2, 3, 1, 2, 3, 4, 2, 3, 4, 5),
    (2, 1, 2, 3, 1, 0, 1, 2, 2, 1, 2, 3, 3, 2, 3, 4),
    (3, 2, 1, 2, 2, 1, 0, 1, 3, 2, 1, 2, 4, 3, 2, 3),
    (4, 3, 2, 1, 3, 2, 1, 0, 4, 3, 2, 1, 5, 4, 3, 2),
    (2, 3, 4, 5, 1, 2, 3, 4, 0, 1, 2, 3, 1, 2, 3, 4),
    (3, 2, 3, 4, 2, 1, 2, 3, 1, 0, 1, 2, 2, 1, 2, 3),
    (4, 3, 2, 3, 3, 2, 1, 2, 2, 1, 0, 1, 3, 2, 1, 2),
    (5, 4, 3, 2, 4, 3, 2, 1, 3, 2, 1, 0, 4, 3, 2, 1),
    (3, 4, 5, 6, 2, 3, 4, 5, 1, 2, 3, 4, 0, 1, 2, 3),
    (4, 3, 4, 5, 3, 2, 3, 4, 2, 1, 2, 3, 1, 0, 1, 2),
    (5, 4, 3, 4, 4, 3, 2, 3, 3, 2, 1, 2, 2, 1, 0, 1)
)

def get_distance(board):
    sd = 0
    for i in range(16):
        p = board[i]
        if p == 0:
            continue
        sd += distance[p][i]
    return sd

adjacent = (
    (1, 4),         # 0
    (0, 2, 5),      # 1
    (1, 3, 6),      # 2
    (2, 7),         # 3
    (0, 5, 8),      # 4
    (1, 4, 6, 9),   # 5
    (2, 5, 7, 10),  # 6
    (3, 6, 11),     # 7
    (4, 9, 12),     # 8
    (5, 8, 10, 13), # 9
    (6, 9, 11, 14), # 10
    (7, 10, 15),    # 11
    (8, 13),        # 12
    (9, 12, 14),    # 13
    (10, 13, 15),   # 14
    (11, 14)        # 15
)

GOAL = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 0]

def df_lower_search(limit, move, space, lower, pre_p):
    if move == limit:
        if board == GOAL:
            return True
    else:
        for i in adjacent[space]:
            p = board[i]
            if p == pre_p:
                continue
            board[space] = p
            board[i] = 0
            new_lower = lower - distance[p][i] + distance[p][space]
            if new_lower + move <= limit:
                if df_lower_search(limit, move + 1, i, new_lower, p):
                    return True
            board[space] = 0
            board[i] = p

import sys

board = list(map(int, sys.stdin.read().split()))

s = board.index(0)
e_o = (0, 1, 0, 1, 1, 0, 1, 0, 0, 1, 0, 1, 1, 0, 1, 0)

n = get_distance(board)

if e_o[s] != n % 2:
    n += 1

for l in range(n, 46, 2):
    if df_lower_search(l, 0, s, n, None):
        print(l)
        break