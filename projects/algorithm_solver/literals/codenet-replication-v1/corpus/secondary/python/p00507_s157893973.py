n = int(input())
a = [int(input()) for i in range(n)]
a.sort()
s = a[0:4]
p = []
for i in range(len(s)):
    for j in range(len(s)):
        if i != j:
            p.append(int(str(s[i]) + str(s[j])))
p.sort()
print(p[2])

