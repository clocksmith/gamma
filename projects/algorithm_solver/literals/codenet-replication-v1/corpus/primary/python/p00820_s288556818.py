MAXN = 2**15
MAXRT = int(MAXN**0.5)
MAXTERM = 4

dp = [[0 for n in range(MAXN+1)] for t in range(MAXTERM+1)]
dp[0][0] = 1
for r in range(MAXRT,0,-1):
    for t in range(MAXTERM):
        for n in range(MAXN+1 - r*r):
            if dp[t][n] == 0: continue
            dp[t+1][n + r*r] += dp[t][n]

while True:
    N = int(input())
    if N == 0: break
    print(sum(map(lambda x:x[N],dp)))