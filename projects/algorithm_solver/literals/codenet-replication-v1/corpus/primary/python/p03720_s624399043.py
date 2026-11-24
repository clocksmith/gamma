N, M = list(map(int, input().split()))
re = [0 for i in range(N+1)]
for i in range(M):
    a, b=  list(map(int,input().split()))
    re[a] += 1
    re[b] += 1

for i in range(N):
    print(re[i+1])