def lcs(x, y):
    a = len(x)
    b = len(y)
    c1 = [0] * (b + 1)
    for i in range(a):
        e1 = x[i]
        c2 = c1[:]
        for j in range(b):
            if e1 == y[j]:
                c1[j + 1] = c2[j] + 1
            elif c1[j + 1] < c1[j]:
                c1[j + 1] = c1[j]
    return c1[-1]


n = int(input().rstrip())
ret = []
for i in range(n):
    s1 = input().rstrip()
    s2 = input().rstrip()
    ret.append(lcs(s1, s2))
print(*ret, sep="\n")
