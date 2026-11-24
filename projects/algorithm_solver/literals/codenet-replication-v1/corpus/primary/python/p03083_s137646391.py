def prepare(n, MOD):
    f = 1
    factorials = [1]
    for m in range(1, n + 1):
        f *= m
        f %= MOD
        factorials.append(f)
    inv = pow(f, MOD - 2, MOD)
    invs = [1] * (n + 1)
    invs[n] = inv
    for m in range(n, 1, -1):
        inv *= m
        inv %= MOD
        invs[m - 1] = inv
    return factorials, invs


b, w = map(int, input().split())
MOD = 10 ** 9 + 7
I2 = 500000004  # 2^(-1) mod MOD
factorials, inverses = prepare(b + w, MOD)
buf = []
denom = I2
pi, qi = 0, 0
for i in range(b + w):
    if i >= b:
        pi *= 2
        pi += factorials[i - 1] * inverses[i - b] * inverses[b - 1]
        pi %= MOD
    if i >= w:
        qi *= 2
        qi += factorials[i - 1] * inverses[i - w] * inverses[w - 1]
        qi %= MOD
    buf.append((I2 - (pi - qi) * denom) % MOD)
    denom = denom * I2 % MOD
print('\n'.join(map(str, buf)))
