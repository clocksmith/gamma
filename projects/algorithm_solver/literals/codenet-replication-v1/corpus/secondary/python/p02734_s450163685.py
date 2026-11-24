N,S=map(int,input().split())
A=list(map(int,input().split()))
mod=998244353

dp=[[0 for i in range(0,S+1)] for j in range(0,N)]
for i in range(0,S+1):
    if i==A[0]:
        dp[0][i]=1

for i in range(1,N):
    for j in range(0,S+1):
        if j>A[i]:
            dp[i][j]=(dp[i-1][j]+dp[i-1][j-A[i]])%mod
        elif j==A[i]:
            dp[i][j]=(dp[i-1][j]+(i+1))%mod
        else:
            dp[i][j]=dp[i-1][j]

ans=0
for i in range(0,N):
    ans=(ans+dp[i][S])%mod

print(ans)