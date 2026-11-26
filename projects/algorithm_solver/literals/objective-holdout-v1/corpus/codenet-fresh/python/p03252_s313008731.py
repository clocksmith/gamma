import sys

s = input().strip()
t = input().strip()

d = dict()
for i, sc in enumerate(s):
    tc = t[i]

    if sc in d:
        if d[sc] == tc:
            continue
        else:
            print('No')
            sys.exit(0)

    d[sc] = tc

vs = list(d.values())
for v in vs:
    if vs.count(v) > 1:
        print('No')
        sys.exit(0)

print('Yes')
