N = int(input())
D = list(map(int, input().split()))

N = len(D)
r = 0
for i in range(N):
    for j in range(i + 1, N):
        r += D[i] * D[j]

print(r)
