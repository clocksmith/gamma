from sys import stdin
import numpy as np
N,M,Q = [int(x) for x in stdin.readline().rstrip().split()]

cumsum_2d = np.zeros([N+1,N+1]) 
for i in range(M):
    L,R = [int(x) for x in stdin.readline().rstrip().split()]
    cumsum_2d[L,R] += 1
    
np.cumsum(cumsum_2d,axis=0,out=cumsum_2d)
np.cumsum(cumsum_2d,axis=1,out=cumsum_2d)
    
for i in range(Q):
    p,q = [int(x) for x in stdin.readline().rstrip().split()]
    ans = cumsum_2d[q,q] - cumsum_2d[q,p-1] - cumsum_2d[p-1,q] + cumsum_2d[p-1,p-1]
    print(int(ans))