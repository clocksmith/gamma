from collections import Counter
a = int(input())
l = list(map(int, input().split()))
#i = 1

c=Counter(l)
d = dict(c)
kv = []
for k,v in d.items():
    if k>v:
        kv.append(v)
    elif k<v:
        t = v-k
        kv.append(t)
s = sum(kv)
print(s)
