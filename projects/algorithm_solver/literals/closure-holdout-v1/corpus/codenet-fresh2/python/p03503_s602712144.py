N = int(input())

f_vals = []
for i in range(N):
    f_vals.append([int(_) for _ in input().split()])
p_vals = []
for i in range(N):
    p_vals.append([int(_) for _ in input().split()])


def solve():
    ans = -1e12
    for i in range(1, 2 ** 10):
        sumv = 0
        for l in range(N):
            fcnt = 0
            for j in range(10):
                fcnt += ((i >> j) & 1) and f_vals[l][j]
            sumv += p_vals[l][fcnt]

        ans = max(ans, sumv)
    print(ans)


solve()