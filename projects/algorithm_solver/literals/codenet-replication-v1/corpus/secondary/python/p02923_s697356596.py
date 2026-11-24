N = int(input())
H = list(map(int,input().split()))
J = [0 for k in range(N+1)]

for k in range(1,N):
    if H[k-1] >= H[k] and J[k-1] > 0:
        J[k] = J[k-1]+1
    elif H[k-1] >= H[k] and J[k-1] == 0:
        J[k] = 1

print(max(J))
