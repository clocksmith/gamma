N=int(input())
A=list(map(int,input().split()))
B=list(map(int,input().split()))
AS=[A[0]]
for i in range(1,N):
    AS.append(AS[i-1]+A[i])
dp=[0 for i in range(N)]

dp[0]=A[0]+B[0]

for i in range(1,N):
    dp[i]=max(AS[i]+B[i],dp[i-1]+B[i])
print(dp[N-1])