N,M=map(int,input().split())
if min(M,N)<=1:
  K=max(M,N)
  print(int(K*(K-1)/2))
else:
  print(int(M*(M-1)/2+N*(N-1)/2))