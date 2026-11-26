

a,b,c,d,e,f = map(int, input().split())

waters = []
for i in range(f // (100 * a) + 1):
    for j in range(f // (100 * b) + 1):
        amount = 100 * (i * a + j * b)
        if amount <= f:
            waters.append(amount)

sugers = []
for i in range(f // c + 1):
    for j in range(f // d + 1):
        amount = i * c + j * d
        if amount <= f:
            sugers.append(amount)

maxp = -1.0
res_w = 0
res_s = 0

for w in waters:
    for s in sugers:
        if w + s > f or w + s == 0:
            continue
        capa = w // 100 * e
        if s > capa:
            continue
        p = 100 * s / (w + s)
        if maxp < p:
            maxp, res_w, res_s = p, w + s, s

print("%d %d" % (res_w, res_s))