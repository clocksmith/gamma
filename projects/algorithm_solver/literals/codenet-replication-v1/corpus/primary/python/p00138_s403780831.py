# -*- coding: utf-8 -*-

import sys
import os
import math

N = 24
A = []
for i in range(N):
    id, t = map(float, input().split())
    id = int(id)
    A.append((t, id))

B = A[:8]
C = A[8:16]
D = A[16:]

B.sort()
C.sort()
D.sort()

def print_data(A, index):
    data = A[index]
    t = data[0]
    id = data[1]
    print(id, t)

print_data(B, 0)
print_data(B, 1)
print_data(C, 0)
print_data(C, 1)
print_data(D, 0)
print_data(D, 1)

B = B[2:]
C = C[2:]
D = D[2:]

E = B + C + D
E.sort()
print_data(E, 0)
print_data(E, 1)