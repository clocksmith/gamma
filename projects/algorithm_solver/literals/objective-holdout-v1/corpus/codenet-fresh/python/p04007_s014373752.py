import sys
input = sys.stdin.readline
import copy
from collections import deque

H,W=map(int,input().split())
A=[[0]*W for i in range(H)]
for i in range(H):
    S=input()
    for j in range(W):
        A[i][j]=S[j]
C=copy.deepcopy(A)
for h in range(W):
    C[0][h]='#'
for j in range(W):
    if j%2==1:
        for i in range(H-1):
            C[i][j]='#'
D=copy.deepcopy(A)
for h in range(W):
    D[-1][h]='#'
for j in range(W):
    if j%2==0:
        for i in range(1,H):
            D[i][j]='#'
for i in range(H):
    print(''.join(C[i]))
print()
for i in range(H):
    print(''.join(D[i]))