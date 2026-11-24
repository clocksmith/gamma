N = int(input())
A = list(map(int,input().split()))

res = 0
old_h = 0
for i, h in enumerate(A):
    if (diff:=h-old_h) < 0: 
        res -= diff
    else:
        old_h = h

print(res)