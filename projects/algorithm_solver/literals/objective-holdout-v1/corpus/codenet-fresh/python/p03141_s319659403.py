import sys

n=int(sys.stdin.readline())
M = []
for i in range(n):
    a,b = map(int,sys.stdin.readline().split())
    M.append([a,b])

M = sorted(M,key=lambda x:sum(x), reverse=True)
cnt = 0
for i in range(n):
    if i%2==0:
        cnt += M[i][0]
    else:
        cnt -= M[i][1]
print(cnt)
