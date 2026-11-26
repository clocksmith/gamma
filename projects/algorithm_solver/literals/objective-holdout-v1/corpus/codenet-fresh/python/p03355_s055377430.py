s = input()
k = int(input())
li = []
l = 0
r = min(len(s), 5)

while l != r:
    s1 = s[l:r]
    for i in range(1,len(s1)+1):
        s2 = s1[:i]
        li.append(s2)

    if r < len(s):
        r += 1
    l += 1

li = list(set(li))
li.sort()

print(li[k-1])
