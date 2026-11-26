class SegTree:
    
    def __init__(self, A, intv, initialize = True):
        self.N = len(A)
        self.N0 = 2**(self.N-1).bit_length()
        self.intv = intv
        if initialize:
            self.data = [intv]*(self.N0-1) + A + [intv]*(self.N0 - self.N + 1)
            for i in range(self.N0-2, -1, -1):
                self.data[i] = min(self.data[2*i+1], self.data[2*i+2]) 
        else:
            self.data = [intv]*(2*self.N0)
    
    def segf(self, a, b):
        return min(a, b)
    
    def update(self, k, x):
        k += self.N0-1
        self.data[k] = x
        while k >= 0 :
            k = (k-1)//2
            self.data[k] = min(self.data[2*k+1], self.data[2*k+2])
    
    def query(self, l, r):
        L, R = l+self.N0, r+self.N0
        s = self.intv
        while L < R:
            if R & 1:
                R -= 1
                s = min(s, self.data[R-1])
            if L & 1:
                
                s = min(s, self.data[L-1])
                L += 1
            L >>= 1
            R >>= 1
        return s

import sys
N, Q = map(int, input().split())
T = SegTree([0]*N, 2**31-1, False)
for _ in range(Q):
    qt, x, y = map(int, sys.stdin.readline().split())
    if qt:
        print(T.query(x, y+1))
    else:
        T.update(x, y)
