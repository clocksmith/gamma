w = input()
s = set(w)

r = True
for si in s:
    c = w.count(si)
    # print(si, c)
    if c % 2 == 1:
        r = False

if r:
    print('Yes')
else:
    print('No')
