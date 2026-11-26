n = int(input())
a =  list(map(int, input().split()))
b =  list(map(int, input().split()))
cnt = 0
for i in range(n):
    if a[i] <= b[i]:
        cnt+= a[i]
        b[i] -= a[i]
        if a[i+1] <= b[i]:
            cnt += a[i+1]
            a[i+1] = 0
        else:
            cnt += b[i]
            a[i+1] -= b[i]
    else:
        cnt += b[i]

print(cnt)