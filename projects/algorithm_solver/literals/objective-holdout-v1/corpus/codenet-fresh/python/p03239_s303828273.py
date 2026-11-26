n,T = map(int,input().split())
ans = 10000
count = 0
for i in range(n):
    c,t = map(int,input().split())
    if t <= T and ans > c:
        ans = c
        count += 1
if count == 0:
    print("TLE")
else:
    print(ans)