N, M = map(int, input().split(' '))
X = []
for i in range(M):
    X.append(list(map(int, input().split(' '))))

num_b = [1 for i in range(N+1)]
num_b[0] = 0
psb = [0]*(N+1)
psb[1] = 1
for i in range(M):
    num_b[X[i][0]] -= 1
    num_b[X[i][1]] += 1
    if psb[X[i][0]] == 1:
        psb[X[i][1]] = 1 
    if num_b[X[i][0]] == 0:
        psb[X[i][0]] = 0

print(psb.count(1))