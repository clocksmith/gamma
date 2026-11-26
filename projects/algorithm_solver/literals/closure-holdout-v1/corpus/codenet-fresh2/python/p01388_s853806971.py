a = str(input())
f = []
c = ['K','U','P','C']
for i in range(0,4):
    b = a.count(c[i])
    f.append(b)
f.sort()
print(f[0])
