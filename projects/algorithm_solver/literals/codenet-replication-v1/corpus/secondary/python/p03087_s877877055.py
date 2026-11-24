# coding: utf-8

N, Q = map(int, input().split())
S = input()
l_r = [tuple(map(int, input().split())) for _ in range(Q)]

isAC = [0] * N
cnt = 0
for i in range(len(S) - 1):
    if S[i] == "A" and S[i + 1] == "C":
        cnt += 1
    isAC[i + 1] = cnt

for l, r in l_r:
    print(isAC[r - 1] - isAC[l - 1])
