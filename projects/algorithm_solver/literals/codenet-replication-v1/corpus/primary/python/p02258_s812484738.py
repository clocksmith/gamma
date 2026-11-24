n = int(input())
R = [int(input()) for i in range(n)]
maxv = R[1] - R[0]
minv = R[0]

for j in range(1, n):
    maxv = R[j] - minv if R[j] - minv > maxv else maxv
    minv = R[j] if R[j] < minv else minv

print(maxv)