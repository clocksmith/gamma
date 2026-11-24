import math
n = int(input())
m = int(input())
A = list(map(int,input().split()))
B = [list(map(int,input().split())) for i in range(m)]
p = [0 for i in range(n+1)]

for i in range(m):
    for j in range(n):
        if B[i][j] == A[i]:
            p[j+1] += 1
        else:
            p[A[i]] += 1
for i in range(1,n+1):
    print(p[i])

