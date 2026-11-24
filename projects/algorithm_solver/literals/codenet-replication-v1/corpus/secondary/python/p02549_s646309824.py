n,k= map(int, input().split())
a= [list(map(int, input().split())) for i in range(k)]
s=[]


mod=998244353
# dp[i]:i番目のマスへの行き方
dp=[0]*(n+6)

for j in range(k):
    l = a[j][0]
    r = a[j][1]
    dp[l+1] += 1
    dp[r+2] -= 1


for i in range(1,n+1):
    dp[i+1]+=dp[i]
    dp[i+1]%=mod
    x=dp[i+1]
    for j in range(k):
        l=a[j][0]
        r=a[j][1]
        if l+i<=n:
            dp[i + l + 1] += x
        if r+i<=n:
            dp[i + 2 + r] -= x



print(dp[n]%mod)