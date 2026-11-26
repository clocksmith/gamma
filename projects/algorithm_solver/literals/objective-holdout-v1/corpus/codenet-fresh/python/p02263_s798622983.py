a = input().split()
b = []
for i in a:
    if i.isdigit():
        b.append(int(i))
    else:
        if i == '+':
            s1 = b.pop()
            s2 = b.pop()
            b.append(s1+s2)
        elif i == '-':
            s1 = b.pop()
            s2 = b.pop()
            b.append(s2-s1)
        elif i == '*':
            s1 = b.pop()
            s2 = b.pop()
            b.append(s1*s2)
print(b[0])