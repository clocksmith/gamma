# coding: utf-8
# Your code here!
import sys
read = sys.stdin.read
readline = sys.stdin.readline

#a,b,c,d = map(int,readline().split())
s,k = readline().split()


a = [len(i) for i in s.split("0")]
while a and a[-1] == 0: a.pop()

if not a:
    print(1)
    exit()

MOD = 998244353

M = sum(a)+1
k = min(int(k),M)


dp = [[0]*M for _ in range(k+1)] # j 使って（上限 k）、l 余ってる
dp[0][0] = 1

#print(a)
for ai in a[::-1]:
    ndp = [[0]*M for _ in range(k+1)] # j 使って（上限 k）、l 余ってる
    for j in range(k+1):
        for l in range(M):
            if dp[j][l]:
                for ll in range(l):
                    ndp[j][ll] += dp[j][l]
                    ndp[j][ll] %= MOD

                V = min(M-l,k-j+1,ai+1)
                for i in range(V):
                    #if j+i > k: break
                    ndp[j+i][l+i] += dp[j][l]
                    ndp[j+i][l+i] %= MOD
    
    dp = ndp
    #print(dp)

ans = 0
for jj in range(k+1):
    ans += dp[jj][0]

print(ans%MOD)





