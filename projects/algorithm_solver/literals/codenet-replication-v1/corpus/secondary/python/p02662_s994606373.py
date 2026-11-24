n, s = map(int, input().split())
a = list(map(int, input().split()))
mod = 998244353

lst = [0 for i in range(s+1)]
lst[0] = 1
dp = [lst]
for i in range(n):
    lst = [0 for i in range(s+1)]
    ai = a[i]
    for j in range(s+1):
        if j-ai >= 0:
            lst[j] = (2*dp[-1][j] + dp[-1][j-ai]) % mod
        else:
            lst[j] = (2*dp[-1][j]) % mod
    dp.append(lst)

print(dp[-1][-1])