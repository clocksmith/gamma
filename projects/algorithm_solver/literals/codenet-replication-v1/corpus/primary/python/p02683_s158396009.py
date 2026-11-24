import sys
input = lambda: sys.stdin.readline().rstrip()

N,M,X = map(int, input().split())


text = []
for i in range(N):
    tmp = list(map(int, input().split()))
    text.append(tmp)

ans = float("inf")
for i in range(1 << N):
    tmp = [0] * (M+1)  
    flg = 0
    for j in range(N):
        if (i>>j) & 1:
            for k in range(M+1):
                tmp[k] += text[j][k]
    for l in range(1, M+1):
        if tmp[l] < X:
            flg = 1
            break
    if tmp[0] != 0 and not flg:   
        ans = min(ans, tmp[0])    

print(ans if ans != float("inf") else -1)