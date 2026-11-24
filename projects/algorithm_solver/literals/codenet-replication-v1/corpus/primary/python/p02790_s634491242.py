a, b = map(int, input().split())

s1 = str(a) * b
s2 = str(b) * a
if s1 < s2:
    print(s1)
else:
    print(s2)