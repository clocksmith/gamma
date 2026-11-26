n = int(input())
p = list(map(int, input().split()))

ans = 0
for i in range(1,n+1):
    if i<=len(list(filter(lambda x: x>=i, p))):
        ans = i

print(ans)
