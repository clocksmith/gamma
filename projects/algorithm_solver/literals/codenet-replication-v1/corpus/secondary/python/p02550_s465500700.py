inpl = lambda: list(map(int,input().split()))
N, X, M = inpl()
hisS = [0] * M
pos = [-1] * M
c = S = hisS[0] = X
pos[X] = 0
for i in range(1, min(M+1,N)):
    c = c * c % M
    S += c
    if pos[c] >= 0:
        prev = pos[c]
        period = i - prev
        q = (N - prev) // period
        r = (N - prev) % period
        if prev == 0 and r == 0:
           ans = (S - hisS[prev]) * q
        else:
            ans = (S - hisS[prev]) * q + hisS[prev+r-1]
        print(ans)
        break
    else:
        hisS[i] = S
        pos[c] = i
else:
    print(S)
    exit()
