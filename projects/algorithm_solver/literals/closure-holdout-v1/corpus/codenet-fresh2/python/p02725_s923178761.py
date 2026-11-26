k, n = map(int, input().split())
l = list(map(int, input().split()))
d = [0] * n
for i in range(n):
    if i == n - 1:
        d[i] = k - l[-1] + l[0]
    else:
        d[i] = l[i + 1] - l[i]
print(k - max(d))