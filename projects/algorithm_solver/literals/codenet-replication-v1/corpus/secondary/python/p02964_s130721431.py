import sys
input = sys.stdin.readline

N,K = map(int,input().split())
A = list(map(int,input().split()))

X = A * 2

Nextcount = [-1] * (2 * (10**5+1))
Nextind = [-1]*N

for i,x in enumerate(X):
    if 0 <= Nextcount[x] < N:
        Nextind[Nextcount[x]] = i

    Nextcount[x] = i

Repeatcount=0
NOW = 0

Repeatcount+=Nextind[NOW]-NOW+1
NOW=(Nextind[NOW]+1)%N

while NOW!=0:
    Repeatcount+=Nextind[NOW]-NOW+1
    NOW=(Nextind[NOW]+1)%N
    

Rep=(N*K)%Repeatcount
NOW=0

while True:
    if Nextind[NOW]-NOW+1<Rep:
        Rep-=Nextind[NOW]-NOW+1
        NOW=(Nextind[NOW]+1)%N

    else:
        break
    
#print(Rep,NOW)

from collections import Counter
C=Counter()
s=[]
for i in range(Rep):
    if X[(NOW+i)%N] in C:
        while X[(NOW+i)%N] in C:
            po=s.pop()
            C[po]-=1
            if C[po]==0:
                del C[po]

    else:
        s.append(X[(NOW+i)%N])
        C[X[(NOW+i)%N]]+=1

    #print(s,C)

print(*s)
        
            

