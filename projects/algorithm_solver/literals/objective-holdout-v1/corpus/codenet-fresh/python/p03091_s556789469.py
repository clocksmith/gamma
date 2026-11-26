import sys
input = sys.stdin.readline

N,M=map(int,input().split())
EDGE=[tuple(map(int,input().split())) for i in range(M)]

E=[[] for i in range(N+1)]
J=[0]*(N+1)

for x,y in EDGE:
    J[x]+=1
    J[y]+=1

    E[x].append(y)
    E[y].append(x)

from collections import deque
Q=deque()
Q.append(1)

USE=[0]*(N+1)

while Q:
    x=Q.pop()

    for to in E[x]:
        if USE[to]==0:
            Q.append(to)
            USE[to]=1

if min(USE[1:])==0:
    print("No")
    sys.exit()

for i in range(N+1):
    if J[i]%2==1:
        print("No")
        sys.exit()

if max(J)>=6:
    print("Yes")
    sys.exit()

if sum(J)<=2*N+2:
    print("No")
    sys.exit()

if sum(J)>=2*N+6:
    print("Yes")
    sys.exit()

FOUR=[]
for i in range(N+1):
    if J[i]==4:
        FOUR.append(i)

Q=deque()
Q.append(FOUR[0])
USE=[0]*(N+1)

count=0

while Q:
    x=Q.pop()

    for to in E[x]:
        if to==FOUR[1]:
            count+=1
            continue
            
        if USE[to]==0:
            Q.append(to)
            USE[to]=1

if count==2:
    print("Yes")
else:
    print("No")