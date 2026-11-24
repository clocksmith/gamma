def solve(X, Y, Z, V, E, A):
    dp = [[0.0] * 6001 for _ in range(Y + 11)]
    dp[0][0] = 1.0
    for i in range(Y):
        for j in range(5001):
            if dp[i][j] <= 0.0:
                continue
            for k in V:
                t = i + k
                if t > Y:
                    dp[Y][j] += dp[i][j]/X
                elif E[t] == 1:
                    dp[min(Y, t+A[t])][j] += dp[i][j]/X
                else:
                    dp[t][max(0, j+A[t])] += dp[i][j]/X

    s = 0
    for i in range(5001):
        s += i * dp[Y][i]
    print(int(s))

if __name__ == "__main__":
    import sys

    while True:
        X, Y, Z = map(int, input().split())
        if X | Y | Z == 0:
            sys.exit()
        V = list(map(int, input().split()))
        E = [0] * 100
        A = [0] * 100
        for _ in range(Z):
            n, e, a = map(int, input().split())
            E[n] = e
            if e == 3:
                A[n] = -a
            else:
                A[n] = a
        solve(X, Y, Z, V, E, A)