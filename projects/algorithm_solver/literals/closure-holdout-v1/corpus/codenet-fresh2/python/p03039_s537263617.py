n, m, k = map(int, input().split())

MOD = 1000000007
def pow_mod(x, y):
    if y == 0: return 1
    ans = 1
    while y > 1:
        if y % 2 != 0: 
            ans *= x
            ans %= MOD
        x *= x
        x %= MOD
        y //= 2
    return ans * x % MOD
mod_inv = lambda x: pow_mod(x, MOD - 2)

a = 0
for i in range(1, n):
  a += (i * (n - i)) % MOD 
  a %= MOD
a *= (m * m) % MOD
a %= MOD

b = 0
for i in range(1, m):
  b += (i * (m - i)) % MOD 
  b %= MOD
b *= (n * n) % MOD
b %= MOD

w = (m * n - 2) % MOD
u = 1
v = 1
for i in range(1, k-1):
  u *= (w - i + 1)
  u %= MOD
  v *= i
  v %= MOD

ans = ((a + b) % MOD) 
ans *= u
ans %= MOD
ans *= mod_inv(v)
ans %= MOD


print(ans)