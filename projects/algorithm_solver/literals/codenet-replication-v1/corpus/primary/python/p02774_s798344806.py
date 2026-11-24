import numpy as np
import sys

input = sys.stdin.readline

n, k = [int(x) for x in input().split()]
A = np.array([int(a) for a in input().split()], dtype="int64")

A = np.sort(A)

A_pos = A[A > 0]
A_neg = A[A < 0]
A_zero = A[A == 0]

# 積がc以下となる組み合わせの数を求める
def n_comb_lt(c):
    n_comb = 0
    # A[i] > 0であるA[i]について
    target = c // A_pos  # target以下の値がA[i]の相方
    n_comb += np.searchsorted(A, target, side="right").sum()

    # A[i] == 0であるA[i]について
    n_comb += n * len(A_zero) if c >= 0 else 0

    # A[i] < 0であるA[i]について
    target = -(-c // A_neg)
    n_comb += (n - np.searchsorted(A, target, side="left")).sum()

    # 組み合わせのうち、A[i]*A[i]となっているものを引いて、2で割る
    n_comb -= A[A * A <= c].size
    n_comb //= 2

    return n_comb

ok = -10 ** 18 - 1
ng = 10 ** 18 + 1

# k番目の積は、積がm未満となる組み合わせがk個未満となる最大のm
# ←→積が(m-1)以下となる組み合わせがk個未満となる最大のm
while ng - ok > 1:
    mid = (ng + ok) // 2
    if n_comb_lt(mid - 1) < k:
        ok = mid
    else:
        ng = mid

print(ok)