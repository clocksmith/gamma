import itertools
n,x,m=map(int,input().split())
t=[list(map(int,input().split()))for _ in [0]*m]
a=[-1]
for b in itertools.product(range(x+1),repeat=n):
    for l,r,s in t:
        if s!=sum(b[l-1:r]):break
    else:
        if sum(a)<sum(b):a=b
print(*a)