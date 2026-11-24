N = int(input())
S = input()

mod = 10**9 + 7
M=len(S)

DP = [[0]*(N+1) for i in range(N+1)]

DP[0][0] = 1

for i in range(1,N+1):
    for j in range(N+1):
        if j>0 and j<N:
            DP[i][j] = DP[i-1][j-1] + 2*DP[i-1][j+1]
        elif j==0:
            DP[i][j] = DP[i-1][j] + 2*DP[i-1][j+1]
        else:
            DP[i][j] = DP[i-1][j-1]
        DP[i][j] %= mod

print(DP[N][M])