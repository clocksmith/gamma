n = int(input())
P =[]
s = 0
for _ in range(n):P.append([int(i) for i in input().split()])
P.append(P[0])
for j in range(n):s += P[j][1]*P[j+1][0] -  P[j][0] * P[j+1][1]
print(-s*0.5)