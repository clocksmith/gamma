def solve(N, X, D):
    if D == 0:
        if X == 0:
            return 1
        return N+1
    L = {0: [(0, 1), (1, -1)]}
    coef_l = 0
    coef_r = 1
    for coef_x in range(1, N+1):
        m = X * coef_x % D
        l = X * coef_x // D + coef_l
        r = X * coef_x // D + coef_x * N - coef_r
        coef_l = coef_r
        coef_r += coef_x + 1
        if m not in L:
            L[m] = []
        L[m].append((l, 1))
        L[m].append((r+1, -1))
    ans = 0
    #print(L)
    for Q in L.values():
        Q.sort()
        cnt = 0
        last = None
        for val, sign in Q:
            if cnt > 0:
                ans += val - last
            cnt += sign
            last = val
    return ans

N, X, D = map(int, input().split())
print(solve(N, X, D))
