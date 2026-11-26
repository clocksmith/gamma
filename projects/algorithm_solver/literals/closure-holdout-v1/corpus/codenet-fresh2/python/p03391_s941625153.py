q = int(input())
a = []
b = []
smb = []

for i in range(q):
    t1, t2 = map(int,input().split(' '))
    a.append(t1)
    b.append(t2)
    if t1 > t2:
        smb.append(t2)

smb.sort()

if a == b:
    print(0)
else:
    b.sort()
    print(sum(b)-smb[0])
