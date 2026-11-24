n, k = map(int, input().split())
rules = [map(int, input().split()) for _ in range(k)]

ans = [[0,1,1,1,1,1,1] for _ in range(n+1)]

dic = [0, [0,1,0,0,1,0,0], [0,0,1,0,0,1,0], [0,0,0,1,0,0,1]]
for [d, p] in rules:
    ans[d] = list(dic[p])

ans[1][4] = 0
ans[1][5] = 0
ans[1][6] = 0

for d in range(2, n+1):
    ans[d][1] = ans[d][1] * (ans[d-1][2] + ans[d-1][3] + ans[d-1][5] + ans[d-1][6])
    ans[d][2] = ans[d][2] * (ans[d-1][1] + ans[d-1][3] + ans[d-1][4] + ans[d-1][6])
    ans[d][3] = ans[d][3] * (ans[d-1][1] + ans[d-1][2] + ans[d-1][4] + ans[d-1][5])
    ans[d][4] = ans[d][4] *  ans[d-1][1]
    ans[d][5] = ans[d][5] *  ans[d-1][2]
    ans[d][6] = ans[d][6] *  ans[d-1][3]

print(sum(ans[n]) % 10000)

