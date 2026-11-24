N = int(input())
S = input()

l = list(S)
MOD = 10**9 + 7

ans = 1
for c in range(ord('a'), ord('z') + 1):
    c = chr(c)
    ans *= (l.count(c) + 1)
    ans %= MOD
ans = (ans + MOD - 1) % MOD
print(ans)
