r, c = map(int, input().split())
A = [[0 for i in range(c + 1)] for j in range(r + 1)]

for i in range(r):
    l = list(map(int, input().split()))
    for j in range(c):
        A[i][j] = l[j]
        A[r][j] += l[j]
    A[i][c] = sum(l)
    A[r][c] += sum(l)

for i in range(r + 1):
    for j in range(c):
        print(A[i][j], "", end = "")
    print(A[i][c])

