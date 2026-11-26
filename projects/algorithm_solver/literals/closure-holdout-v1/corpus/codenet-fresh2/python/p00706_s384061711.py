while True:
    N = int(input())
    if N == 0: break
    W,H = map(int,input().split())
    fld = [[0 for w in range(W)] for h in range(H)]
    for i in range(N):
        x,y = map(lambda s:int(s)-1,input().split())
        fld[y][x] = 1
    cums = [[0 for w in range(W+1)] for h in range(H+1)]
    for y in range(H):
        for x in range(W):
            cums[y+1][x+1] = fld[y][x] + cums[y][x+1] + cums[y+1][x] - cums[y][x]
    S,T = map(int,input().split())
    ans = 0
    for y in range(H-T+1):
        for x in range(W-S+1):
            ans = max(ans, cums[y+T][x+S] - cums[y+T][x] - cums[y][x+S] + cums[y][x])
    print(ans)