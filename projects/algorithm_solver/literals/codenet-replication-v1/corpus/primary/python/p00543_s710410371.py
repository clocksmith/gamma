N, M = map(int, input().split())
bibs = [int(input()) for _ in range(N)]
btns = [k+1 for k in range(M)]
for k in btns:
    for i in range(N-1):
        if bibs[i]%k > bibs[i+1]%k:
            bibs[i], bibs[i+1] = bibs[i+1], bibs[i]
print(*bibs, sep='\n')