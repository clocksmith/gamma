N, K, Q = [int(x) for x in input().split()]
A = [int(input()) for _ in range(Q)]
Point = [Q for _ in range(N)]
for i in range(Q):
  Point[A[i]-1] -= 1
for i in range(N):
  if(K-Point[i])>0:
    print('Yes')
  else:
    print('No')