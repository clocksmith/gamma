import sys
input = sys.stdin.readline
import itertools

H, W, K = map(int, input().split())
S = [input() for i in range(H)]
Col = [[] for i in range(W)]
for j in range(W):
    for i in range(H):
        Col[j].append(S[i][j])
Ans = 10**9
for lst in itertools.product([0,1], repeat=H-1):
    ran = []
    ans = sum(lst)
    l = 0
    for i, x in enumerate(lst, 1):
        if x == 1:
            ran.append((l, i))
            l = i
    ran.append((l, H))
    cnt = [0] * len(ran)
    endflg = 0
    for j in range(W):
        flg = 0
        for i, (l, r) in enumerate(ran):
            c = Col[j][l:r].count('1')
            if c > K:
                ans = 10**9
                endflg = 1
                break
            if cnt[i] + c > K:
                flg = 1
                break
        if endflg:
            break
        if flg:
            ans += 1
            for i, (l, r) in enumerate(ran):
                cnt[i] = Col[j][l:r].count('1')
        else:
            for i, (l, r) in enumerate(ran):
                cnt[i] += Col[j][l:r].count('1')
    Ans = min(Ans, ans)
print(Ans)
