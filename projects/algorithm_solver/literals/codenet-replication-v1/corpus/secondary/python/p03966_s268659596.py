N=int(input())
T,A=map(int,input().split())

def bisect(x,X):
  l=0
  r=10**18
  while r>l+1:
    n=(r+l)//2
    if n*x>=X:
      r=n
    else:
      l=n
  return r    

for _ in range(N-1):
  t,a=map(int,input().split())
  n=max(bisect(t,T),bisect(a,A))  
  T=n*t
  A=n*a
    
print(T+A)