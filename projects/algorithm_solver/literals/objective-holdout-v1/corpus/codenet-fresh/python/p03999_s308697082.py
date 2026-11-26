S=input()
L=len(S)

from itertools import product

P=product(range(2),repeat=L-1)

ans=0
for p in P:
    s=0
    temp=S[0]
    for i in range(L-1):
        if p[i]==1:
            s+=int(temp)
            temp=S[i+1]
        else:
            temp+=S[i+1]
    s+=int(temp)
    ans+=s
print(ans)