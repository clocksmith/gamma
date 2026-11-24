N = int(input())
A = [int(a) for a in input().split()] + [0] * 2
X = [[-10**10] * (N+1) for _ in range(N+1)]
X[A[0]][A[1]] = 0
ans = 0
ma = 0
MA = [-10**10] * (N+1)
MA[A[0]] = MA[A[1]] = 0
for i in range(N):
    B = A[i*3+2:i*3+5]
    cnt = len(set(B))
    if cnt == 1:
        ans += 1
    elif cnt == 2:
        a1 = B[0]^B[1]^B[2]
        a2 = (sum(B) - a1) // 2
        X[a1], X[a1][a2], X[a2][a2] = [max(X[a2][j] + 1, X[j][a2] + 1, MA[j]) for j in range(N+1)], max(X[a1][a2], X[a2][a2] + 1, ma), max(ma, X[a2][a2], X[a1][a1] + 1)
        X[a2] = [max(X[a2][j], MA[j]) for j in range(N+1)]
        MA = [max(m, x1, x2) for m, x1, x2 in zip(MA, X[a1], X[a2])]
        MA[a1] = max(MA[a1], max(X[a1]), X[a2][a1])
        MA[a2] = max(MA[a2], X[a1][a2], X[a2][a2])
        ma = max(ma, MA[a1], MA[a2])
    else:
        a, b, c = B
        # X[a][b], X[a][c], X[b][c] = max(X[a][b], ma, X[c][c] + 1), max(X[a][c], ma, X[b][b] + 1), max(X[b][c], ma, X[a][a] + 1)
        X[a][b], X[a][c], X[b][c] = max(ma, X[c][c] + 1), max(ma, X[b][b] + 1), max(ma, X[a][a] + 1)
        X[a] = [max(x, m) for x, m in zip(X[a], MA)]
        X[b] = [max(x, m) for x, m in zip(X[b], MA)]
        X[c] = [max(x, m) for x, m in zip(X[c], MA)]
        MA[a] = max(MA[a], max(X[a]))
        MA[b] = max(MA[b], X[a][b], max(X[b]))
        MA[c] = max(MA[c], X[a][c], X[b][c], max(X[c]))
        MA = [max(m, xa, xb, xc) for m, xa, xb, xc in zip(MA, X[a], X[b], X[c])]
        ma = max(ma, MA[a], MA[b], MA[c])

print(ans + max(ma, max(max(x) for x in X)))