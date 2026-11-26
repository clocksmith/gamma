b = [[1,2,3,4],[2,-1,4,-3],[3,-4,-1,2],[4,3,-2,-1]]
while 1:
    n = int(input())
    if n == 0:break
    for _ in range(n):
        x = tuple(map(int, input().split()))
        x1, x2 = x[:4], x[4:]
        a = [0,0,0,0]
        for i in range(4):
            for j in range(4):
                if b[i][j] > 0:a[b[i][j] - 1] += x1[i] * x2[j]
                else:a[-b[i][j] - 1] -= x1[i] * x2[j]
        print(*a)
