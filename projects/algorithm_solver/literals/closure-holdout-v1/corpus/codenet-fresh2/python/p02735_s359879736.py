import queue

H, W = map(int, input().split())

s = [list(input()) for _ in range(H)]

ini = 0
if s[0][0] == '#':
    ini = 1

dist = [[ini for _ in range(W)] for _ in range(H)]
start = (0,0)

qq = queue.Queue()

for i in range(H):
    for j in range(W):
        tgt = []
        if j == 0:
            pass
        else:
            if s[i][j-1] == '.' and s[i][j] == '#':
                tgt.append(dist[i][j-1] + 1)

            else:
                tgt.append(dist[i][j-1])

        if i == 0:
            pass
        else:
            if s[i-1][j] == '.' and s[i][j] == "#":
                tgt.append(dist[i-1][j] + 1)
            else:
                tgt.append(dist[i-1][j])
        if i + j == 0:
            continue
        dist[i][j] = min(tgt)

print(dist[H-1][W-1])

