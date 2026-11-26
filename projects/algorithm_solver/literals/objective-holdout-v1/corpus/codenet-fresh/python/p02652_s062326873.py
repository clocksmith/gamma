S = input()

c = 0
cum = [c]
for s in S:
    if s == "1":
        c += 1
    else:
        c -= 1
    cum.append(c)
max_cum = [None] * (len(S) + 1)
max_cum[-1] = cum[-1]
for i in reversed(range(len(S))):
    max_cum[i] = max(cum[i], max_cum[i + 1])
z = max_cum[0]


def f(m):
    c = 0
    fz = c
    add = 0
    for i, s in enumerate(S):
        if s == "1":
            c += 1
        elif s == "0":
            c -= 1
            fz = min(fz, c)
        elif add + max_cum[i + 1] + 2 <= m:
            c += 1
            add += 2
        else:
            c -= 1
            fz = min(fz, c)
    return fz


fz = f(z)
fz1 = f(z + 1)

ans = min(z - fz, z + 1 - fz1)
print(ans)