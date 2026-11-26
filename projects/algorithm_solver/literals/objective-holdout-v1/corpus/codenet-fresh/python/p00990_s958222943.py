n = int(input())
ID = input()[::-1]
m = int(input())
a_lst = list(map(int, input().split()))
dp = [[0] * 10 for _ in range(n + 1)]
dp[0][0] = 1


def fix(a):
    if a < 10:return a
    return a % 10 + a // 10


for i in range(n):
    c = ID[i]
    mag = 1 if i % 2 == 0 else 2
    for j in range(10):
        if c == "*":
            for a in a_lst:
                a = fix(a * mag)
                dp[i + 1][(j + a) % 10] += dp[i][j]
        else:
            a = fix(int(c) * mag)
            dp[i + 1][(j + a) % 10] += dp[i][j]
print(dp[n][0])


