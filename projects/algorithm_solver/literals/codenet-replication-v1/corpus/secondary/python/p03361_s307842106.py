H, W = map(int,input().split())
s = [[i for i in list(input())] for j in range(H)]
dx = [0,0,-1,1]
dy = [-1,1,0,0]
 
for i in range(H):
    for j in range(W):
        if s[i][j] == ".": continue
 
        # 上下左右の4方向
        for k in range(4):
            ni = i + dy[k]
            nj = j + dx[k]
 
            if ni < 0 or ni >= H: continue
            if nj < 0 or nj >= W: continue
 
            if s[ni][nj] == "#": break
            if k == 3:
                print("No")
                exit()
 
print("Yes")