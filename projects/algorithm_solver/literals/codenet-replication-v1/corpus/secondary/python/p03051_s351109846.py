from itertools import accumulate
from operator import xor


def solve(acc):
    MOD = 10 ** 9 + 7
    cnt0 = 0
    dp0 = {}
    dp1 = {}
    last_0 = {}
    for a in acc:
        if a == 0:
            cnt0 += 1
        else:
            if a not in dp1:
                dp0[a] = 1
                dp1[a] = 1
                last_0[a] = cnt0
            else:
                bw0 = cnt0 - last_0[a]
                if bw0 > 0:
                    dp0[a] = (dp0[a] + dp1[a] * bw0) % MOD
                    last_0[a] = cnt0
                dp1[a] = (dp1[a] + dp0[a]) % MOD

    if acc[-1] == 0:
        return (pow(2, cnt0 - 1, MOD) + sum(dp1.values())) % MOD
    else:
        return dp0[acc[-1]]


n = int(input())
aaa = list(map(int, input().split()))
acc = list(accumulate(aaa, func=xor))
print(solve(acc))
