s=input()
p=input()
s += s
a = s.count(p)

if a == 0:
    print('No')
else:
    print('Yes')
