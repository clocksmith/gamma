N,x = map(int,(input().split()))
a = list(map(int,(input().split())))

ans = 0
for i in range(N-1):
    s = a[i] + a[i+1]
    if s > x:
        if a[i+1] < s-x:
            a[i+1] = 0
            a[i] -= s-x-a[i+1]
        else:
            a[i+1] -= s-x
        ans += s-x

print(ans)