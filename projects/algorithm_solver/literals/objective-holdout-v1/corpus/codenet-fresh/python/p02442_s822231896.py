n = int(input())
a = list(map(int,input().split()))
m = int(input())
b = list(map(int,input().split()))
ans = 0
for i in range(min(n,m)):
    if a[i] < b[i]:
        ans = 1
        break
    elif a[i] > b[i]:
        break
else:
    if n < m:
        ans = 1

print(ans)
