while True:
    a, b = map(int, input().split())
    if a == 0:
        break
    N = int(input())
    memo = [[0 for i in range(a+1)] for j in range(b+1)]
    flag = [[False for i in range(a+1)] for j in range(b+1)]
    memo[1][1] = 1
    flag[1][1] = True
    x = [0] * N
    y = [0] * N
    for i in range(N):
        x[i], y[i] = map(int, input().split())
        flag[y[i]][x[i]] = True

    for i in range(1, b+1):
        for j in range(1, a+1):
            if not flag[i][j]:
                flag[i][j] = True
                memo[i][j] = memo[i-1][j] + memo[i][j-1]

    print(memo[b][a])

