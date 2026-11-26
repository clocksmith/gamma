a, b = map(int,input().split())
ans = 0
for i in range(a,b+1):
    val = str(i)
    if val[0] == val[4] and val[1] == val[3]:
        ans += 1
print(ans)