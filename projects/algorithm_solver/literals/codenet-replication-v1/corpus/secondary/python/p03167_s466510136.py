H,W=map(int,input().split())
a=[]
mod=10**9+7

for i in range(H):
    temp=list(map(str,input()))
    a.append(temp)

dp=[[0]*(W) for _ in range(H)]
dp[0][0]=1

for h in range(H):
    for w in range(W):
        if h==w==0:continue
        if a[h][w]=="#":continue
        if h-1<0:
            dp[h][w]=dp[h][w-1]%mod
        elif w-1<0:
            dp[h][w] = dp[h-1][w]%mod
        else:
            dp[h][w] = (dp[h][w -1] + dp[h -1][w])%mod

ans=dp[H-1][W-1]%mod
print(ans)