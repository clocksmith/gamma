x, y, z = map(int, input().split())
A = [list(map(int, input().split())) for _ in range(x)]
B = [list(map(int, input().split())) for _ in range(y)]
ans_s = []
ans = []

for i in range(x):
    ans_s = []
    for j in range(z):
        p = 0
        for k in range(y):
            p += A[i][k] * B[k][j]
        ans_s.append(p)
    ans.append((ans_s))

for i in ans:
    print(' '.join([str(v) for v in i]))
