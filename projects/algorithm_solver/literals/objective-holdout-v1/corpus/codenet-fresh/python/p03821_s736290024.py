N = int(input())
al = []
bl = []
for i in range(N):
    a, b = map(int, input().split())
    al.append(a)
    bl.append(b)
cnt = 0

for i in range(N - 1, -1, -1):
    tmp = (al[i] + cnt) % bl[i]
    if tmp != 0:
        cnt += bl[i] - tmp

print(cnt)
