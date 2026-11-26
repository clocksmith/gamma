import itertools

while True:
    N, K, S = map(int, input().split())
    if N == K == S == 0:
        break
    ans = 0
    for l in itertools.combinations(range(1, N+1), K):
        if sum(l) == S:
            ans += 1
    print(ans)