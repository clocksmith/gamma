# Original implementation. Contract: https://leetcode.com/problems/find-all-possible-stable-binary-arrays-i/
def solve(zero,one,limit):
    mod=1000000007;d0=[[0]*(one+1) for _ in range(zero+1)];d1=[[0]*(one+1) for _ in range(zero+1)]
    for i in range(1,min(zero,limit)+1):d0[i][0]=1
    for j in range(1,min(one,limit)+1):d1[0][j]=1
    for i in range(1,zero+1):
        for j in range(1,one+1):
            d0[i][j]=(d0[i-1][j]+d1[i-1][j]-(d1[i-limit-1][j] if i>limit else 0))%mod
            d1[i][j]=(d0[i][j-1]+d1[i][j-1]-(d0[i][j-limit-1] if j>limit else 0))%mod
    return (d0[zero][one]+d1[zero][one])%mod
