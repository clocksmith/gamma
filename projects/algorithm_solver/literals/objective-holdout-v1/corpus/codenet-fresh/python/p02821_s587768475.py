n, m = map(int, input().split())
a = [int(x) for x in input().split()]

aa = [0]*(10**5+1)
aa_sum = [0]*(10**5+1)

for x in a:
    aa[x] += 1
    aa_sum[x] += x

for i in range(10**5)[::-1]:
    aa[i] = aa[i] + aa[i+1]
    aa_sum[i] = aa_sum[i] + aa_sum[i+1]


def count(x):
    cnt = 0
    sm = 0
    for i in range(n):
        if x-a[i] < 0:
            cnt += n
            sm += aa_sum[0]+n*a[i]
        elif x-a[i] > 10**5:
            continue
        else:
            cnt += aa[x-a[i]]
            sm += aa_sum[x-a[i]]+aa[x-a[i]]*a[i]

    return cnt, sm


bottom = 0
top = 10**6

while top - bottom > 1:
    mid = (top+bottom) // 2
    cnt, sm = count(mid)
    if cnt < m:
        top = mid
    else:
        bottom = mid

cnt, sm = count(bottom)
ans = sm - (cnt-m)*bottom

print(ans)
