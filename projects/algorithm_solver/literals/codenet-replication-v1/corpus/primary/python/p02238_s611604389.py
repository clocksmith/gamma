def dfs(u):
    global dfs_color, d, f, t
    color[u] = GRAY
    d[u] += t
    t += 1
    for v in range(n):
        if (M[u][v] == 0):
            continue
        else:
            if (color[v] == WHITE):
               dfs(v)
    color[u] = BLACK
    f[u] = t
    t += 1

n = int(input())
M = [[False for i in range(n)] for j in range(n)]
for i in range(n):
    tmp = list(map(int, input().split()))
    for j in range(tmp[1]):
        M[tmp[0]-1][tmp[j+2]-1] = True

WHITE = 0
GRAY = 1
BLACK = 2
color = [WHITE for i in range(n)]
d = [0 for i in range(n)]
f = [0 for i in range(n)]
t = 1

for u in range(n):
    if (color[u] == WHITE):
        dfs(u)
for u in range(n):
    print(str(u+1), str(d[u]), str(f[u]), sep = " ")