#!/usr/bin/env python3
#ABC123 C
import math
L = [int(input()) for _ in range(6)]

N = L[0]
L.remove(L[0])
L.sort()
min = L[0]
print(math.ceil(N/L[0]) + 4)