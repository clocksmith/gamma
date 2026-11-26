from collections import deque

H, W = map(int, input().split())
A = [input() for _ in range(H)]

D = [[0] * W for _ in range(H)]

Q = deque()
Q1 = deque()
for i in range(H):
    for j in range(W):
        if A[i][j] == '#':
            D[i][j] = 1
            Q.append([i, j])

yudlr = [1, -1, 0, 0]
xudlr = [0, 0, -1, 1]

C = 0
while len(Q) > 0:
    C += 1
    while len(Q) > 0:
        Q1.append(Q.pop())
    while len(Q1) > 0:
        q = Q1.popleft()
        y = q[0]
        x = q[1]
        for i in range(4):
            y1 = y + yudlr[i]
            x1 = x + xudlr[i]
            if y1 < 0 or y1 >= H or x1 < 0 or x1 >= W:
                continue
            if D[y1][x1] == 1:
                continue
            D[y1][x1] = 1
            Q.append([y1, x1])

print(C - 1)