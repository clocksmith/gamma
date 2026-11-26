N,K = map(int,input().split())

MOD = 10**9 + 7
A = [0] * (K + 1)

# 最大公約数がdの倍数の個数
for d in range(1, K + 1):
    A[d] = pow(K // d, N, MOD)

# ちょうどdになるためには
for d in range(K, 0, -1):
    # 2d,3d,...を引く
    for i in range(2, K // d + 1):
        A[d] -= A[d * i]

answer = sum(d * x for d, x in enumerate(A))
print(answer % MOD)