S = input()
T = input()
# S = 'acac'
# T = 'acm'
# DP[i][j]=Sのi文字とTのj文字の編集距離
DP = [[0 for j in range(len(T)+1)] for i in range(len(S)+1)]
for i in range(len(S)+1):
    DP[i][0] = i
for j in range(len(T)+1):
    DP[0][j] = j
for i in range(1, len(S)+1):
    for j in range(1, len(T)+1):
        if S[i-1] == T[j-1]:
            c = 0
        else:
            c = 1
        DP[i][j] = min(DP[i-1][j]+1, DP[i][j-1]+1, DP[i-1][j-1]+c)
print(DP[len(S)][len(T)])

