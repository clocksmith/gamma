from itertools import product
N = int(input())
S = input()
S = [int(s) for s in S]
ans = 0
for q in product(range(10),repeat=3):
    qi = q[0] # PyPyならこんなことしなくてもOK
    i = 0
    for s in S:
        if s==qi:
            if i==2:
                ans += 1
                break
            else:
                i+=1
                qi = q[i] # PyPyならこんなことしなくてもOK
print (ans)