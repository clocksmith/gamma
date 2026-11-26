#"""
import sys
input = sys.stdin.readline
#"""

N,M = map(int,input().split())
ST = [list(map(int,input().split())) for _ in [0]*M]

Ef = [[] for _ in [0]*N]
Eb = [[] for _ in [0]*N]

for s,t in ST:
    s -= 1
    t -= 1
    Ef[s].append(t)
    Eb[t].append(s)

V = [0]*N
for i in range(N-2,-1,-1):
    tmp_sum = 0
    tmp_num = 0
    for j in Ef[i]:
        tmp_num += 1
        tmp_sum += V[j]
    V[i] = tmp_sum/tmp_num + 1.0

bq = []
for bi in range(i,N-1):
    if len(Ef[bi]) <= 1:
        continue
    bj = 0
    tmp = 0
    for j in Ef[bi]:
        if tmp<V[j]:
            tmp = V[j]
            bj = j
    bq.append((bi,bj))

ans = V[0]
for bi,bj in bq:
    V2 = [0]*N
    for i in range(N-2,-1,-1):
        tmp_sum = 0
        tmp_num = 0
        for j in Ef[i]:
            if i==bi and j==bj : continue
            tmp_num += 1
            tmp_sum += V2[j]
        V2[i] = tmp_sum/tmp_num + 1.0
    ans = min(ans,V2[0])
print(ans)