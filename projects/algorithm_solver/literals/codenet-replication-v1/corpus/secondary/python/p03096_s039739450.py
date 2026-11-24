n = int(input())
oth = [int(input()) for _ in range(n)]
mod = 10**9 + 7
l = list()
for x in oth:
    if l and l[-1] == x:
        continue
    l.append(x)
lenl = len(l)
last = [-1] * 200001
l2 = [-1] * 200001
for i, a in enumerate(l):
    l2[i] = last[a]
    last[a] = i

dp = [0] * lenl
dp[0] = 1
for i in range(1, lenl):
    prev = 0 if l2[i] < 0 else dp[l2[i]]
    dp[i] = (dp[i - 1] + prev) % mod
print(dp[-1])
