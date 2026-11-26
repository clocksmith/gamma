n = int(input())
a = [int(input()) for _ in range(n)]
ans = 0
for i in range(n - 1):
    m = a[i] // 2
    ans += m
    if a[i] % 2 == 1:
        if a[i + 1] > 0:
            ans += 1
            a[i + 1] -= 1
ans += a[n - 1] // 2
print(ans)