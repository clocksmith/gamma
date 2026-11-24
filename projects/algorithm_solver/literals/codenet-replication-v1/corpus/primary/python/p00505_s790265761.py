import sys

a = []
for line in sys.stdin:
    a.append(list(map(int,line.split())))
t = [0 for i in range(3)]
for i in range(len(a)):
    a[i].sort()
    if a[i][2] >= a[i][0] + a[i][1]:
        break
    b = a[i][2] ** 2
    c = a[i][0] ** 2 + a[i][1] ** 2
    if b > c:
        t[2] += 1
    elif b < c:
        t[1] += 1
    else:
        t[0] += 1
print("{0} {1} {2} {3}".format(sum(t), t[0], t[1], t[2]))

