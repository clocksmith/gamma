n = int(input())
m = int(input())
a = []
for i in range(n*2):
    a.append(i+1)
for i in range(m):
    k = int(input())
    if k == 0:
        b = []
        for j in range(n):
            b.append(a[j])
            b.append(a[j+n])
        a = b.copy()
    else:
        a = (a[k:] + a[:k]).copy()
for i in range(n*2):
    print(a[i])

